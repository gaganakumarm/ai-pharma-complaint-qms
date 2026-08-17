import re
from collections.abc import Mapping
from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph

from app.ai.providers import ComplaintExtractionProvider
from app.core.exceptions import InputProcessingError, MalformedProviderResponseError
from app.domain import SourceType
from app.schemas.extraction import ExtractedComplaint


class ComplaintGraphState(TypedDict, total=False):
    raw_text: str
    normalized_text: str
    source_type: SourceType
    extracted_complaint: ExtractedComplaint
    provider_payload: Mapping[str, Any]
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
    async def normalize_input(state: ComplaintGraphState) -> ComplaintGraphState:
        return {
            "normalized_text": normalize_text(state["raw_text"], maximum_length),
            "source_type": SourceType.TEXT,
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
        warnings = [
            warning
            for field, warning in IMPORTANT_FIELDS.items()
            if getattr(extraction, field) is None
        ]
        return {
            "extracted_complaint": extraction,
            "validation_warnings": warnings,
            "execution_trace": [
                *state.get("execution_trace", []),
                "validate_extraction",
            ],
        }

    async def prepare_response(state: ComplaintGraphState) -> ComplaintGraphState:
        warnings = state["validation_warnings"]
        message = "I extracted the complaint details that were present. " + (
            "Please review the missing information listed below."
            if warnings
            else "Please review the populated form before committing it."
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
    builder.add_node("prepare_response", prepare_response)
    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "extract_complaint_fields")
    builder.add_edge("extract_complaint_fields", "validate_extraction")
    builder.add_edge("validate_extraction", "prepare_response")
    builder.add_edge("prepare_response", END)
    return builder.compile()
