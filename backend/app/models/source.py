import uuid
from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, TimestampMixin


class SourceType(str, Enum):
    RSS = "rss"
    SCRAPER = "scraper"
    CUSTOM = "custom"
    WEBHOOK = "webhook"


class Source(Base, TimestampMixin):
    __tablename__ = "sources"

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
    
    type: Mapped[SourceType] = mapped_column(
        SQLEnum(SourceType),
        default=SourceType.RSS
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    feed_url: Mapped[str] = mapped_column(Text, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    
    fetch_interval_minutes: Mapped[int] = mapped_column(Integer, default=15)
    max_items_per_fetch: Mapped[int] = mapped_column(Integer, default=50)
    
    # Normalization rules (remove utm, ref params etc.)
    normalization_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Scraper config (selectors, etc.) - for type=scraper
    scraper_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Reputation and stats
    reputation_score: Mapped[float] = mapped_column(Float, default=0.5)
    total_articles: Mapped[int] = mapped_column(Integer, default=0)
    approved_articles: Mapped[int] = mapped_column(Integer, default=0)
    rejected_articles: Mapped[int] = mapped_column(Integer, default=0)
    
    last_fetch_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    consecutive_errors: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    runs: Mapped[list["SourceRun"]] = relationship(back_populates="source", lazy="dynamic")
    articles: Mapped[list["Article"]] = relationship(back_populates="source", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Source {self.name} ({self.type.value})>"


class SourceRun(Base):
    __tablename__ = "source_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="CASCADE"),
        index=True
    )
    
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    status: Mapped[str] = mapped_column(String(50), default="running")  # running, success, failed
    articles_found: Mapped[int] = mapped_column(Integer, default=0)
    articles_new: Mapped[int] = mapped_column(Integer, default=0)
    articles_duplicate: Mapped[int] = mapped_column(Integer, default=0)
    
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    source: Mapped["Source"] = relationship(back_populates="runs")