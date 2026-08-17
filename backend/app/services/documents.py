from dataclasses import dataclass
from pathlib import Path

import pymupdf
from fastapi import UploadFile

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
from app.domain import SourceType
from app.schemas.extraction import (
    DocumentMetadata,
    ProcessDocumentResponse,
)
from app.services.text_processing import TextComplaintProcessingService

PDF_CONTENT_TYPES = {"application/pdf", "application/x-pdf"}
READ_CHUNK_SIZE = 64 * 1024


@dataclass(frozen=True)
class ExtractedPdf:
    text: str
    page_count: int


class PdfTextExtractor:
    def extract(self, content: bytes, maximum_pages: int) -> ExtractedPdf:
        try:
            with pymupdf.open(  # type: ignore[no-untyped-call]
                stream=content, filetype="pdf"
            ) as document:
                if document.needs_pass:
                    raise EncryptedPdfError
                if document.page_count > maximum_pages:
                    raise ExcessivePdfPagesError(maximum_pages)
                page_text = [page.get_text("text") for page in document]
                return ExtractedPdf("\n".join(page_text), document.page_count)
        except (EncryptedPdfError, ExcessivePdfPagesError):
            raise
        except Exception as exc:
            raise UnreadablePdfError from exc


class DocumentComplaintProcessingService:
    def __init__(
        self,
        text_service: TextComplaintProcessingService,
        extractor: PdfTextExtractor,
        maximum_upload_bytes: int,
        maximum_upload_mb: int,
        maximum_pages: int,
        maximum_text_length: int,
    ) -> None:
        self.text_service = text_service
        self.extractor = extractor
        self.maximum_upload_bytes = maximum_upload_bytes
        self.maximum_upload_mb = maximum_upload_mb
        self.maximum_pages = maximum_pages
        self.maximum_text_length = maximum_text_length

    async def process(self, upload: UploadFile) -> ProcessDocumentResponse:
        try:
            filename = (upload.filename or "").strip()
            if not filename:
                raise MissingDocumentError
            safe_filename = Path(filename.replace("\\", "/")).name
            if Path(safe_filename).suffix.lower() != ".pdf":
                raise UnsupportedDocumentTypeError
            if upload.content_type not in PDF_CONTENT_TYPES:
                raise UnsupportedDocumentTypeError

            content = await self._read_bounded(upload)
            if not content:
                raise EmptyDocumentError
            if not content.startswith(b"%PDF-"):
                raise InvalidPdfSignatureError

            extracted = self.extractor.extract(content, self.maximum_pages)
            normalized_text = extracted.text.strip()
            if not normalized_text:
                raise NoExtractableTextError
            if len(normalized_text) > self.maximum_text_length:
                raise ExtractedTextTooLargeError(self.maximum_text_length)

            result = await self.text_service.process(normalized_text, SourceType.PDF)
            return ProcessDocumentResponse(
                document=DocumentMetadata(
                    filename=safe_filename,
                    content_type="application/pdf",
                    page_count=extracted.page_count,
                    character_count=result.input_length,
                ),
                extracted_complaint=result.extracted_complaint,
                quality_assessment=result.quality_assessment,
                warnings=result.warnings,
                assistant_message=result.assistant_message,
                model=result.model,
            )
        finally:
            await upload.close()

    async def _read_bounded(self, upload: UploadFile) -> bytes:
        chunks: list[bytes] = []
        size = 0
        while chunk := await upload.read(READ_CHUNK_SIZE):
            size += len(chunk)
            if size > self.maximum_upload_bytes:
                raise DocumentTooLargeError(self.maximum_upload_mb)
            chunks.append(chunk)
        return b"".join(chunks)
