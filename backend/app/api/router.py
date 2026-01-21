from fastapi import APIRouter

from app.api import (
    analytics, articles, audit, auth, batches, health, rules, 
    sources, targets, templates, users, webhooks
)

api_router = APIRouter()

# Include routers
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(articles.router, prefix="/articles", tags=["articles"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(batches.router, prefix="/batches", tags=["batches"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(rules.router, prefix="/rules", tags=["rules"])
api_router.include_router(sources.router, prefix="/sources", tags=["sources"])
api_router.include_router(targets.router, prefix="/targets", tags=["targets"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])

__all__ = ["api_router"]
