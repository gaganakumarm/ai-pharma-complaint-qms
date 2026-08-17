# ruff: noqa: E501
from copy import deepcopy
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.correction_graph import build_correction_graph
from app.core.exceptions import ProviderTimeoutError
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.correction import (
    ComplaintCorrectionPatch,
    CorrectableComplaint,
    CorrectionField,
)
from app.services.corrections import merge_correction


def draft(**changes: Any) -> CorrectableComplaint:
    values = dict.fromkeys(CorrectableComplaint.model_fields)
    values.update(product_type="FDF", batch_lot_number="AMX240602")
    values.update(changes)
    return CorrectableComplaint.model_validate(values)


def assessment() -> ComplaintQualityAssessment:
    return ComplaintQualityAssessment(
        complaint_category="Packaging",
        structured_complaint_description="Carton issue.",
        suggested_severity="MINOR",
        severity_rationale="Cosmetic report.",
        initial_risk_assessment="Potential quality impact requires review.",
        suggested_next_action="QA should review the complaint.",
        assessment_status="COMPLETE",
        information_gaps=[],
        human_review_required=True,
    )


class FakeProvider:
    model = "fake-model"

    def __init__(self, patch: dict[str, Any]) -> None:
        self.patch = patch
        self.assessments = 0

    async def extract_correction(
        self, current: CorrectableComplaint, instruction: str
    ) -> dict[str, Any]:
        return self.patch

    async def assess_complaint(self, complaint: CorrectableComplaint) -> dict[str, Any]:
        self.assessments += 1
        return assessment().model_dump()


@pytest.mark.parametrize(
    ("field", "old", "new"),
    [
        ("product_strength_grade", "USP", "EP"),
        ("manufacturing_date", "January 2026", "February 2026"),
        ("expiry_retest_date", "January 2028", None),
        ("product_type", "FDF", "API"),
    ],
)
def test_single_field_grade_date_clear_and_product_type(
    field: str, old: str, new: str | None
) -> None:
    current = draft(**{field: old})
    patch = ComplaintCorrectionPatch.model_validate(
        {
            "updates": [{"field": field, "value": new}],
            "clarification_required": False,
            "clarification_question": None,
        }
    )
    result = merge_correction(current, patch)
    assert getattr(result.complaint, field) == new
    assert result.changed_fields == [field]


def test_patch_rejects_duplicate_unknown_blank_and_invalid_product_type() -> None:
    with pytest.raises(ValidationError):
        ComplaintCorrectionPatch.model_validate(
            {
                "updates": [
                    {"field": "batch_lot_number", "value": "A"},
                    {"field": "batch_lot_number", "value": "B"},
                ],
                "clarification_required": False,
                "clarification_question": None,
            }
        )
    for field, value in (("status", "COMMITTED"), ("product_name", "")):
        with pytest.raises(ValidationError):
            ComplaintCorrectionPatch.model_validate(
                {
                    "updates": [{"field": field, "value": value}],
                    "clarification_required": False,
                    "clarification_question": None,
                }
            )
    patch = ComplaintCorrectionPatch.model_validate(
        {
            "updates": [{"field": "product_type", "value": "tablet"}],
            "clarification_required": False,
            "clarification_question": None,
        }
    )
    with pytest.raises(ValidationError):
        merge_correction(draft(), patch)


def test_merge_changes_only_listed_fields_and_does_not_mutate_original() -> None:
    current = draft(customer_name="Apollo", affected_quantity=None)
    snapshot = deepcopy(current)
    patch = ComplaintCorrectionPatch.model_validate(
        {
            "updates": [
                {"field": "batch_lot_number", "value": "BMX240602"},
                {"field": "affected_quantity", "value": "48 capsules"},
            ],
            "clarification_required": False,
            "clarification_question": None,
        }
    )
    result = merge_correction(current, patch)
    assert current == snapshot
    assert result.complaint.customer_name == "Apollo"
    assert result.complaint.batch_lot_number == "BMX240602"
    assert result.complaint.affected_quantity == "48 capsules"


@pytest.mark.asyncio
async def test_graph_runs_nodes_and_reassesses_quality_change() -> None:
    provider = FakeProvider(
        {
            "updates": [{"field": "affected_quantity", "value": "48 capsules"}],
            "clarification_required": False,
            "clarification_question": None,
        }
    )
    result = await build_correction_graph(provider, 2000).ainvoke(
        {
            "current_complaint": draft(),
            "instruction": "Quantity is 48 capsules",
            "current_quality_assessment": assessment(),
            "execution_trace": [],
        }
    )
    assert result["changed_fields"] == ["affected_quantity"]
    assert provider.assessments == 1
    assert result["execution_trace"] == [
        "normalize_instruction",
        "extract_correction",
        "validate_patch",
        "merge_patch",
        "recalculate_warnings",
        "reassess_complaint",
        "validate_assessment",
        "prepare_response",
    ]


@pytest.mark.asyncio
async def test_clarification_and_noop_do_not_change_or_reassess() -> None:
    for patch, expected in (
        (
            {
                "updates": [],
                "clarification_required": True,
                "clarification_question": "Which number should change?",
            },
            "CLARIFICATION_REQUIRED",
        ),
        (
            {
                "updates": [{"field": "batch_lot_number", "value": "AMX240602"}],
                "clarification_required": False,
                "clarification_question": None,
            },
            "NO_CHANGES",
        ),
    ):
        provider = FakeProvider(patch)
        current = draft()
        result = await build_correction_graph(provider, 2000).ainvoke(
            {
                "current_complaint": current,
                "instruction": "The number is wrong",
                "current_quality_assessment": assessment(),
                "execution_trace": [],
            }
        )
        assert result["status"] == expected
        assert result["updated_complaint"] == current
        assert provider.assessments == 0


@pytest.mark.asyncio
async def test_non_risk_change_skips_reassessment() -> None:
    provider = FakeProvider(
        {
            "updates": [{"field": "customer_name", "value": "New Customer"}],
            "clarification_required": False,
            "clarification_question": None,
        }
    )
    result = await build_correction_graph(provider, 2000).ainvoke(
        {
            "current_complaint": draft(customer_name="Old Customer"),
            "instruction": "Correct customer",
            "current_quality_assessment": assessment(),
            "execution_trace": [],
        }
    )
    assert result["reassessment_required"] is False
    assert provider.assessments == 0


@pytest.mark.asyncio
async def test_reassessment_failure_returns_no_partial_result() -> None:
    provider = FakeProvider(
        {
            "updates": [
                {
                    "field": "complaint_description",
                    "value": "Visible foreign particles.",
                }
            ],
            "clarification_required": False,
            "clarification_question": None,
        }
    )

    async def fail(_complaint: CorrectableComplaint) -> dict[str, Any]:
        raise ProviderTimeoutError

    provider.assess_complaint = fail  # type: ignore[method-assign]
    with pytest.raises(ProviderTimeoutError):
        await build_correction_graph(provider, 2000).ainvoke(
            {
                "current_complaint": draft(complaint_description="Dented carton."),
                "instruction": "Particles are visible",
                "current_quality_assessment": assessment(),
                "execution_trace": [],
            }
        )


def test_too_many_updates_are_rejected() -> None:
    updates = [{"field": field.value, "value": "x"} for field in list(CorrectionField)]
    updates.append({"field": "customer_name", "value": "y"})
    with pytest.raises(ValidationError):
        ComplaintCorrectionPatch.model_validate(
            {
                "updates": updates,
                "clarification_required": False,
                "clarification_question": None,
            }
        )
