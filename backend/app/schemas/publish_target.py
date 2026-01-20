from typing import Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime


class PublishTargetSettings(BaseModel):
    disable_web_page_preview: bool = False
    parse_mode: str = "HTML"
    min_interval_seconds: int = 60
    default_template_id: Optional[UUID] = None


class PublishTargetBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = "telegram_channel"
    telegram_chat_id: Optional[int] = None
    telegram_chat_username: Optional[str] = None
    settings: Optional[PublishTargetSettings] = None
    is_active: bool = True


class PublishTargetCreate(PublishTargetBase):
    pass


class PublishTargetUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    telegram_chat_id: Optional[int] = None
    telegram_chat_username: Optional[str] = None
    settings: Optional[PublishTargetSettings] = None
    is_active: Optional[bool] = None


class PublishTargetResponse(PublishTargetBase):
    id: UUID
    project_id: Optional[UUID] = None
    total_published: int
    last_published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True