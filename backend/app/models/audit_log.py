import uuid
from enum import Enum
from typing import Optional
from datetime import datetime
from sqlalchemy import String, Text, Enum as SQLEnum, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.models.base import Base


class AuditAction(str, Enum):
    # Article actions
    ARTICLE_CREATED = "article_created"
    ARTICLE_APPROVED = "article_approved"
    ARTICLE_REJECTED = "article_rejected"
    ARTICLE_EDITED = "article_edited"
    ARTICLE_SCHEDULED = "article_scheduled"
    ARTICLE_PUBLISHED = "article_published"
    ARTICLE_FAILED = "article_failed"
    
    # Source actions
    SOURCE_CREATED = "source_created"
    SOURCE_UPDATED = "source_updated"
    SOURCE_DELETED = "source_deleted"
    SOURCE_FETCH = "source_fetch"
    
    # Rule actions
    RULE_CREATED = "rule_created"
    RULE_UPDATED = "rule_updated"
    RULE_DELETED = "rule_deleted"
    RULE_APPLIED = "rule_applied"
    
    # Template actions
    TEMPLATE_CREATED = "template_created"
    TEMPLATE_UPDATED = "template_updated"
    TEMPLATE_DELETED = "template_deleted"
    
    # User actions
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    
    # System actions
    BATCH_CREATED = "batch_created"
    BATCH_SENT = "batch_sent"
    AI_PROCESSED = "ai_processed"


class AuditLog(Base):
    __tablename__ = "audit_logs"

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
    
    # Actor
    actor_type: Mapped[str] = mapped_column(String(50), nullable=False)  # user, system, telegram
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    actor_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Action
    action: Mapped[AuditAction] = mapped_column(SQLEnum(AuditAction), nullable=False, index=True)
    
    # Entity
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # article, source, rule, etc.
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Changes
    before_state: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    
    # Additional context
    metadata_info: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.action.value} on {self.entity_type}>"
