import uuid
from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Integer, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, TimestampMixin


class PublishJobStatus(str, Enum):
    QUEUED = "queued"
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PublishJob(Base, TimestampMixin):
    __tablename__ = "publish_jobs"

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
    
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True
    )
    target_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("publish_targets.id", ondelete="CASCADE"),
        index=True
    )
    
    status: Mapped[PublishJobStatus] = mapped_column(
        SQLEnum(PublishJobStatus),
        default=PublishJobStatus.QUEUED,
        index=True
    )
    
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True
    )
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    retries_count: Mapped[int] = mapped_column(Integer, default=0)
    max_retries: Mapped[int] = mapped_column(Integer, default=3)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # External ID (Telegram message ID)
    external_post_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Published content snapshot
    published_content: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Relationships
    article: Mapped["Article"] = relationship()
    target: Mapped["PublishTarget"] = relationship()

    def __repr__(self) -> str:
        return f"<PublishJob {self.id} ({self.status.value})>"
