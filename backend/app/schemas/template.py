from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class TemplateVariable(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool = False
    default: Optional[str] = None


class TemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    scope: str = "global"  # global, category, target
    scope_value: Optional[str] = None
    body: str = Field(..., min_length=1)
    auto_hashtags: Optional[List[str]] = None
    is_active: bool = True
    is_default: bool = False


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    scope: Optional[str] = None
    scope_value: Optional[str] = None
    body: Optional[str] = None
    auto_hashtags: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: UUID
    project_id: Optional[UUID] = None
    variables_schema: Optional[List[TemplateVariable]] = None
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateRenderRequest(BaseModel):
    article_id: Optional[UUID] = None
    variables: Optional[Dict[str, Any]] = None


class TemplateRenderResponse(BaseModel):
    rendered_text: str
    warnings: List[str] = []
    length: int
    is_valid_for_telegram: bool