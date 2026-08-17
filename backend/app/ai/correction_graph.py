import re
from collections.abc import Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.graph import build_extraction_warnings, deterministic_test_recommendations
from app.ai.providers import ComplaintExtractionProvider
from app.core.exceptions import InputProcessingError, MalformedProviderResponseError
from app.schemas.assessment import ComplaintQualityAssessment
from app.schemas.correction import (
    ComplaintCorrectionPatch,
    CorrectableComplaint,
    CorrectionField,
    CorrectionStatus,
)
from app.schemas.enhancements import RcaCapaRecommendations
from app.services.corrections import merge_correction

RISK_FIELDS = set(CorrectionField) - {
    CorrectionField.COMPLAINT_SOURCE,
    CorrectionField.CUSTOMER_NAME,
}
RCA_CAPA_FIELDS = RISK_FIELDS


class CorrectionGraphState(TypedDict, total=False):
    current_complaint: CorrectableComplaint
    instruction: str
    normalized_instruction: str
    current_quality_assessment: ComplaintQualityAssessment
    provider_payload: Mapping[str, Any]
    patch: ComplaintCorrectionPatch
    updated_complaint: CorrectableComplaint
    changed_fields: list[CorrectionField]
    reassessment_required: bool
    assessment_payload: Mapping[str, Any]
    quality_assessment: ComplaintQualityAssessment
    current_rca_capa_recommendations: RcaCapaRecommendations | None
    rca_capa_payload: Mapping[str, Any]
    rca_capa_recommendations: RcaCapaRecommendations
    warnings: list[str]
    assistant_message: str
    status: CorrectionStatus
    execution_trace: list[str]


def normalize_correction_instruction(instruction: str, maximum_length: int) -> str:
    normalized = re.sub(r"\s+", " ", instruction.strip())
    if not normalized:
        raise InputProcessingError("Correction instruction must not be blank")
    if len(normalized) > maximum_length:
        raise InputProcessingError(
            f"Correction instruction must not exceed {maximum_length} characters"
        )
    return normalized


def _label(field: CorrectionField) -> str:
    return field.value.replace("_", " ").title().replace("Lot", "Lot")


def build_correction_graph(
    provider: ComplaintExtractionProvider, maximum_length: int
) -> Any:
    async def normalize(state: CorrectionGraphState) -> CorrectionGraphState:
        return {
            "normalized_instruction": normalize_correction_instruction(
                state["instruction"], maximum_length
            ),
            "execution_trace": [
                *state.get("execution_trace", []),
                "normalize_instruction",
            ],
        }

    async def extract(state: CorrectionGraphState) -> CorrectionGraphState:
        payload = await provider.extract_correction(
            state["current_complaint"], state["normalized_instruction"]
        )
        return {
            "provider_payload": payload,
            "execution_trace": [*state["execution_trace"], "extract_correction"],
        }

    async def validate(state: CorrectionGraphState) -> CorrectionGraphState:
        try:
            patch = ComplaintCorrectionPatch.model_validate(state["provider_payload"])
        except Exception as exc:
            raise MalformedProviderResponseError from exc
        return {
            "patch": patch,
            "execution_trace": [*state["execution_trace"], "validate_patch"],
        }

    async def merge(state: CorrectionGraphState) -> CorrectionGraphState:
        result = merge_correction(state["current_complaint"], state["patch"])
        return {
            "updated_complaint": result.complaint,
            "changed_fields": result.changed_fields,
            "reassessment_required": bool(set(result.changed_fields) & RISK_FIELDS),
            "execution_trace": [*state["execution_trace"], "merge_patch"],
        }

    async def warnings(state: CorrectionGraphState) -> CorrectionGraphState:
        return {
            "warnings": build_extraction_warnings(state["updated_complaint"]),
            "execution_trace": [*state["execution_trace"], "recalculate_warnings"],
        }

    async def reassess(state: CorrectionGraphState) -> CorrectionGraphState:
        payload = (
            await provider.assess_complaint(state["updated_complaint"])
            if state["reassessment_required"]
            else state["current_quality_assessment"].model_dump()
        )
        return {
            "assessment_payload": payload,
            "execution_trace": [*state["execution_trace"], "reassess_complaint"],
        }

    async def validate_assessment(state: CorrectionGraphState) -> CorrectionGraphState:
        try:
            assessment = ComplaintQualityAssessment.model_validate(
                state["assessment_payload"]
            )
        except Exception as exc:
            raise MalformedProviderResponseError from exc
        return {
            "quality_assessment": assessment,
            "execution_trace": [*state["execution_trace"], "validate_assessment"],
        }

    async def recommend_rca_capa(state: CorrectionGraphState) -> CorrectionGraphState:
        changed = bool(set(state["changed_fields"]) & RCA_CAPA_FIELDS)
        if changed or state.get("current_rca_capa_recommendations") is None:
            method = getattr(provider, "recommend_rca_capa", None)
            payload = (
                await method(state["updated_complaint"], state["quality_assessment"])
                if method
                else deterministic_test_recommendations()
            )
        else:
            current = state["current_rca_capa_recommendations"]
            if current is None:
                raise MalformedProviderResponseError
            payload = current.model_dump()
        return {
            "rca_capa_payload": payload,
            "execution_trace": [*state["execution_trace"], "recommend_rca_capa"],
        }

    async def validate_rca_capa(state: CorrectionGraphState) -> CorrectionGraphState:
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

    async def prepare(state: CorrectionGraphState) -> CorrectionGraphState:
        if state["patch"].clarification_required:
            status = CorrectionStatus.CLARIFICATION_REQUIRED
            message = (
                state["patch"].clarification_question
                or "Please clarify the requested correction."
            )
        elif not state["changed_fields"]:
            status = CorrectionStatus.NO_CHANGES
            message = (
                "The draft already contains the requested values; "
                "no fields were changed."
            )
        else:
            status = CorrectionStatus.APPLIED
            descriptions = [
                f"{_label(field)} to "
                f"{getattr(state['updated_complaint'], field.value) or 'cleared'}"
                for field in state["changed_fields"]
            ]
            message = (
                "Updated "
                + ", ".join(descriptions)
                + ". Review the draft before committing it."
            )
        return {
            "status": status,
            "assistant_message": message,
            "execution_trace": [*state["execution_trace"], "prepare_response"],
        }

    builder = StateGraph(CorrectionGraphState)
    for name, node in (
        ("normalize_instruction", normalize),
        ("extract_correction", extract),
        ("validate_patch", validate),
        ("merge_patch", merge),
        ("recalculate_warnings", warnings),
        ("reassess_complaint", reassess),
        ("validate_assessment", validate_assessment),
        ("recommend_rca_capa", recommend_rca_capa),
        ("validate_rca_capa", validate_rca_capa),
        ("prepare_response", prepare),
    ):
        builder.add_node(name, node)
    order = [
        "normalize_instruction",
        "extract_correction",
        "validate_patch",
        "merge_patch",
        "recalculate_warnings",
        "reassess_complaint",
        "validate_assessment",
        "recommend_rca_capa",
        "validate_rca_capa",
        "prepare_response",
    ]
    builder.add_edge(START, order[0])
    for before, after in zip(order, order[1:], strict=False):
        builder.add_edge(before, after)
    builder.add_edge(order[-1], END)
    return builder.compile()
