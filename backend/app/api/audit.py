from typing import Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.models.audit_log import AuditAction
from app.services.audit_service import AuditService
from app.schemas.common import PaginatedResponse

router = APIRouter()


@router.get("")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    entity_type: Optional[str] = None,
    entity_id: Optional[UUID] = None,
    actor_id: Optional[UUID] = None,
    action: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get audit logs with filters"""
    service = AuditService(db)
    
    action_enum = None
    if action:
        try:
            action_enum = AuditAction(action)
        except ValueError:
            pass
    
    logs, total = await service.get_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        action=action_enum,
        date_from=date_from,
        date_to=date_to,
        page=page,
        per_page=per_page
    )
    
    return PaginatedResponse.create(
        items=[{
            "id": str(log.id),
            "action": log.action.value,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "actor_type": log.actor_type,
            "actor_id": str(log.actor_id) if log.actor_id else None,
            "actor_name": log.actor_name,
            "before_state": log.before_state,
            "after_state": log.after_state,
            "metadata": log.metadata,
            "created_at": log.created_at.isoformat()
        } for log in logs],
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def get_entity_history(
    entity_type: str,
    entity_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get full history for an entity"""
    service = AuditService(db)
    logs = await service.get_entity_history(entity_type, entity_id, limit)
    
    return [{
        "id": str(log.id),
        "action": log.action.value,
        "actor_type": log.actor_type,
        "actor_id": str(log.actor_id) if log.actor_id else None,
        "actor_name": log.actor_name,
        "before_state": log.before_state,
        "after_state": log.after_state,
        "created_at": log.created_at.isoformat()
    } for log in logs]