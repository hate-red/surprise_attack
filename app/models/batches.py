from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


BATCH_STATUS_PENDING = 'pending'
BATCH_STATUS_PROCESSING = 'processing'
BATCH_STATUS_DONE = 'done'
BATCH_STATUS_ERROR = 'error'


class ImportBatch(Base):
    """Пакетная загрузка CSV с описаниями товаров."""

    __tablename__ = 'import_batches'

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str]
    status: Mapped[str] = mapped_column(default=BATCH_STATUS_PENDING)
    total_items: Mapped[int] = mapped_column(default=0)
    processed_items: Mapped[int] = mapped_column(default=0)
    error: Mapped[str | None] = mapped_column(nullable=True)

    items: Mapped[list['ImportBatchItem']] = relationship(
        back_populates='batch',
        cascade='all, delete-orphan',
        order_by='ImportBatchItem.row_number',
    )


class ImportBatchItem(Base):
    """Одна строка CSV: описание товара и результат его обработки."""

    __tablename__ = 'import_batch_items'

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(
        ForeignKey('import_batches.id', ondelete='CASCADE'), index=True
    )
    row_number: Mapped[int]
    description: Mapped[str]
    status: Mapped[str] = mapped_column(default=BATCH_STATUS_PENDING)
    # сценарий результата анализа: resolved / need_more_info / name_not_found ...
    result_status: Mapped[str | None] = mapped_column(nullable=True)
    ktru_code: Mapped[str | None] = mapped_column(nullable=True)
    candidates_count: Mapped[int | None] = mapped_column(nullable=True)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(nullable=True)

    batch: Mapped['ImportBatch'] = relationship(back_populates='items')
