from app.ai.graph import build_complaint_graph
from app.domain import SourceType
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from app.services.text_processing import TextComplaintProcessingService
from tests.pdf_factory import make_pdf
from tests.test_documents import upload
from tests.test_text_processing import FakeProvider, extraction


async def test_pdf_and_text_converge_on_same_graph() -> None:
    provider = FakeProvider(
        extraction(
            customer_name="Apollo Pharmacy",
            product_type="FDF",
            product_name="Amoxicillin Capsules",
            batch_lot_number="AMX-FDF-2407",
            affected_quantity="18 cartons",
            complaint_description="Capsules were discoloured.",
        )
    )
    graph = build_complaint_graph(provider, 2000)
    text_service = TextComplaintProcessingService(graph, provider)
    document_service = DocumentComplaintProcessingService(
        text_service, PdfTextExtractor(), 1_000_000, 1, 10, 2000
    )

    text_result = await text_service.process("FDF complaint")
    pdf_result = await document_service.process(
        upload(make_pdf("FDF complaint batch AMX-FDF-2407"), "fictional.pdf")
    )

    assert text_result.source_type == SourceType.TEXT
    assert pdf_result.source_type == SourceType.PDF
    assert pdf_result.extracted_complaint == text_result.extracted_complaint
    assert pdf_result.document.filename == "fictional.pdf"
    assert pdf_result.document.page_count == 1
    assert pdf_result.document.character_count > 0
    assert provider.calls == 2


async def test_incomplete_pdf_returns_nulls_and_warnings() -> None:
    provider = FakeProvider(
        extraction(product_type="API", product_name="Metformin API")
    )
    text_service = TextComplaintProcessingService(
        build_complaint_graph(provider, 2000), provider
    )
    document_service = DocumentComplaintProcessingService(
        text_service, PdfTextExtractor(), 1_000_000, 1, 10, 2000
    )
    result = await document_service.process(upload(make_pdf("Incomplete API report")))
    assert result.extracted_complaint.batch_lot_number is None
    assert "Batch number was not provided" in result.warnings
