from typing import Optional
from redis.asyncio import Redis
from app.config import settings

_redis_client: Optional[Redis] = None


async def get_redis() -> Redis:
    """Get Redis connection"""
    global _redis_client
    
    if _redis_client is None:
        _redis_client = Redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
    
    return _redis_client


async def close_redis():
    """Close Redis connection"""
    global _redis_client
    
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# Вспомогательные функции для работы с Redis
async def redis_get(key: str) -> Optional[bytes]:
    """Get value from Redis"""
    redis = await get_redis()
    return await redis.get(key)


async def redis_set(key: str, value: str, expire: Optional[int] = None) -> bool:
    """Set value in Redis"""
    redis = await get_redis()
    if expire:
        return await redis.setex(key, expire, value)
    return await redis.set(key, value)


async def redis_delete(key: str) -> int:
    """Delete key from Redis"""
    redis = await get_redis()
    return await redis.delete(key)
