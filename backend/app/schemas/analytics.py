from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, date


class DateRangeParams(BaseModel):
    date_from: Optional[date] = None
    date_to: Optional[date] = None


class SummaryStats(BaseModel):
    total_articles: int
    pending_articles: int
    approved_articles: int
    rejected_articles: int
    published_articles: int
    approval_rate: float
    avg_processing_time_minutes: Optional[float] = None
    articles_today: int
    articles_this_week: int


class CategoryStats(BaseModel):
    category: str
    total: int
    approved: int
    rejected: int
    published: int
    approval_rate: float


class SourceStats(BaseModel):
    source_id: str
    source_name: str
    total: int
    approved: int
    rejected: int
    approval_rate: float
    avg_quality: float
    reputation_score: float


class EditorStats(BaseModel):
    user_id: str
    username: str
    total_moderated: int
    approved: int
    rejected: int
    avg_processing_time_minutes: float


class TimeSeriesPoint(BaseModel):
    date: date
    count: int


class AnalyticsSummaryResponse(BaseModel):
    summary: SummaryStats
    categories: List[CategoryStats]
    top_sources: List[SourceStats]
    articles_by_day: List[TimeSeriesPoint]
    period_start: date
    period_end: date


class EditorPerformanceResponse(BaseModel):
    editors: List[EditorStats]
    period_start: date
    period_end: date


class SourceHealthResponse(BaseModel):
    sources: List[SourceStats]
    unhealthy_sources: List[Dict[str, Any]]  # Sources with high error rates