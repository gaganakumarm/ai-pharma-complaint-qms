import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_complaint_service
from app.core.errors import ErrorResponse
from app.schemas import ComplaintCreate, ComplaintResponse, PaginatedComplaintResponse
from app.services.complaints import ComplaintNotFoundError, ComplaintService

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
