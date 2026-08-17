from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.errors import ErrorResponse
from app.infrastructure.database import Database, get_database

router = APIRouter(tags=["system"])


class StatusResponse(BaseModel):
    status: str


@router.get("/health", response_model=StatusResponse)
async def health() -> StatusResponse:
    return StatusResponse(status="ok")


@router.get(
    "/ready",
    response_model=StatusResponse,
    responses={503: {"model": ErrorResponse}},
)
async def ready(database: Annotated[Database, Depends(get_database)]) -> StatusResponse:
    try:
        async with database.engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable",
        ) from exc
    return StatusResponse(status="ready")
