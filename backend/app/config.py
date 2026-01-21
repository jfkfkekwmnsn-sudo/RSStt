from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "News Aggregator"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = Field(..., min_length=32)
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/news_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = Field(..., min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_WEBHOOK_SECRET: str = ""
    TELEGRAM_MODERATION_CHAT_ID: int = 0
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_ENABLED: bool = True
    AI_MAX_TOKENS_PER_DAY: int = 100000
    
    # Ingestion
    DEFAULT_FETCH_INTERVAL_MINUTES: int = 15
    MAX_ARTICLES_PER_FETCH: int = 50
    ARTICLE_FRESHNESS_DAYS: int = 7
    
    # Publishing
    MIN_PUBLISH_INTERVAL_SECONDS: int = 60
    MAX_PUBLISH_RETRIES: int = 3
    
    # S3/MinIO (optional)
    S3_ENDPOINT: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    S3_BUCKET: str = "news-images"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
