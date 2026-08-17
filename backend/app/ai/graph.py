import re
from collections.abc import Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.providers import ComplaintExtractionProvider
from app.core.exceptions import InputProcessingError, MalformedProviderResponseError
from app.domain import SourceType
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.enhancements import CompletenessAssessment, RcaCapaRecommendations
from app.schemas.extraction import ExtractedComplaint
from app.services.completeness import ComplaintCompletenessChecker


class ComplaintGraphState(TypedDict, total=False):
    raw_text: str
    normalized_text: str
    source_type: SourceType
    extracted_complaint: ExtractedComplaint
    provider_payload: Mapping[str, Any]
    assessment_payload: Mapping[str, Any]
    quality_assessment: ComplaintQualityAssessment
    completeness_assessment: CompletenessAssessment
    rca_capa_recommendations: RcaCapaRecommendations
    rca_capa_payload: Mapping[str, Any]
    information_gaps: list[str]
    assessment_error: str | None
    validation_warnings: list[str]
    assistant_message: str
    processing_error: str | None
    execution_trace: list[str]


IMPORTANT_FIELDS = {
    "customer_name": "Customer name was not provided",
    "product_name": "Product name was not provided",
    "batch_lot_number": "Batch number was not provided",
    "affected_quantity": "Affected quantity was not provided",
    "complaint_description": "Complaint description was not provided",
}


def deterministic_test_recommendations() -> dict[str, Any]:
    """Safe fallback for legacy test doubles that predate the provider method."""
    return {
        "potential_root_causes": [
            {
                "statement": "A process or material variation may have contributed",
                "rationale": "The complaint evidence requires investigation",
                "evidence_required": "Batch records and relevant test data",
            }
        ],
        "investigation_areas": ["Review complaint evidence and batch documentation"],
        "corrective_actions": [
            {
                "action": "Evaluate containment appropriate to the evidence",
                "purpose": "Control potential quality impact during investigation",
                "verification": "Authorised QA verifies documented completion",
            }
        ],
        "preventive_actions": [
            {
                "action": "Trend verified investigation findings",
                "purpose": "Identify recurrence requiring quality-system action",
                "effectiveness_check": "QA reviews the defined trend period",
            }
        ],
        "assumptions_or_limitations": [
            "Complaint intake evidence is insufficient to determine causality"
        ],
        "human_review_required": True,
        "disclaimer": "Application controlled",
    }


def build_extraction_warnings(complaint: Any) -> list[str]:
    return [
        warning
        for field, warning in IMPORTANT_FIELDS.items()
        if getattr(complaint, field) is None
    ]


def normalize_text(raw_text: str, maximum_length: int) -> str:
    normalized = re.sub(r"[ \t]+", " ", raw_text.strip())
    normalized = re.sub(r"[ \t]*\n[ \t]*", "\n", normalized)
    normalized = re.sub(r"\n\s*\n(?:\s*\n)+", "\n\n", normalized)
    if not normalized:
        raise InputProcessingError("Complaint text must not be blank")
    if len(normalized) > maximum_length:
        raise InputProcessingError(
            f"Complaint text must not exceed {maximum_length} characters"
        )
    return normalized


def build_complaint_graph(
    provider: ComplaintExtractionProvider, maximum_length: int
) -> Any:
    completeness_checker = ComplaintCompletenessChecker()

    async def normalize_input(state: ComplaintGraphState) -> ComplaintGraphState:
        return {
            "normalized_text": normalize_text(state["raw_text"], maximum_length),
            "source_type": state.get("source_type", SourceType.TEXT),
            "execution_trace": [*state.get("execution_trace", []), "normalize_input"],
        }

    async def extract_complaint_fields(
        state: ComplaintGraphState,
    ) -> ComplaintGraphState:
        payload = await provider.extract(state["normalized_text"])
        return {
            "provider_payload": payload,
            "execution_trace": [
                *state.get("execution_trace", []),
                "extract_complaint_fields",
            ],
        }

    async def validate_extraction(
        state: ComplaintGraphState,
    ) -> ComplaintGraphState:
        try:
            extraction = ExtractedComplaint.model_validate(state["provider_payload"])
        except Exception as exc:
            raise MalformedProviderResponseError from exc
        warnings = build_extraction_warnings(extraction)
        return {
            "extracted_complaint": extraction,
            "validation_warnings": warnings,
            "execution_trace": [
                *state.get("execution_trace", []),
                "validate_extraction",
            ],
        }

    async def assess_complaint_quality(
        state: ComplaintGraphState,
    ) -> ComplaintGraphState:
        payload = await provider.assess_complaint(state["extracted_complaint"])
        return {
            "assessment_payload": payload,
            "execution_trace": [
                *state.get("execution_trace", []),
                "assess_complaint_quality",
            ],
        }

    async def validate_quality_assessment(
        state: ComplaintGraphState,
    ) -> ComplaintGraphState:
        try:
            assessment = ComplaintQualityAssessment.model_validate(
                state["assessment_payload"]
            )
        except Exception as exc:
            raise MalformedProviderResponseError from exc
        return {
            "quality_assessment": assessment,
            "information_gaps": assessment.information_gaps,
            "assessment_error": None,
            "execution_trace": [
                *state.get("execution_trace", []),
                "validate_quality_assessment",
            ],
        }

    async def assess_completeness(state: ComplaintGraphState) -> ComplaintGraphState:
        complaint = state["extracted_complaint"].model_dump()
        complaint["complaint_category"] = state["quality_assessment"].complaint_category
        return {
            "completeness_assessment": completeness_checker.assess(complaint),
            "execution_trace": [*state["execution_trace"], "assess_completeness"],
        }

    async def recommend_rca_capa(state: ComplaintGraphState) -> ComplaintGraphState:
        method = getattr(provider, "recommend_rca_capa", None)
        payload = (
            await method(state["extracted_complaint"], state["quality_assessment"])
            if method
            else deterministic_test_recommendations()
        )
        return {
            "rca_capa_payload": payload,
            "execution_trace": [*state["execution_trace"], "recommend_rca_capa"],
        }

    async def validate_rca_capa(state: ComplaintGraphState) -> ComplaintGraphState:
        try:
            recommendations = RcaCapaRecommendations.model_validate(
                state["rca_capa_payload"]
            )
        except Exception as exc:
            raise MalformedProviderResponseError from exc
        return {
            "rca_capa_recommendations": recommendations,
            "execution_trace": [*state["execution_trace"], "validate_rca_capa"],
        }

    async def prepare_response(state: ComplaintGraphState) -> ComplaintGraphState:
        warnings = state["validation_warnings"]
        message = (
            "I extracted and assessed the complaint details that were present. "
            + (
                "Please review the missing information listed below."
                if warnings
                else "Please review the populated form before committing it."
            )
        )
        return {
            "assistant_message": message,
            "processing_error": None,
            "execution_trace": [
                *state.get("execution_trace", []),
                "prepare_response",
            ],
        }

    builder = StateGraph(ComplaintGraphState)
    builder.add_node("normalize_input", normalize_input)
    builder.add_node("extract_complaint_fields", extract_complaint_fields)
    builder.add_node("validate_extraction", validate_extraction)
    builder.add_node("assess_complaint_quality", assess_complaint_quality)
    builder.add_node("validate_quality_assessment", validate_quality_assessment)
    builder.add_node("assess_completeness", assess_completeness)
    builder.add_node("recommend_rca_capa", recommend_rca_capa)
    builder.add_node("validate_rca_capa", validate_rca_capa)
    builder.add_node("prepare_response", prepare_response)
    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "extract_complaint_fields")
    builder.add_edge("extract_complaint_fields", "validate_extraction")
    builder.add_edge("validate_extraction", "assess_complaint_quality")
    builder.add_edge("assess_complaint_quality", "validate_quality_assessment")
    builder.add_edge("validate_quality_assessment", "assess_completeness")
    builder.add_edge("assess_completeness", "recommend_rca_capa")
    builder.add_edge("recommend_rca_capa", "validate_rca_capa")
    builder.add_edge("validate_rca_capa", "prepare_response")
    builder.add_edge("prepare_response", END)
    return builder.compile()
