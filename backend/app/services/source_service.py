from typing import Optional, List, Tuple, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models.source import Source, SourceRun, SourceType
from app.schemas.source import SourceCreate, SourceUpdate, SourceListItem
from app.services.audit_service import AuditService
from app.models.audit_log import AuditAction
import structlog

logger = structlog.get_logger()


class SourceService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.audit = AuditService(db)
    
    async def get_source(self, source_id: UUID) -> Optional[Source]:
        """Get source by ID"""
        query = select(Source).where(Source.id == source_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_sources(
        self,
        page: int = 1,
        per_page: int = 20,
        is_active: Optional[bool] = None,
        type: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[SourceListItem], int]:
        """List sources with filters"""
        query = select(Source)
        conditions = []
        
        if is_active is not None:
            conditions.append(Source.is_active == is_active)
        
        if type:
            conditions.append(Source.type == SourceType(type))
        
        if search:
            conditions.append(Source.name.ilike(f"%{search}%"))
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Count
        count_query = select(func.count(Source.id))
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Get sources
        query = query.order_by(Source.created_at.desc())
        query = query.offset((page - 1) * per_page).limit(per_page)
        
        result = await self.db.execute(query)
        sources = result.scalars().all()
        
        # Convert to list items
        items = [
            SourceListItem(
                id=s.id,
                name=s.name,
                type=s.type,
                is_active=s.is_active,
                is_trusted=s.is_trusted,
                reputation_score=s.reputation_score,
                total_articles=s.total_articles,
                last_fetch_at=s.last_fetch_at,
                consecutive_errors=s.consecutive_errors,
                created_at=s.created_at
            )
            for s in sources
        ]
        
        return items, total
    
    async def create_source(self, data: SourceCreate, user_id: UUID) -> Source:
        """Create new source"""
        source = Source(
            name=data.name,
            feed_url=data.feed_url,
            type=data.type or SourceType.RSS,
            is_active=data.is_active if data.is_active is not None else True,
            is_trusted=data.is_trusted if data.is_trusted is not None else False,
            fetch_interval_minutes=data.fetch_interval_minutes or 15,
            max_items_per_fetch=data.max_items_per_fetch or 50,
            normalization_rules=data.normalization_rules.model_dump() if data.normalization_rules else None,
        )
        
        self.db.add(source)
        await self.db.commit()
        await self.db.refresh(source)
        
        await self.audit.log(
            action=AuditAction.SOURCE_CREATED,
            entity_type="source",
            entity_id=source.id,
            actor_id=user_id,
            actor_type="user",
            after_state={"name": source.name, "feed_url": source.feed_url}
        )
        
        logger.info("Source created", source_id=str(source.id), name=source.name)
        
        return source
    
    async def update_source(
        self, 
        source_id: UUID, 
        data: SourceUpdate, 
        user_id: UUID
    ) -> Optional[Source]:
        """Update source"""
        source = await self.get_source(source_id)
        if not source:
            return None
        
        before_state = {
            "name": source.name,
            "is_active": source.is_active,
            "is_trusted": source.is_trusted
        }
        
        update_data = data.model_dump(exclude_unset=True)
        
        # Handle nested normalization_rules
        if "normalization_rules" in update_data and update_data["normalization_rules"]:
            update_data["normalization_rules"] = update_data["normalization_rules"].model_dump() \
                if hasattr(update_data["normalization_rules"], "model_dump") \
                else update_data["normalization_rules"]
        
        for field, value in update_data.items():
            if hasattr(source, field) and value is not None:
                setattr(source, field, value)
        
        await self.db.commit()
        await self.db.refresh(source)
        
        await self.audit.log(
            action=AuditAction.SOURCE_UPDATED,
            entity_type="source",
            entity_id=source.id,
            actor_id=user_id,
            actor_type="user",
            before_state=before_state,
            after_state=update_data
        )
        
        return source
    
    async def delete_source(self, source_id: UUID, user_id: UUID) -> bool:
        """Delete (deactivate) source"""
        source = await self.get_source(source_id)
        if not source:
            return False
        
        source.is_active = False
        await self.db.commit()
        
        await self.audit.log(
            action=AuditAction.SOURCE_DELETED,
            entity_type="source",
            entity_id=source.id,
            actor_id=user_id,
            actor_type="user"
        )
        
        return True
    
    async def fetch_now(self, source_id: UUID, user_id: UUID) -> Dict[str, Any]:
        """Trigger immediate fetch for source"""
        source = await self.get_source(source_id)
        if not source:
            return {"success": False, "message": "Source not found"}
        
        if not source.is_active:
            return {"success": False, "message": "Source is not active"}
        
        # Queue fetch task
        from app.workers.tasks import fetch_source_task
        fetch_source_task.delay(str(source_id))
        
        await self.audit.log(
            action=AuditAction.SOURCE_FETCH,
            entity_type="source",
            entity_id=source.id,
            actor_id=user_id,
            actor_type="user",
            metadata={"triggered": "manual"}
        )
        
        return {"success": True, "message": "Fetch queued"}
    
    async def get_runs(self, source_id: UUID, limit: int = 20) -> List[SourceRun]:
        """Get source fetch history"""
        query = select(SourceRun).where(
            SourceRun.source_id == source_id
        ).order_by(SourceRun.started_at.desc()).limit(limit)
        
        result = await self.db.execute(query)
        return list(result.scalars().all())