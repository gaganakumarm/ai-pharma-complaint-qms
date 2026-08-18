from collections.abc import AsyncIterator
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

from app.ai.correction_graph import build_correction_graph
from app.api.dependencies import get_correction_service
from app.core.config import Settings
from app.main import create_app
from app.schemas.correction import CorrectableComplaint
from app.services.correction_processing import ComplaintCorrectionService

ASSESSMENT = {
    "complaint_category": "Packaging",
    "structured_complaint_description": "Carton issue.",
    "suggested_severity": "MINOR",
    "severity_rationale": "Cosmetic report.",
    "initial_risk_assessment": "Potential quality impact requires review.",
    "suggested_next_action": "QA should review the complaint.",
    "assessment_status": "COMPLETE",
    "information_gaps": [],
    "human_review_required": True,
}


class Provider:
    model = "fake-model"

    async def extract_correction(
        self, current: CorrectableComplaint, instruction: str
    ) -> dict[str, Any]:
        return {
            "updates": [
                {"field": "batch_lot_number", "value": "BMX240602"},
                {"field": "affected_quantity", "value": "48 capsules"},
            ],
            "clarification_required": False,
            "clarification_question": None,
        }

    async def assess_complaint(self, complaint: CorrectableComplaint) -> dict[str, Any]:
        return ASSESSMENT


@pytest.fixture
async def correction_client() -> AsyncIterator[AsyncClient]:
    provider = Provider()
    service = ComplaintCorrectionService(
        build_correction_graph(provider, 2000), provider
    )
    app = create_app(Settings(database_url="sqlite+aiosqlite:///:memory:"))
    app.dependency_overrides[get_correction_service] = lambda: service
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client


async def test_correction_endpoint_changes_only_requested_fields(
    correction_client: AsyncClient,
) -> None:
    current = dict.fromkeys(CorrectableComplaint.model_fields)
    current.update(
        customer_name="Apollo", product_type="FDF", batch_lot_number="AMX240602"
    )
    response = await correction_client.post(
        "/api/complaints/correct",
        json={
            "current_complaint": current,
            "instruction": "Batch is BMX240602 and quantity is 48 capsules",
            "current_quality_assessment": ASSESSMENT,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["changed_fields"] == ["batch_lot_number", "affected_quantity"]
    assert body["updated_complaint"]["customer_name"] == "Apollo"
    assert body["status"] == "APPLIED"


async def test_blank_instruction_uses_standard_error_envelope(
    correction_client: AsyncClient,
) -> None:
    current = dict.fromkeys(CorrectableComplaint.model_fields)
    response = await correction_client.post(
        "/api/complaints/correct",
        json={
            "current_complaint": current,
            "instruction": "   ",
            "current_quality_assessment": ASSESSMENT,
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_COMPLAINT_TEXT"
