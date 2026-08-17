import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ComplaintModel


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, complaint: ComplaintModel) -> ComplaintModel:
        self.session.add(complaint)
        await self.session.flush()
        await self.session.refresh(complaint)
        return complaint

    async def get_by_id(self, complaint_id: uuid.UUID) -> ComplaintModel | None:
        return await self.session.get(ComplaintModel, complaint_id)

    async def list(self, page: int, page_size: int) -> tuple[list[ComplaintModel], int]:
        offset = (page - 1) * page_size
        records = await self.session.scalars(
            select(ComplaintModel)
            .order_by(ComplaintModel.created_at.desc(), ComplaintModel.id.desc())
            .offset(offset)
            .limit(page_size)
        )
        total = await self.session.scalar(select(func.count(ComplaintModel.id)))
        return list(records), total or 0
