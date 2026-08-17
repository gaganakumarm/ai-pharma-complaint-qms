import os

import pytest

from app.ai.graph import build_complaint_graph
from app.ai.providers import GroqComplaintExtractionProvider
from app.core.config import Settings
from app.schemas.assessment import HUMAN_REVIEW_DISCLAIMER, AssessmentStatus
from app.schemas.extraction import ProcessTextResponse
from app.services.text_processing import TextComplaintProcessingService

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_GROQ_SMOKE") != "1" or not os.getenv("GROQ_API_KEY"),
    reason="manual assessment/Groq smoke requires RUN_GROQ_SMOKE=1 and GROQ_API_KEY",
)


async def process(text: str) -> ProcessTextResponse:
    settings = Settings()
    provider = GroqComplaintExtractionProvider(
        settings.groq_api_key, settings.groq_model, timeout_seconds=30
    )
    service = TextComplaintProcessingService(
        build_complaint_graph(provider, settings.max_text_input_length), provider
    )
    return await service.process(text)


@pytest.mark.parametrize(
    "text",
    [
        (
            "Apollo Pharmacy reports brown discoloration in Amoxicillin Capsules "
            "500 mg, batch AMX-FDF-2407, affecting 18 cartons."
        ),
        (
            "ABC Formulations reports dark foreign particles in Metformin "
            "Hydrochloride IP/BP API, batch MET-API-77A, 25 kg in an HDPE drum."
        ),
        (
            "A customer reports damaged tablets. Batch, quantity, dates and product "
            "name were not provided."
        ),
        (
            "The outer secondary carton of Paracetamol 500 mg tablets batch COS-1 "
            "has a small scuff. The sealed blister and all printed information are "
            "intact and readable."
        ),
    ],
)
async def test_real_assessment_contract(text: str) -> None:
    response = await process(text)
    assessment = response.quality_assessment
    assert assessment.complaint_category
    assert assessment.suggested_severity.value in {"MINOR", "MAJOR", "CRITICAL"}
    assert assessment.severity_rationale
    assert assessment.initial_risk_assessment
    assert assessment.suggested_next_action
    assert assessment.human_review_required is True
    assert assessment.disclaimer == HUMAN_REVIEW_DISCLAIMER
    combined = " ".join(
        (
            assessment.severity_rationale,
            assessment.initial_risk_assessment,
            assessment.suggested_next_action,
        )
    ).lower()
    assert "root cause has been confirmed" not in combined
    assert "automatically initiate a recall" not in combined


async def test_real_incomplete_assessment_exposes_uncertainty() -> None:
    response = await process("A customer reports damaged tablets.")
    assert response.extracted_complaint.batch_lot_number is None
    assert response.extracted_complaint.affected_quantity is None
    assert (
        response.quality_assessment.assessment_status
        is AssessmentStatus.NEEDS_INFORMATION
    )
    assert response.quality_assessment.information_gaps


async def test_real_api_assessment_considers_downstream_context() -> None:
    response = await process(
        "Metformin Hydrochloride API IP grade batch API-DOWN-1 contains foreign "
        "particles."
    )
    assessment_text = (
        response.quality_assessment.initial_risk_assessment
        + " "
        + response.quality_assessment.severity_rationale
    ).lower()
    assert any(
        term in assessment_text
        for term in ("downstream", "finished", "fdf", "manufactur")
    )
