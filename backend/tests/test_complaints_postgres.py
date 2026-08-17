import os
import re
import uuid
from collections.abc import AsyncIterator

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.graph import build_complaint_graph
from app.api.dependencies import get_document_processing_service
from app.core.config import Settings
from app.main import create_app
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from app.services.text_processing import TextComplaintProcessingService
from tests.pdf_factory import make_pdf
from tests.test_text_processing import FakeProvider, extraction

pytestmark = pytest.mark.skipif(
    not os.getenv("TEST_DATABASE_URL"), reason="TEST_DATABASE_URL is not configured"
)


def valid_payload(suffix: str = "1") -> dict[str, str]:
    return {
        "source_type": "MANUAL",
        "complaint_source": "Phone",
        "customer_name": f"Hospital {suffix}",
        "product_type": "FDF",
        "product_name": "Paracetamol 500 mg",
        "batch_lot_number": f"LOT-{suffix}",
        "manufacturing_date": "March 2026",
        "expiry_retest_date": "Not Provided",
        "complaint_category": "Packaging",
        "complaint_description": "Blister seal was damaged on receipt.",
    }


@pytest.fixture
async def pg_client() -> AsyncIterator[AsyncClient]:
    settings = Settings(database_url=os.environ["TEST_DATABASE_URL"])
    app = create_app(settings)
    provider = FakeProvider(
        extraction(
            product_type="FDF",
            product_name="Amoxicillin Capsules",
            batch_lot_number="PG-PDF-1",
            complaint_description="Discoloration complaint.",
        )
    )
    text_service = TextComplaintProcessingService(
        build_complaint_graph(provider, 2000), provider
    )
    document_service = DocumentComplaintProcessingService(
        text_service, PdfTextExtractor(), 1_000_000, 1, 10, 2000
    )
    app.dependency_overrides[get_document_processing_service] = lambda: document_service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


@pytest.fixture
async def pg_connection() -> AsyncIterator[asyncpg.Connection]:
    connection = await asyncpg.connect(
        os.environ["TEST_DATABASE_URL"].replace("postgresql+asyncpg", "postgresql")
    )
    try:
        yield connection
    finally:
        await connection.close()


async def test_create_retrieve_and_number_uniqueness(pg_client: AsyncClient) -> None:
    first = await pg_client.post("/api/complaints", json=valid_payload("multi-a"))
    second = await pg_client.post("/api/complaints", json=valid_payload("multi-b"))
    assert first.status_code == second.status_code == 201
    first_body, second_body = first.json(), second.json()
    assert re.fullmatch(r"CMP-\d{4}-\d{6}", first_body["complaint_number"])
    assert first_body["complaint_number"] != second_body["complaint_number"]
    assert first_body["status"] == "COMMITTED"
    assert first_body["manufacturing_date"] == "March 2026"

    retrieved = await pg_client.get(f"/api/complaints/{first_body['id']}")
    assert retrieved.status_code == 200
    assert retrieved.json()["complaint_number"] == first_body["complaint_number"]


async def test_validation_errors_use_standard_contract(pg_client: AsyncClient) -> None:
    missing = await pg_client.post("/api/complaints", json={})
    blank = await pg_client.post(
        "/api/complaints", json={**valid_payload("blank"), "customer_name": " "}
    )
    malformed = await pg_client.get("/api/complaints/not-a-uuid")
    unknown = await pg_client.get(f"/api/complaints/{uuid.uuid4()}")
    assert missing.status_code == blank.status_code == malformed.status_code == 422
    assert missing.json()["error"]["code"] == "VALIDATION_ERROR"
    assert unknown.status_code == 404
    assert unknown.json()["error"]["code"] == "HTTP_404"


async def test_list_is_paginated_newest_first(pg_client: AsyncClient) -> None:
    created = [
        (
            await pg_client.post("/api/complaints", json=valid_payload(f"page-{i}"))
        ).json()
        for i in range(3)
    ]
    response = await pg_client.get("/api/complaints?page=1&page_size=2")
    assert response.status_code == 200
    body = response.json()
    assert len(body["items"]) == 2
    assert body["total"] >= 3
    assert body["items"][0]["id"] == created[-1]["id"]


async def test_invalid_pagination_is_rejected(pg_client: AsyncClient) -> None:
    response = await pg_client.get("/api/complaints?page=0&page_size=101")
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_database_constraint_failure_leaves_no_partial_record(
    pg_connection: asyncpg.Connection,
) -> None:
    before = await pg_connection.fetchval("SELECT count(*) FROM complaints")
    with pytest.raises(asyncpg.InvalidTextRepresentationError):
        async with pg_connection.transaction():
            await pg_connection.execute(
                """
                INSERT INTO complaints (
                    id, source_type, customer_name, product_type, product_name,
                    batch_lot_number, complaint_category, complaint_description, status
                ) VALUES ($1, 'MANUAL', 'Constraint Test', 'BIOLOGIC', 'Product',
                          'LOT-CONSTRAINT', 'Quality', 'Invalid enum test', 'COMMITTED')
                """,
                uuid.uuid4(),
            )
    after = await pg_connection.fetchval("SELECT count(*) FROM complaints")
    assert after == before


async def test_process_document_does_not_create_ledger_row(
    pg_client: AsyncClient, pg_connection: asyncpg.Connection
) -> None:
    before = await pg_connection.fetchval("SELECT count(*) FROM complaints")
    response = await pg_client.post(
        "/api/complaints/process-document",
        files={
            "file": (
                "fictional.pdf",
                make_pdf("FDF batch PG-PDF-1 discoloration complaint"),
                "application/pdf",
            )
        },
    )
    after = await pg_connection.fetchval("SELECT count(*) FROM complaints")
    assert response.status_code == 200
    assert response.json()["source_type"] == "PDF"
    assert after == before
