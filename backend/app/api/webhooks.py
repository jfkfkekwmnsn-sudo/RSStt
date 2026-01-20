from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.ext.asyncio import AsyncSession
import hmac
import hashlib

from app.api.deps import get_db
from app.config import settings
from app.telegram.handler import TelegramHandler

router = APIRouter()


def verify_telegram_secret(x_telegram_bot_api_secret_token: str = Header(None)):
    """Verify Telegram webhook secret"""
    if settings.TELEGRAM_WEBHOOK_SECRET:
        if x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid webhook secret"
            )


@router.post("/telegram")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_telegram_secret)
):
    """Handle Telegram webhook updates"""
    try:
        update_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    handler = TelegramHandler(db)
    await handler.process_update(update_data)
    
    return {"ok": True}


@router.post("/external/article")
async def external_article_webhook(
    request: Request,
    api_key: str = Header(..., alias="X-API-Key"),
    db: AsyncSession = Depends(get_db)
):
    """Receive articles from external sources"""
    # Verify API key
    # TODO: Implement API key verification
    
    try:
        article_data = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON"
        )
    
    from app.services.ingestion_service import IngestionService
    service = IngestionService(db)
    
    result = await service.process_external_article(article_data)
    
    return result