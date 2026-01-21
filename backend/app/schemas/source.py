from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from datetime import datetime
from enum import Enum


class SourceType(str, Enum):
    RSS = "rss"
    SCRAPER = "scraper"
    CUSTOM = "custom"
    WEBHOOK = "webhook"


class SourceCreate(BaseModel):
    type: SourceType = SourceType.RSS
    name: str = Field(..., min_length=1, max_length=255)
    feed_url: str
    fetch_interval_minutes: int = Field(15, ge=1, le=1440)
    max_items_per_fetch: int = Field(50, ge=1, le=500)
    is_trusted: bool = False
    normalization_rules: Optional[dict] = None
    scraper_config: Optional[dict] = None


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    feed_url: Optional[str] = None
    is_active: Optional[bool] = None
    is_trusted: Optional[bool] = None
    fetch_interval_minutes: Optional[int] = None
    max_items_per_fetch: Optional[int] = None
    normalization_rules: Optional[dict] = None
    scraper_config: Optional[dict] = None


class SourceResponse(BaseModel):
    id: UUID
    type: SourceType
    name: str
    feed_url: str
    is_active: bool
    is_trusted: bool
    fetch_interval_minutes: int
    max_items_per_fetch: int
    reputation_score: float
    total_articles: int
    approved_articles: int
    rejected_articles: int
    last_fetch_at: Optional[datetime] = None
    last_error: Optional[str] = None
    consecutive_errors: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SourceListItem(BaseModel):
    id: UUID
    type: SourceType
    name: str
    is_active: bool
    is_trusted: bool
    reputation_score: float
    total_articles: int
    approved_articles: int
    last_fetch_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SourceRunResponse(BaseModel):
    id: UUID
    source_id: UUID
    status: str
    articles_count: int
    errors_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class FetchNowResponse(BaseModel):
    success: bool
    message: str
    run_id: Optional[UUID] = None
    articles_count: Optional[int] = None
