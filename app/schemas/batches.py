from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    status: str
    total_items: int
    processed_items: int
    error: str | None = None
    created_at: datetime
    updated_at: datetime


class BatchItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    batch_id: int
    row_number: int
    description: str
    status: str
    result_status: str | None = None
    ktru_code: str | None = None
    candidates_count: int | None = None
    error: str | None = None
    updated_at: datetime


class BatchDetailOut(BatchOut):
    items: list[BatchItemOut] = Field(default_factory=list)


class BatchItemDetailOut(BatchItemOut):
    result: dict[str, Any] | None = None
