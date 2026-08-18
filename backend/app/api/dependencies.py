from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import Database, get_database
from app.repositories import ComplaintRepository
from app.services import ComplaintService
from app.services.correction_processing import ComplaintCorrectionService
from app.services.documents import DocumentComplaintProcessingService
from app.services.duplicates import DuplicateDetectionService
from app.services.text_processing import TextComplaintProcessingService


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async for session in database.session():
        yield session


def get_complaint_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintService:
    return ComplaintService(session)


def get_text_processing_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> TextComplaintProcessingService:
    base: TextComplaintProcessingService = request.app.state.text_processing_service
    return TextComplaintProcessingService(
        base.graph,
        base.provider,
        DuplicateDetectionService(ComplaintRepository(session)),
    )


def get_document_processing_service(
    request: Request,
    text_service: Annotated[
        TextComplaintProcessingService, Depends(get_text_processing_service)
    ],
) -> DocumentComplaintProcessingService:
    base: DocumentComplaintProcessingService = (
        request.app.state.document_processing_service
    )
    return DocumentComplaintProcessingService(
        text_service=text_service,
        extractor=base.extractor,
        maximum_upload_bytes=base.maximum_upload_bytes,
        maximum_upload_mb=base.maximum_upload_mb,
        maximum_pages=base.maximum_pages,
        maximum_text_length=base.maximum_text_length,
    )


def get_duplicate_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DuplicateDetectionService:
    return DuplicateDetectionService(ComplaintRepository(session))


def get_correction_service(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> ComplaintCorrectionService:
    base: ComplaintCorrectionService = request.app.state.correction_service
    return ComplaintCorrectionService(
        base.graph,
        base.provider,
        DuplicateDetectionService(ComplaintRepository(session)),
    )
