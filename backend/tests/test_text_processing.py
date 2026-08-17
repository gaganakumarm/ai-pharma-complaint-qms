from collections.abc import Mapping
from typing import Any

import pytest
from pydantic import ValidationError

from app.ai.graph import build_complaint_graph, normalize_text
from app.core.exceptions import (
    InputProcessingError,
    MalformedProviderResponseError,
    ProviderAuthenticationError,
)
from app.schemas.extraction import ExtractedComplaint
from app.services.text_processing import TextComplaintProcessingService


def extraction(**overrides: Any) -> dict[str, Any]:
    values: dict[str, Any] = {
        "complaint_source": None,
        "customer_name": None,
        "product_type": "UNKNOWN",
        "product_name": None,
        "product_strength_grade": None,
        "batch_lot_number": None,
        "affected_quantity": None,
        "manufacturing_date": None,
        "expiry_retest_date": None,
        "originating_site_block": None,
        "impacted_non_product_materials": None,
        "complaint_description": None,
    }
    values.update(overrides)
    return values


class FakeProvider:
    model = "fake-structured-model"

    def __init__(self, payload: Mapping[str, Any] | Exception) -> None:
        self.payload = payload
        self.calls = 0

    async def extract(self, _text: str) -> Mapping[str, Any]:
        self.calls += 1
        if isinstance(self.payload, Exception):
            raise self.payload
        return self.payload


def test_normalize_input_preserves_identifier_and_spacing() -> None:
    normalized = normalize_text("  Batch: API-77/A   received\n\n\n  today  ", 1000)
    assert normalized == "Batch: API-77/A received\n\ntoday"


@pytest.mark.parametrize("text", ["", "  \n \t"])
def test_normalize_rejects_blank(text: str) -> None:
    with pytest.raises(InputProcessingError):
        normalize_text(text, 1000)


def test_normalize_rejects_oversized_input() -> None:
    with pytest.raises(InputProcessingError):
        normalize_text("x" * 1001, 1000)


def test_extraction_normalizes_empty_strings_and_rejects_unknown_fields() -> None:
    parsed = ExtractedComplaint.model_validate(
        extraction(customer_name="  ", manufacturing_date="March 2026")
    )
    assert parsed.customer_name is None
    assert parsed.manufacturing_date == "March 2026"
    with pytest.raises(ValidationError):
        ExtractedComplaint.model_validate(extraction(invented_field="bad"))


@pytest.mark.parametrize(
    ("product_type", "product_name", "detail"),
    [("FDF", "Paracetamol", "500 mg"), ("API", "Metformin HCl", "USP")],
)
async def test_langgraph_executes_all_nodes_for_api_and_fdf(
    product_type: str, product_name: str, detail: str
) -> None:
    provider = FakeProvider(
        extraction(
            customer_name="Apollo Pharmacy",
            product_type=product_type,
            product_name=product_name,
            product_strength_grade=detail,
            batch_lot_number="LOT-9/A",
            complaint_description="Material did not meet expectations.",
        )
    )
    graph = build_complaint_graph(provider, 2000)
    result = await graph.ainvoke({"raw_text": "  complaint LOT-9/A  "})
    assert result["execution_trace"] == [
        "normalize_input",
        "extract_complaint_fields",
        "validate_extraction",
        "prepare_response",
    ]
    assert result["extracted_complaint"].product_type.value == product_type
    assert result["extracted_complaint"].batch_lot_number == "LOT-9/A"


async def test_incomplete_graph_keeps_nulls_and_truthful_message() -> None:
    provider = FakeProvider(extraction(complaint_description="Tablets were cracked."))
    service = TextComplaintProcessingService(
        build_complaint_graph(provider, 2000), provider
    )
    response = await service.process("Tablets were cracked.")
    assert response.extracted_complaint.batch_lot_number is None
    assert "Batch number was not provided" in response.warnings
    assert "missing information" in response.assistant_message
    assert "batch was extracted" not in response.assistant_message.lower()


async def test_provider_failure_propagates_without_retry() -> None:
    provider = FakeProvider(ProviderAuthenticationError())
    graph = build_complaint_graph(provider, 2000)
    with pytest.raises(ProviderAuthenticationError):
        await graph.ainvoke({"raw_text": "valid complaint"})
    assert provider.calls == 1


async def test_invalid_provider_shape_is_controlled() -> None:
    provider = FakeProvider({"unexpected": "field"})
    graph = build_complaint_graph(provider, 2000)
    with pytest.raises(MalformedProviderResponseError):
        await graph.ainvoke({"raw_text": "valid complaint"})
