import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    get_complaint_service,
    get_document_processing_service,
    get_text_processing_service,
)
from app.core.errors import ErrorResponse
from app.schemas import ComplaintCreate, ComplaintResponse, PaginatedComplaintResponse
from app.schemas.extraction import (
    ProcessDocumentResponse,
    ProcessTextRequest,
    ProcessTextResponse,
)
from app.services.complaints import ComplaintNotFoundError, ComplaintService
from app.services.documents import DocumentComplaintProcessingService
from app.services.text_processing import TextComplaintProcessingService

router = APIRouter(prefix="/api/complaints", tags=["complaints"])


@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    responses={422: {"model": ErrorResponse}},
)
async def create_complaint(
    payload: ComplaintCreate,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
) -> ComplaintResponse:
    return ComplaintResponse.model_validate(await service.commit(payload))


@router.get("", response_model=PaginatedComplaintResponse)
async def list_complaints(
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> PaginatedComplaintResponse:
    return await service.list(page, page_size)


@router.post(
    "/process-text",
    response_model=ProcessTextResponse,
    responses={
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def process_complaint_text(
    payload: ProcessTextRequest,
    service: Annotated[
        TextComplaintProcessingService, Depends(get_text_processing_service)
    ],
) -> ProcessTextResponse:
    return await service.process(payload.text)


@router.post(
    "/process-document",
    response_model=ProcessDocumentResponse,
    responses={
        413: {"model": ErrorResponse},
        415: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        429: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse},
        504: {"model": ErrorResponse},
    },
)
async def process_complaint_document(
    file: Annotated[UploadFile, File(description="Text-based PDF complaint")],
    service: Annotated[
        DocumentComplaintProcessingService,
        Depends(get_document_processing_service),
    ],
) -> ProcessDocumentResponse:
    return await service.process(file)


@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}},
)
async def get_complaint(
    complaint_id: uuid.UUID,
    service: Annotated[ComplaintService, Depends(get_complaint_service)],
) -> ComplaintResponse:
    try:
        complaint = await service.get(complaint_id)
    except ComplaintNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Complaint not found") from exc
    return ComplaintResponse.model_validate(complaint)
