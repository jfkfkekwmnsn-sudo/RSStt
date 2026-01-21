from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

from app.models.article import ArticleStatus


class ImageInfo(BaseModel):
    url: str
    alt: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    is_main: bool = False


class QualityFactors(BaseModel):
    has_image: float = 0.0
    text_length: float = 0.0
    freshness: float = 0.0
    source_trust: float = 0.0
    uniqueness: float = 0.0


class PriorityFactors(BaseModel):
    category_weight: int = 0
    quality_bonus: int = 0
    freshness_bonus: int = 0
    source_bonus: int = 0
    media_bonus: int = 0


class ArticleBase(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    content_clean: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    main_image_url: Optional[str] = None


class ArticleCreate(ArticleBase):
    url: str
    source_id: Optional[UUID] = None
    content_raw: Optional[str] = None
    pub_date: Optional[datetime] = None


class ArticleUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    content_clean: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    main_image_url: Optional[str] = None


class ArticleResponse(ArticleBase):
    id: UUID
    token: str
    project_id: Optional[UUID] = None
    source_id: Optional[UUID] = None
    url: str
    pub_date: Optional[datetime] = None
    images: Optional[List[ImageInfo]] = None
    quality_score: float
    quality_factors: Optional[QualityFactors] = None
    priority_score: int
    priority_factors: Optional[PriorityFactors] = None
    status: ArticleStatus
    batch_id: Optional[UUID] = None
    ai_used: bool
    ai_metadata: Optional[Dict[str, Any]] = None
    moderated_at: Optional[datetime] = None
    moderator_id: Optional[UUID] = None
    rejection_reason: Optional[str] = None
    published_at: Optional[datetime] = None
    scheduled_at: Optional[datetime] = None
    published_target_id: Optional[UUID] = None
    published_external_id: Optional[str] = None
    similar_to_id: Optional[UUID] = None
    similarity_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArticleListResponse(BaseModel):
    id: UUID
    token: str
    title: str
    category: Optional[str] = None
    source_id: Optional[UUID] = None
    source_name: Optional[str] = None
    status: ArticleStatus
    quality_score: float
    priority_score: int
    has_image: bool
    ai_used: bool
    pub_date: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ArticleDetailResponse(ArticleResponse):
    source_name: Optional[str] = None
    moderator_name: Optional[str] = None
    similar_articles: Optional[List["ArticleListResponse"]] = None
    versions_count: int = 0


class ArticleApproveRequest(BaseModel):
    target_id: Optional[UUID] = None
    schedule_at: Optional[datetime] = None
    use_ai_rewrite: bool = False


class ArticleRejectRequest(BaseModel):
    reason: Optional[str] = None


class ArticleScheduleRequest(BaseModel):
    scheduled_at: datetime
    target_id: Optional[UUID] = None


class ArticleBulkActionRequest(BaseModel):
    article_ids: List[UUID] = Field(..., min_items=1, max_items=50)


class ArticleBulkActionResponse(BaseModel):
    success_count: int
    failed_count: int
    failed_ids: List[UUID] = []
    message: str


class ArticleVersionResponse(BaseModel):
    id: UUID
    article_id: UUID
    version_number: int
    title: str
    content_clean: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    main_image_url: Optional[str] = None
    created_at: datetime
    created_by_id: Optional[UUID] = None
    created_by_name: Optional[str] = None
    change_summary: Optional[str] = None

    class Config:
        from_attributes = True


class ArticlePreviewRequest(BaseModel):
    template_id: Optional[UUID] = None
    target_id: Optional[UUID] = None


class ArticlePreviewResponse(BaseModel):
    text: str
    has_image: bool
    image_url: Optional[str] = None
    estimated_length: int
    warnings: List[str] = []


class ArticleFilterParams(BaseModel):
    status: Optional[List[ArticleStatus]] = None
    category: Optional[str] = None
    source_id: Optional[UUID] = None
    has_image: Optional[bool] = None
    ai_used: Optional[bool] = None
    min_quality: Optional[float] = None
    max_quality: Optional[float] = None
    min_priority: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    sort_by: str = "created_at"
    sort_order: str = "desc"
