from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc

from app.models.audit_log import AuditLog, AuditAction
import structlog

logger = structlog.get_logger()


class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log(
        self,
        action: AuditAction,
        entity_type: str,
        entity_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        actor_type: str = "system",
        actor_name: Optional[str] = None,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        project_id: Optional[UUID] = None
    ):
        """Create audit log entry"""
        log_entry = AuditLog(
            project_id=project_id,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(log_entry)
        # Don't commit here - let the caller handle transaction
        
        logger.debug(
            "Audit log created",
            action=action.value,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id else None
        )
    
    async def get_logs(
        self,
        entity_type: Optional[str] = None,
        entity_id: Optional[UUID] = None,
        actor_id: Optional[UUID] = None,
        action: Optional[AuditAction] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        page: int = 1,
        per_page: int = 50
    ) -> tuple[List[AuditLog], int]:
        """Get audit logs with filters"""
        query = select(AuditLog)
        conditions = []
        
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        
        if entity_id:
            conditions.append(AuditLog.entity_id == entity_id)
        
        if actor_id:
            conditions.append(AuditLog.actor_id == actor_id)
        
        if action:
            conditions.append(AuditLog.action == action)
        
        if date_from:
            conditions.append(AuditLog.created_at >= date_from)
        
        if date_to:
            conditions.append(AuditLog.created_at <= date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count
        from sqlalchemy import func
        count_query = select(func.count(AuditLog.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get logs
        query = query.order_by(desc(AuditLog.created_at))
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        return logs, total
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: UUID,
        limit: int = 50
    ) -> List[AuditLog]:
        """Get full history for an entity"""
        query = select(AuditLog).where(
            and_(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == entity_id
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_user_activity(
        self,
        user_id: UUID,
        date_from: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """Get user activity log"""
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=7)
        
        query = select(AuditLog).where(
            and_(
                AuditLog.actor_id == user_id,
                AuditLog.created_at >= date_from
            )
        ).order_by(desc(AuditLog.created_at)).limit(limit)
        
        result = await self.db.execute(query)
        return result.scalars().all()