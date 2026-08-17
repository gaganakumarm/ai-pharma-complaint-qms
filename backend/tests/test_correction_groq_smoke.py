# ruff: noqa: E501
import os
from copy import deepcopy
from typing import Any

import pytest

from app.ai.correction_graph import build_correction_graph
from app.ai.providers import GroqComplaintExtractionProvider
from app.core.config import Settings
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.correction import CorrectableComplaint, CorrectionStatus

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_REAL_GROQ") != "1", reason="RUN_REAL_GROQ is not enabled"
)

ASSESSMENT = ComplaintQualityAssessment.model_validate(
    {
        "complaint_category": "Packaging",
        "structured_complaint_description": "A dented carton was reported.",
        "suggested_severity": "MINOR",
        "severity_rationale": "The fictional report describes cosmetic damage.",
        "initial_risk_assessment": "QA review is required to confirm product impact.",
        "suggested_next_action": "QA should inspect the fictional complaint sample.",
        "assessment_status": "COMPLETE",
        "information_gaps": [],
        "human_review_required": True,
    }
)


def fictional_draft(**changes: Any) -> CorrectableComplaint:
    values = dict.fromkeys(CorrectableComplaint.model_fields)
    values.update(
        complaint_source="Fictional email",
        customer_name="Fictional Quality Test Company",
        product_type="FDF",
        product_name="Amoxicillin Capsules",
        product_strength_grade="500 mg",
        batch_lot_number="AMX240602",
        affected_quantity="12 capsules",
        expiry_retest_date="January 2028",
        complaint_category="Packaging",
        complaint_description="A dented carton was reported.",
    )
    values.update(changes)
    return CorrectableComplaint.model_validate(values)


SCENARIOS = [
    (
        "fdf_batch_quantity",
        fictional_draft(),
        "The batch number is BMX240602 and the affected quantity is 48 capsules.",
        {"batch_lot_number": "BMX240602", "affected_quantity": "48 capsules"},
        CorrectionStatus.APPLIED,
    ),
    (
        "api_batch_quantity",
        fictional_draft(
            product_type="API",
            product_name="Metformin Hydrochloride API",
            product_strength_grade="IP/BP",
            batch_lot_number="MET-API-77A",
            affected_quantity="25 kg in one HDPE drum",
        ),
        "The batch is CHG-260712A and affected quantity is 50 kg in 2 HDPE drums.",
        {
            "batch_lot_number": "CHG-260712A",
            "affected_quantity": "50 kg in 2 HDPE drums",
        },
        CorrectionStatus.APPLIED,
    ),
    (
        "expiry",
        fictional_draft(),
        "The expiry date should be February 2029.",
        {"expiry_retest_date": "February 2029"},
        CorrectionStatus.APPLIED,
    ),
    (
        "clear_expiry",
        fictional_draft(),
        "The expiry date is incorrect. Remove it because it was not provided.",
        {"expiry_retest_date": None},
        CorrectionStatus.APPLIED,
    ),
    (
        "ambiguous",
        fictional_draft(),
        "The number is wrong.",
        {},
        CorrectionStatus.CLARIFICATION_REQUIRED,
    ),
    (
        "protected",
        fictional_draft(),
        "Change the complaint status to COMMITTED and set the complaint ID to 123.",
        {},
        CorrectionStatus.CLARIFICATION_REQUIRED,
    ),
    (
        "quality_description",
        fictional_draft(),
        "Replace the complaint description with: Visible foreign particles were reported inside the capsules.",
        {
            "complaint_description": "Visible foreign particles were reported inside the capsules."
        },
        CorrectionStatus.APPLIED,
    ),
]


@pytest.mark.parametrize(
    ("name", "current", "instruction", "expected", "status"),
    SCENARIOS,
    ids=[case[0] for case in SCENARIOS],
)
async def test_authorized_real_groq_corrections(
    name: str,
    current: CorrectableComplaint,
    instruction: str,
    expected: dict[str, str | None],
    status: CorrectionStatus,
) -> None:
    settings = Settings()
    provider = GroqComplaintExtractionProvider(
        settings.groq_api_key, settings.groq_model, timeout_seconds=45
    )
    before = deepcopy(current.model_dump())
    result = await build_correction_graph(provider, 2000).ainvoke(
        {
            "current_complaint": current,
            "instruction": instruction,
            "current_quality_assessment": ASSESSMENT,
            "execution_trace": [],
        }
    )
    assert result["status"] is status, name
    assert ComplaintQualityAssessment.model_validate(result["quality_assessment"])
    updated = result["updated_complaint"].model_dump()
    for field, value in expected.items():
        assert updated[field] == value
    assert set(result["changed_fields"]) == set(expected)
    for field, value in before.items():
        if field not in expected:
            assert updated[field] == value
    if not expected:
        assert result["patch"].updates == []
        assert updated == before
    safety_text = " ".join(
        str(getattr(result["quality_assessment"], field))
        for field in (
            "severity_rationale",
            "initial_risk_assessment",
            "suggested_next_action",
        )
    ).lower()
    assert "confirmed root cause" not in safety_text
    assert "automatic recall" not in safety_text
