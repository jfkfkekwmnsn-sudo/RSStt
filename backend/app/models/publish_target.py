import uuid
from typing import Optional
from datetime import datetime  # ДОБАВЛЕНО
from sqlalchemy import String, Boolean, BigInteger, Integer, DateTime  # ДОБАВЛЕНО Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, TimestampMixin


class PublishTarget(Base, TimestampMixin):
    __tablename__ = "publish_targets"

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
    
    type: Mapped[str] = mapped_column(String(50), default="telegram_channel")
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    telegram_chat_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, unique=True)
    telegram_chat_username: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    settings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    
    total_published: Mapped[int] = mapped_column(Integer, default=0)
    last_published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )

    def __repr__(self) -> str:
        return f"<PublishTarget {self.name} ({self.type})>"