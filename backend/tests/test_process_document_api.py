from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.graph import build_complaint_graph
from app.api.dependencies import get_document_processing_service
from app.core.config import Settings
from app.main import create_app
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from app.services.text_processing import TextComplaintProcessingService
from tests.pdf_factory import make_encrypted_pdf, make_pdf
from tests.test_text_processing import FakeProvider, extraction


@pytest.fixture
async def document_client() -> AsyncIterator[AsyncClient]:
    provider = FakeProvider(
        extraction(
            customer_name="ABC Formulations Ltd.",
            product_type="API",
            product_name="Metformin Hydrochloride API",
            product_strength_grade="IP/BP",
            batch_lot_number="MET-API-77A",
            affected_quantity="25 kg in one HDPE drum",
            complaint_description="Foreign particles observed.",
        )
    )
    text_service = TextComplaintProcessingService(
        build_complaint_graph(provider, 2000), provider
    )
    service = DocumentComplaintProcessingService(
        text_service, PdfTextExtractor(), 100_000, 1, 10, 2000
    )
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    app.dependency_overrides[get_document_processing_service] = lambda: service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


async def test_valid_pdf_returns_contract(document_client: AsyncClient) -> None:
    response = await document_client.post(
        "/api/complaints/process-document",
        files={"file": ("api.PDF", make_pdf("Batch MET-API-77A"), "application/pdf")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "PDF"
    assert body["document"]["filename"] == "api.PDF"
    assert body["extracted_complaint"]["batch_lot_number"] == "MET-API-77A"
    assert "extracted_text" not in body


@pytest.mark.parametrize("field", [None, "document"])
async def test_missing_or_wrong_multipart_field_returns_422(
    document_client: AsyncClient, field: str | None
) -> None:
    files = (
        {} if field is None else {field: ("a.pdf", make_pdf("text"), "application/pdf")}
    )
    response = await document_client.post(
        "/api/complaints/process-document", files=files
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize(
    ("filename", "content", "content_type", "status_code", "code"),
    [
        ("x.txt", b"text", "text/plain", 415, "UNSUPPORTED_DOCUMENT_TYPE"),
        ("x.pdf", b"%PDF-corrupt", "application/pdf", 422, "UNREADABLE_PDF"),
        ("x.pdf", make_encrypted_pdf(), "application/pdf", 422, "ENCRYPTED_PDF"),
        ("x.pdf", make_pdf(""), "application/pdf", 422, "NO_EXTRACTABLE_TEXT"),
    ],
)
async def test_document_errors_are_controlled(
    document_client: AsyncClient,
    filename: str,
    content: bytes,
    content_type: str,
    status_code: int,
    code: str,
) -> None:
    response = await document_client.post(
        "/api/complaints/process-document",
        files={"file": (filename, content, content_type)},
    )
    assert response.status_code == status_code
    assert response.json()["error"]["code"] == code


async def test_oversized_document_returns_413(document_client: AsyncClient) -> None:
    response = await document_client.post(
        "/api/complaints/process-document",
        files={"file": ("large.pdf", b"%PDF-" + b"x" * 100_001, "application/pdf")},
    )
    assert response.status_code == 413
    assert response.json()["error"]["code"] == "DOCUMENT_TOO_LARGE"
