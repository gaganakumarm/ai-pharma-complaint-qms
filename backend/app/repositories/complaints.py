import builtins
import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.models import ComplaintModel
from app.schemas.enhancements import DuplicateCheckRequest
from app.services.duplicates import normalize


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

    async def find_duplicate_candidates(
        self, request: DuplicateCheckRequest, limit: int
    ) -> builtins.list[ComplaintModel]:
        predicates = []
        if request.product_name:
            predicates.append(
                func.lower(ComplaintModel.product_name) == request.product_name.lower()
            )
        if request.batch_lot_number:
            dialect = self.session.bind.dialect.name if self.session.bind else ""
            if dialect == "postgresql":
                predicates.append(
                    func.regexp_replace(
                        func.lower(ComplaintModel.batch_lot_number),
                        "[^a-z0-9]",
                        "",
                        "g",
                    )
                    == normalize(request.batch_lot_number)
                )
            else:
                predicates.append(
                    func.lower(ComplaintModel.batch_lot_number)
                    == request.batch_lot_number.lower()
                )
        query = select(ComplaintModel)
        if predicates:
            query = query.where(or_(*predicates))
        if request.current_complaint_id:
            query = query.where(ComplaintModel.id != request.current_complaint_id)
        query = query.order_by(
            ComplaintModel.created_at.desc(), ComplaintModel.id.desc()
        ).limit(limit)
        records = list(await self.session.scalars(query))
        if len(records) >= limit or not predicates:
            return records
        fallback = select(ComplaintModel)
        if request.current_complaint_id:
            fallback = fallback.where(ComplaintModel.id != request.current_complaint_id)
        if records:
            fallback = fallback.where(
                ComplaintModel.id.not_in([record.id for record in records])
            )
        fallback = fallback.order_by(
            ComplaintModel.created_at.desc(), ComplaintModel.id.desc()
        ).limit(limit - len(records))
        return [*records, *list(await self.session.scalars(fallback))]
