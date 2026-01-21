from typing import Optional, Dict, Any
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

from app.models.publish_job import PublishJobStatus


class PublishJobResponse(BaseModel):
    id: UUID
    project_id: Optional[UUID] = None
    article_id: UUID
    target_id: UUID
    status: PublishJobStatus
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    retries_count: int
    last_error: Optional[str] = None
    external_post_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PublishJobDetailResponse(PublishJobResponse):
    article_title: Optional[str] = None
    target_name: Optional[str] = None
    published_content: Optional[Dict[str, Any]] = None


class PublishJobRetryResponse(BaseModel):
    success: bool
    message: str
    job_id: UUID
