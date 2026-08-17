from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import Database, get_database
from app.services import ComplaintService
from app.services.correction_processing import ComplaintCorrectionService
from app.services.documents import DocumentComplaintProcessingService
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


def get_text_processing_service(request: Request) -> TextComplaintProcessingService:
    return request.app.state.text_processing_service  # type: ignore[no-any-return]


def get_document_processing_service(
    request: Request,
) -> DocumentComplaintProcessingService:
    return request.app.state.document_processing_service  # type: ignore[no-any-return]


def get_correction_service(request: Request) -> ComplaintCorrectionService:
    return request.app.state.correction_service  # type: ignore[no-any-return]
