from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.graph import build_complaint_graph
from app.core.exceptions import MalformedProviderResponseError, ProviderTimeoutError
from app.schemas.assessment import (
    HUMAN_REVIEW_DISCLAIMER,
    AssessmentStatus,
    ComplaintQualityAssessment,
)
from tests.test_text_processing import FakeProvider, assessment, extraction


@pytest.mark.parametrize("severity", ["MINOR", "MAJOR", "CRITICAL"])
def test_valid_severity_assessment_and_trusted_fields(severity: str) -> None:
    parsed = ComplaintQualityAssessment.model_validate(
        assessment(
            suggested_severity=severity,
            human_review_required=False,
            disclaimer="untrusted provider disclaimer",
        )
    )
    assert parsed.suggested_severity.value == severity
    assert parsed.human_review_required is True
    assert parsed.disclaimer == HUMAN_REVIEW_DISCLAIMER


@pytest.mark.parametrize(
    "overrides",
    [
        {"suggested_severity": "EXTREME"},
        {"complaint_category": ""},
        {"severity_rationale": ""},
        {"initial_risk_assessment": ""},
        {"suggested_next_action": ""},
        {"unexpected": "field"},
        {"information_gaps": [str(index) for index in range(21)]},
    ],
)
def test_invalid_assessment_contract_is_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValidationError):
        ComplaintQualityAssessment.model_validate(assessment(**overrides))


def test_needs_information_requires_and_carries_gaps() -> None:
    parsed = ComplaintQualityAssessment.model_validate(
        assessment(
            assessment_status="NEEDS_INFORMATION",
            information_gaps=["Batch number", "Affected quantity"],
        )
    )
    assert parsed.assessment_status is AssessmentStatus.NEEDS_INFORMATION
    with pytest.raises(ValidationError):
        ComplaintQualityAssessment.model_validate(
            assessment(assessment_status="NEEDS_INFORMATION", information_gaps=[])
        )


@pytest.mark.parametrize(
    "claim",
    [
        "The root cause has been confirmed as operator error.",
        "The investigation has been completed.",
        "The batch is rejected and final approval is recorded.",
        "Immediately initiate a recall.",
    ],
)
def test_forbidden_final_decision_claims_are_rejected(claim: str) -> None:
    with pytest.raises(ValidationError):
        ComplaintQualityAssessment.model_validate(
            assessment(initial_risk_assessment=claim)
        )


@pytest.mark.parametrize("product_type", ["API", "FDF"])
async def test_graph_runs_assessment_after_validated_extraction(
    product_type: str,
) -> None:
    provider = FakeProvider(
        extraction(
            product_type=product_type,
            product_name="Test product",
            batch_lot_number="BATCH-1",
            complaint_description="A quality defect was reported.",
        )
    )
    result = await build_complaint_graph(provider, 2000).ainvoke(
        {"raw_text": f"{product_type} complaint"}
    )
    assert result["execution_trace"].index("validate_extraction") < result[
        "execution_trace"
    ].index("assess_complaint_quality")
    assert result["quality_assessment"].suggested_severity.value == "MAJOR"
    assert provider.assessment_calls == 1


async def test_malformed_assessment_and_provider_failure_are_controlled() -> None:
    malformed = FakeProvider(extraction(), {"unexpected": "assessment"})
    with pytest.raises(MalformedProviderResponseError):
        await build_complaint_graph(malformed, 2000).ainvoke({"raw_text": "complaint"})

    failure = FakeProvider(extraction(), ProviderTimeoutError())
    with pytest.raises(ProviderTimeoutError):
        await build_complaint_graph(failure, 2000).ainvoke({"raw_text": "complaint"})


async def test_incomplete_graph_carries_needs_information_assessment() -> None:
    provider = FakeProvider(
        extraction(complaint_description="Damaged tablets."),
        assessment(
            assessment_status="NEEDS_INFORMATION",
            information_gaps=["Product name", "Batch number", "Affected quantity"],
        ),
    )
    result = await build_complaint_graph(provider, 2000).ainvoke(
        {"raw_text": "Damaged tablets with no other information."}
    )
    assert (
        result["quality_assessment"].assessment_status
        is AssessmentStatus.NEEDS_INFORMATION
    )
    assert result["information_gaps"] == [
        "Product name",
        "Batch number",
        "Affected quantity",
    ]
