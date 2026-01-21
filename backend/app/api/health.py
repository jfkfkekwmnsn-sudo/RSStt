from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
from datetime import datetime

from app.api.deps import get_db
from app.schemas.common import HealthResponse
from app.config import settings
from app.utils.redis import get_redis

router = APIRouter()


@router.get("", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db)
):
    """Check health of all services"""
    db_ok = False
    redis_ok = False
    
    # Check database
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass
    
    # Check Redis
    try:
        redis = await get_redis()
        await redis.ping()
        redis_ok = True
    except Exception:
        pass
    
    status = "healthy" if (db_ok and redis_ok) else "degraded"
    
    return HealthResponse(
        status=status,
        version=settings.APP_VERSION,
        database=db_ok,
        redis=redis_ok,
        timestamp=datetime.now()
    )
