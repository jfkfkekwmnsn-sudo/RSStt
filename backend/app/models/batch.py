import uuid
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, TimestampMixin


class BatchStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    PARTIAL = "partial"  # Some approved, some pending
    COMPLETED = "completed"


class BatchStrategy(str, Enum):
    MIXED = "mixed"
    BY_CATEGORY = "by_category"
    BY_SOURCE = "by_source"
    BY_PRIORITY = "by_priority"


class Batch(Base, TimestampMixin):
    __tablename__ = "batches"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    project_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True
    )
    
    strategy: Mapped[BatchStrategy] = mapped_column(
        SQLEnum(BatchStrategy),
        default=BatchStrategy.MIXED
    )
    status: Mapped[BatchStatus] = mapped_column(
        SQLEnum(BatchStatus),
        default=BatchStatus.PENDING,
        index=True
    )
    
    articles_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_quality: Mapped[float] = mapped_column(Float, default=0.0)
    total_priority: Mapped[int] = mapped_column(Integer, default=0)
    
    # Telegram message IDs for this batch
    telegram_message_ids: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    articles: Mapped[list["Article"]] = relationship(back_populates="batch", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Batch {self.id} ({self.status.value}, {self.articles_count} articles)>"