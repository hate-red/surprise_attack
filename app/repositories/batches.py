from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.orm import selectinload

from app.database import async_session_maker
from app.models.batches import (
    BATCH_STATUS_DONE,
    BATCH_STATUS_PENDING,
    BATCH_STATUS_PROCESSING,
    ImportBatch,
    ImportBatchItem,
)
from app.repositories.base import BaseRepository


class ImportBatchRepository(BaseRepository):
    model = ImportBatch

    @classmethod
    async def create_with_items(cls, filename: str, descriptions: list[str]) -> ImportBatch:
        async with async_session_maker() as session:
            async with session.begin():
                batch = ImportBatch(
                    filename=filename,
                    status=BATCH_STATUS_PENDING,
                    total_items=len(descriptions),
                    processed_items=0,
                )
                batch.items = [
                    ImportBatchItem(row_number=i, description=text, status=BATCH_STATUS_PENDING)
                    for i, text in enumerate(descriptions, 1)
                ]
                session.add(batch)
            await session.refresh(batch)
            return batch

    @classmethod
    async def list_recent(cls, limit: int = 20) -> list[ImportBatch]:
        async with async_session_maker() as session:
            stmt = select(ImportBatch).order_by(ImportBatch.id.desc()).limit(limit)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def get_with_items(cls, batch_id: int) -> ImportBatch | None:
        async with async_session_maker() as session:
            stmt = (
                select(ImportBatch)
                .where(ImportBatch.id == batch_id)
                .options(selectinload(ImportBatch.items))
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def get_item(cls, batch_id: int, item_id: int) -> ImportBatchItem | None:
        async with async_session_maker() as session:
            stmt = select(ImportBatchItem).where(
                ImportBatchItem.batch_id == batch_id, ImportBatchItem.id == item_id
            )
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    @classmethod
    async def unfinished_ids(cls) -> list[int]:
        async with async_session_maker() as session:
            stmt = select(ImportBatch.id).where(
                ImportBatch.status.in_([BATCH_STATUS_PENDING, BATCH_STATUS_PROCESSING])
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def pending_item_ids(cls, batch_id: int) -> list[int]:
        async with async_session_maker() as session:
            stmt = (
                select(ImportBatchItem.id)
                .where(
                    ImportBatchItem.batch_id == batch_id,
                    ImportBatchItem.status.in_([BATCH_STATUS_PENDING, BATCH_STATUS_PROCESSING]),
                )
                .order_by(ImportBatchItem.row_number)
            )
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @classmethod
    async def set_batch_status(cls, batch_id: int, status: str, error: str | None = None) -> None:
        async with async_session_maker() as session:
            async with session.begin():
                await session.execute(
                    update(ImportBatch)
                    .where(ImportBatch.id == batch_id)
                    .values(status=status, error=error, updated_at=func.now())
                )

    @classmethod
    async def set_item(cls, item_id: int, **values: Any) -> None:
        async with async_session_maker() as session:
            async with session.begin():
                await session.execute(
                    update(ImportBatchItem)
                    .where(ImportBatchItem.id == item_id)
                    .values(**values, updated_at=func.now())
                )

    @classmethod
    async def refresh_progress(cls, batch_id: int) -> None:
        """processed_items = число строк в конечном статусе (done / error)."""
        async with async_session_maker() as session:
            async with session.begin():
                processed = (
                    select(func.count())
                    .select_from(ImportBatchItem)
                    .where(
                        ImportBatchItem.batch_id == batch_id,
                        ImportBatchItem.status.notin_([BATCH_STATUS_PENDING, BATCH_STATUS_PROCESSING]),
                    )
                    .scalar_subquery()
                )
                await session.execute(
                    update(ImportBatch)
                    .where(ImportBatch.id == batch_id)
                    .values(processed_items=processed, updated_at=func.now())
                )

    @classmethod
    async def get_item_description(cls, item_id: int) -> str | None:
        async with async_session_maker() as session:
            result = await session.execute(
                select(ImportBatchItem.description).where(ImportBatchItem.id == item_id)
            )
            return result.scalar_one_or_none()


__all__ = ['ImportBatchRepository', 'BATCH_STATUS_DONE']
