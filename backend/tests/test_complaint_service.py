from unittest.mock import AsyncMock

import pytest

from app.domain import ComplaintStatus
from app.repositories import ComplaintRepository
from app.schemas import ComplaintCreate
from app.services import ComplaintService


def payload() -> ComplaintCreate:
    return ComplaintCreate(
        customer_name="Customer",
        product_name="Product",
        batch_lot_number="LOT-1",
        complaint_category="Quality",
        complaint_description="Description",
    )


async def test_service_sets_committed_status_and_owns_commit() -> None:
    session = AsyncMock()
    repository = AsyncMock(spec=ComplaintRepository)
    repository.create.side_effect = lambda model: model
    service = ComplaintService(session, repository)

    saved = await service.commit(payload())

    assert saved.status is ComplaintStatus.COMMITTED
    repository.create.assert_awaited_once()
    session.commit.assert_awaited_once()


async def test_service_rolls_back_failed_persistence() -> None:
    session = AsyncMock()
    repository = AsyncMock(spec=ComplaintRepository)
    repository.create.side_effect = RuntimeError("write failed")
    service = ComplaintService(session, repository)

    with pytest.raises(RuntimeError):
        await service.commit(payload())
    session.commit.assert_not_awaited()
    session.rollback.assert_awaited_once()
