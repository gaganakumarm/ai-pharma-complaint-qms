from io import BytesIO

import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.core.exceptions import (
    DocumentTooLargeError,
    EmptyDocumentError,
    EncryptedPdfError,
    ExcessivePdfPagesError,
    ExtractedTextTooLargeError,
    InvalidPdfSignatureError,
    MissingDocumentError,
    NoExtractableTextError,
    UnreadablePdfError,
    UnsupportedDocumentTypeError,
)
from app.services.documents import DocumentComplaintProcessingService, PdfTextExtractor
from tests.pdf_factory import make_encrypted_pdf, make_pdf


class RecordingTextService:
    def __init__(self) -> None:
        self.calls: list[tuple[str, object]] = []

    async def process(self, text: str, source_type: object) -> object:
        self.calls.append((text, source_type))
        raise RuntimeError("stop after extraction")


def upload(
    content: bytes,
    filename: str | None = "complaint.pdf",
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        BytesIO(content),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def service(**overrides: int) -> DocumentComplaintProcessingService:
    return DocumentComplaintProcessingService(
        text_service=RecordingTextService(),  # type: ignore[arg-type]
        extractor=PdfTextExtractor(),
        maximum_upload_bytes=overrides.get("maximum_upload_bytes", 1_000_000),
        maximum_upload_mb=1,
        maximum_pages=overrides.get("maximum_pages", 10),
        maximum_text_length=overrides.get("maximum_text_length", 1000),
    )


def test_pdf_extractor_preserves_page_order_and_batch_identifier() -> None:
    result = PdfTextExtractor().extract(make_pdf("First AMX-42/A", "Second 25 kg"), 10)
    assert result.page_count == 2
    assert result.text.index("First AMX-42/A") < result.text.index("Second 25 kg")


def test_pdf_extractor_rejects_corrupt_encrypted_and_excessive_pages() -> None:
    with pytest.raises(UnreadablePdfError):
        PdfTextExtractor().extract(b"%PDF-corrupt", 10)
    with pytest.raises(EncryptedPdfError):
        PdfTextExtractor().extract(make_encrypted_pdf(), 10)
    with pytest.raises(ExcessivePdfPagesError):
        PdfTextExtractor().extract(make_pdf("one", "two"), 1)


@pytest.mark.parametrize(
    ("candidate", "error"),
    [
        (upload(make_pdf("text"), filename=""), MissingDocumentError),
        (
            upload(make_pdf("text"), filename="complaint.txt"),
            UnsupportedDocumentTypeError,
        ),
        (
            upload(make_pdf("text"), content_type="text/plain"),
            UnsupportedDocumentTypeError,
        ),
        (upload(b"not a PDF"), InvalidPdfSignatureError),
        (upload(b""), EmptyDocumentError),
    ],
)
async def test_document_metadata_validation(
    candidate: UploadFile, error: type[Exception]
) -> None:
    with pytest.raises(error):
        await service().process(candidate)
    assert candidate.file.closed


async def test_uppercase_pdf_extension_is_accepted() -> None:
    candidate = upload(make_pdf("Batch ABC-123"), filename="COMPLAINT.PDF")
    with pytest.raises(RuntimeError, match="stop after extraction"):
        await service().process(candidate)
    assert candidate.file.closed


async def test_oversized_upload_is_stopped_and_closed() -> None:
    candidate = upload(b"%PDF-" + b"x" * 100)
    with pytest.raises(DocumentTooLargeError):
        await service(maximum_upload_bytes=20).process(candidate)
    assert candidate.file.closed


async def test_textless_and_excessive_extracted_text_are_rejected() -> None:
    with pytest.raises(NoExtractableTextError):
        await service().process(upload(make_pdf("")))
    with pytest.raises(ExtractedTextTooLargeError):
        await service(maximum_text_length=5).process(
            upload(make_pdf("long complaint text"))
        )
