from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_admin
from app.models.user import User
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse, RuleDryRunRequest, RuleDryRunResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.rules_service import RulesService

router = APIRouter()


@router.get("", response_model=List[RuleResponse])
async def list_rules(
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all rules"""
    query = select(Rule)
    if is_active is not None:
        query = query.where(Rule.is_active == is_active)
    query = query.order_by(Rule.priority)
    
    result = await db.execute(query)
    rules = result.scalars().all()
    return rules


@router.post("", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: RuleCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new rule"""
    rule = Rule(
        name=data.name,
        description=data.description,
        is_active=data.is_active,
        priority=data.priority,
        conditions={"conditions": [c.model_dump() for c in data.conditions], "match": "all"},
        actions={"actions": [a.model_dump() for a in data.actions]}
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get rule by ID"""
    query = select(Rule).where(Rule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    return rule


@router.patch("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: UUID,
    data: RuleUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update rule"""
    query = select(Rule).where(Rule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    update_data = data.model_dump(exclude_unset=True)
    
    if "conditions" in update_data:
        update_data["conditions"] = {
            "conditions": [c.model_dump() for c in data.conditions],
            "match": "all"
        }
    
    if "actions" in update_data:
        update_data["actions"] = {"actions": [a.model_dump() for a in data.actions]}
    
    for field, value in update_data.items():
        if hasattr(rule, field):
            setattr(rule, field, value)
    
    rule.version += 1
    await db.commit()
    await db.refresh(rule)
    return rule


@router.delete("/{rule_id}", response_model=MessageResponse)
async def delete_rule(
    rule_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete rule"""
    query = select(Rule).where(Rule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    await db.delete(rule)
    await db.commit()
    return MessageResponse(message="Rule deleted")


@router.post("/{rule_id}/dry-run", response_model=RuleDryRunResponse)
async def dry_run_rule(
    rule_id: UUID,
    data: RuleDryRunRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Test rule against recent articles"""
    query = select(Rule).where(Rule.id == rule_id)
    result = await db.execute(query)
    rule = result.scalar_one_or_none()
    
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    
    service = RulesService(db)
    results = await service.dry_run(rule_id, data.limit)
    
    return RuleDryRunResponse(
        rule_id=rule.id,
        rule_name=rule.name,
        total_tested=len(results),
        matched_count=sum(1 for r in results if r["matched"]),
        results=results
    )
