import uuid
import secrets
from enum import Enum
from typing import Optional, List
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Float, Text, ForeignKey, Enum as SQLEnum, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY

from app.models.base import Base, TimestampMixin


class ArticleStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    FAILED = "failed"
    DUPLICATE = "duplicate"
    NEEDS_REVIEW = "needs_review"


def generate_token() -> str:
    return secrets.token_urlsafe(12)


class Article(Base, TimestampMixin):
    __tablename__ = "articles"

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
    
    token: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        index=True,
        default=generate_token
    )
    
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    url: Mapped[str] = mapped_column(Text, nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), index=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_raw: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    content_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    pub_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    
    images: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    main_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    quality_score: Mapped[float] = mapped_column(Float, default=0.5)
    quality_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    priority_score: Mapped[int] = mapped_column(Integer, default=50, index=True)
    priority_factors: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    status: Mapped[ArticleStatus] = mapped_column(
        SQLEnum(ArticleStatus),
        default=ArticleStatus.PENDING,
        index=True
    )
    
    batch_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batches.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    ai_used: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_metadata: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    moderator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_target_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("publish_targets.id", ondelete="SET NULL"),
        nullable=True
    )
    published_external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    published_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    similar_to_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="SET NULL"),
        nullable=True
    )
    similarity_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Relationships - используем строковые ссылки для избежания циклических импортов
    source: Mapped[Optional["Source"]] = relationship("Source", back_populates="articles")
    batch: Mapped[Optional["Batch"]] = relationship("Batch", back_populates="articles")
    moderator: Mapped[Optional["User"]] = relationship("User")
    versions: Mapped[List["ArticleVersion"]] = relationship("ArticleVersion", back_populates="article", lazy="dynamic")
    
    __table_args__ = (
        Index("ix_articles_status_priority", "status", "priority_score"),
        Index("ix_articles_source_status", "source_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Article {self.title[:50]}... ({self.status.value})>"


class ArticleVersion(Base):
    __tablename__ = "article_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    article_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("articles.id", ondelete="CASCADE"),
        index=True
    )
    
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content_clean: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True)
    main_image_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    created_by_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    article: Mapped["Article"] = relationship("Article", back_populates="versions")