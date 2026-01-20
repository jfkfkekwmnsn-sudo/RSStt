from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.api.deps import get_db, require_admin, require_editor
from app.models.user import User
from app.models.template import Template
from app.schemas.template import (
    TemplateCreate, TemplateUpdate, TemplateResponse,
    TemplateRenderRequest, TemplateRenderResponse
)
from app.schemas.common import MessageResponse
from app.services.template_service import TemplateService

router = APIRouter()


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    scope: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """List all templates"""
    query = select(Template)
    
    if scope:
        query = query.where(Template.scope == scope)
    if is_active is not None:
        query = query.where(Template.is_active == is_active)
    
    query = query.order_by(Template.name)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    return templates


@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: TemplateCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create new template"""
    template = Template(
        name=data.name,
        description=data.description,
        scope=data.scope,
        scope_value=data.scope_value,
        body=data.body,
        auto_hashtags=data.auto_hashtags,
        is_active=data.is_active,
        is_default=data.is_default
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template


@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: UUID,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Get template by ID"""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.patch("/{template_id}", response_model=TemplateResponse)
async def update_template(
    template_id: UUID,
    data: TemplateUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update template"""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(template, field):
            setattr(template, field, value)
    
    template.version += 1
    await db.commit()
    await db.refresh(template)
    return template


@router.delete("/{template_id}", response_model=MessageResponse)
async def delete_template(
    template_id: UUID,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Delete template"""
    query = select(Template).where(Template.id == template_id)
    result = await db.execute(query)
    template = result.scalar_one_or_none()
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    await db.delete(template)
    await db.commit()
    return MessageResponse(message="Template deleted")


@router.post("/{template_id}/render", response_model=TemplateRenderResponse)
async def render_template(
    template_id: UUID,
    data: TemplateRenderRequest,
    current_user: User = Depends(require_editor),
    db: AsyncSession = Depends(get_db)
):
    """Test render template"""
    service = TemplateService(db)
    result = await service.test_render(template_id, data.article_id)
    
    return TemplateRenderResponse(
        rendered_text=result.get("text", ""),
        warnings=result.get("warnings", []),
        length=result.get("length", 0),
        is_valid_for_telegram=result.get("is_valid_for_telegram", True)
    )