import math
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain import ComplaintStatus
from app.infrastructure.database.models import ComplaintModel
from app.repositories import ComplaintRepository
from app.schemas import ComplaintCreate, PaginatedComplaintResponse


class ComplaintNotFoundError(Exception):
    pass


class ComplaintService:
    def __init__(
        self, session: AsyncSession, repository: ComplaintRepository | None = None
    ) -> None:
        self.session = session
        self.repository = repository or ComplaintRepository(session)

    async def commit(self, payload: ComplaintCreate) -> ComplaintModel:
        complaint = ComplaintModel(
            **payload.model_dump(), status=ComplaintStatus.COMMITTED
        )
        try:
            saved = await self.repository.create(complaint)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return saved

    async def get(self, complaint_id: uuid.UUID) -> ComplaintModel:
        complaint = await self.repository.get_by_id(complaint_id)
        if complaint is None:
            raise ComplaintNotFoundError
        return complaint

    async def list(self, page: int, page_size: int) -> PaginatedComplaintResponse:
        records, total = await self.repository.list(page, page_size)
        return PaginatedComplaintResponse(
            items=records,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=math.ceil(total / page_size) if total else 0,
        )
