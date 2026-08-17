import os
from collections.abc import Mapping
from io import BytesIO
from pathlib import Path
from typing import Any

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.ai.graph import build_complaint_graph
from app.ai.providers import GroqComplaintExtractionProvider
from app.core.config import Settings
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from app.services.text_processing import TextComplaintProcessingService

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_GROQ_SMOKE") != "1" or not os.getenv("GROQ_API_KEY"),
    reason="manual PDF/Groq smoke requires RUN_GROQ_SMOKE=1 and GROQ_API_KEY",
)

SAMPLES = Path(__file__).parents[2] / "sample-data"


@pytest.mark.parametrize(
    ("filename", "expected_type", "expected_product", "expected_batch"),
    [
        (
            "fictional-fdf-complaint.pdf",
            "FDF",
            "Amoxicillin Capsules",
            "AMX-FDF-2407",
        ),
        (
            "fictional-api-complaint.pdf",
            "API",
            "Metformin Hydrochloride API",
            "MET-API-77A",
        ),
    ],
)
async def test_real_groq_pdf_smoke(
    filename: str, expected_type: str, expected_product: str, expected_batch: str
) -> None:
    settings = Settings()
    provider = GroqComplaintExtractionProvider(
        settings.groq_api_key, settings.groq_model, timeout_seconds=30
    )
    text_service = TextComplaintProcessingService(
        build_complaint_graph(provider, settings.max_text_input_length), provider
    )
    service = DocumentComplaintProcessingService(
        text_service,
        PdfTextExtractor(),
        settings.max_upload_size_mb * 1024 * 1024,
        settings.max_upload_size_mb,
        settings.max_pdf_pages,
        settings.max_pdf_text_length,
    )
    content = (SAMPLES / filename).read_bytes()
    result = await service.process(
        UploadFile(
            BytesIO(content),
            filename=filename,
            headers=Headers({"content-type": "application/pdf"}),
        )
    )
    extracted = result.extracted_complaint
    assert extracted.product_type == expected_type
    assert extracted.product_name == expected_product
    assert extracted.batch_lot_number == expected_batch


async def test_textless_pdf_fails_before_groq() -> None:
    class NeverProvider:
        model = "never"

        async def extract(self, _text: str) -> Mapping[str, Any]:
            raise AssertionError("Groq must not be called for a textless PDF")

        async def assess_complaint(self, _complaint: object) -> Mapping[str, Any]:
            raise AssertionError("Groq must not be called for a textless PDF")

    provider = NeverProvider()
    text_service = TextComplaintProcessingService(
        build_complaint_graph(provider, 20000),
        provider,
    )
    service = DocumentComplaintProcessingService(
        text_service, PdfTextExtractor(), 1_000_000, 1, 50, 20000
    )
    content = (SAMPLES / "fictional-textless-complaint.pdf").read_bytes()
    from app.core.exceptions import NoExtractableTextError

    with pytest.raises(NoExtractableTextError):
        await service.process(
            UploadFile(
                BytesIO(content),
                filename="textless.pdf",
                headers=Headers({"content-type": "application/pdf"}),
            )
        )
