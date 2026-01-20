from typing import Optional, List
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.models.batch import BatchStatus, BatchStrategy


class BatchCreate(BaseModel):
    strategy: BatchStrategy = BatchStrategy.MIXED
    max_size: int = Field(5, ge=1, le=20)
    min_quality: Optional[float] = None
    category: Optional[str] = None
    source_id: Optional[UUID] = None


class BatchResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    strategy: BatchStrategy
    status: BatchStatus
    articles_count: int
    avg_quality: float
    total_priority: int
    telegram_message_ids: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BatchDetailResponse(BatchResponse):
    articles: List["ArticleListResponse"] = []


class BatchActionResponse(BaseModel):
    success: bool
    message: str
    approved_count: int = 0
    rejected_count: int = 0