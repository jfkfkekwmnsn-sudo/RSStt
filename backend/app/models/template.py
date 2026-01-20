import uuid
from typing import Optional, List
from datetime import datetime  # ДОБАВЛЕНО
from sqlalchemy import String, Boolean, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base, TimestampMixin


class Template(Base, TimestampMixin):
    __tablename__ = "templates"

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
    
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    scope: Mapped[str] = mapped_column(String(50), default="global")
    scope_value: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    body: Mapped[str] = mapped_column(Text, nullable=False)
    variables_schema: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    auto_hashtags: Mapped[Optional[List[str]]] = mapped_column(JSONB, nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)

    def __repr__(self) -> str:
        return f"<Template {self.name} (scope={self.scope})>"