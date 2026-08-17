from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database import Database, get_database
from app.services import ComplaintService


async def get_session(
    database: Annotated[Database, Depends(get_database)],
) -> AsyncIterator[AsyncSession]:
    async for session in database.session():
        yield session


def get_complaint_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ComplaintService:
    return ComplaintService(session)
