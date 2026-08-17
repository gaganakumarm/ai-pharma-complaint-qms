from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.graph import build_complaint_graph
from app.api.dependencies import get_text_processing_service
from app.core.config import Settings
from app.core.exceptions import (
    MalformedProviderResponseError,
    ProviderAuthenticationError,
    ProviderRateLimitError,
    ProviderTimeoutError,
)
from app.main import create_app
from app.services.text_processing import TextComplaintProcessingService
from tests.test_text_processing import FakeProvider, extraction


@pytest.fixture
async def text_client() -> AsyncIterator[tuple[AsyncClient, object]]:
    provider = FakeProvider(
        extraction(
            customer_name="Apollo Pharmacy",
            product_type="FDF",
            product_name="Paracetamol",
            product_strength_grade="500 mg",
            batch_lot_number="FDF-42",
            complaint_description="Cracked tablets were received.",
        )
    )
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    service = TextComplaintProcessingService(
        build_complaint_graph(provider, 1000), provider
    )
    app.dependency_overrides[get_text_processing_service] = lambda: service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client, app


async def test_valid_process_text_returns_draft_without_persistence(
    text_client: tuple[AsyncClient, object],
) -> None:
    client, _app = text_client
    response = await client.post(
        "/api/complaints/process-text", json={"text": "FDF email"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "TEXT"
    assert body["extracted_complaint"]["product_type"] == "FDF"
    assert body["status"] == "PROCESSED"
    assert body["quality_assessment"]["suggested_severity"] == "MAJOR"
    assert body["quality_assessment"]["human_review_required"] is True
    assert "authorised quality personnel" in body["quality_assessment"]["disclaimer"]


@pytest.mark.parametrize("text", ["", "   "])
async def test_empty_input_is_rejected(
    text_client: tuple[AsyncClient, object], text: str
) -> None:
    client, _app = text_client
    response = await client.post("/api/complaints/process-text", json={"text": text})
    assert response.status_code == 422
    assert response.json()["error"]["code"] in {
        "VALIDATION_ERROR",
        "INVALID_COMPLAINT_TEXT",
    }


async def test_oversized_input_is_rejected(
    text_client: tuple[AsyncClient, object],
) -> None:
    client, _app = text_client
    response = await client.post(
        "/api/complaints/process-text", json={"text": "x" * 1001}
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COMPLAINT_TEXT"


async def test_missing_groq_configuration_is_controlled() -> None:
    app = create_app(
        Settings(database_url="sqlite+aiosqlite:///:memory:", groq_api_key="")
    )
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/complaints/process-text", json={"text": "valid complaint"}
            )
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AI_NOT_CONFIGURED"


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (ProviderAuthenticationError(), 502, "AI_AUTHENTICATION_FAILED"),
        (ProviderTimeoutError(), 504, "AI_TIMEOUT"),
        (ProviderRateLimitError(), 429, "AI_RATE_LIMITED"),
        (MalformedProviderResponseError(), 502, "AI_INVALID_RESPONSE"),
    ],
)
async def test_provider_failures_are_safely_mapped(
    failure: Exception, status_code: int, code: str
) -> None:
    provider = FakeProvider(failure)
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    service = TextComplaintProcessingService(
        build_complaint_graph(provider, 1000), provider
    )
    app.dependency_overrides[get_text_processing_service] = lambda: service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/complaints/process-text", json={"text": "complaint"}
            )
    assert response.status_code == status_code
    assert response.json() == {
        "error": {"code": code, "message": str(failure), "details": None}
    }


async def test_assessment_failure_is_controlled_without_partial_response() -> None:
    provider = FakeProvider(
        extraction(complaint_description="Reported defect."), ProviderTimeoutError()
    )
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    service = TextComplaintProcessingService(
        build_complaint_graph(provider, 1000), provider
    )
    app.dependency_overrides[get_text_processing_service] = lambda: service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/complaints/process-text", json={"text": "complaint"}
            )
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "AI_TIMEOUT"
    assert provider.calls == provider.assessment_calls == 1
