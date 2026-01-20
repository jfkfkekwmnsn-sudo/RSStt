from fastapi import APIRouter
from app.api import (
    auth, users, sources, articles, batches, 
    rules, templates, targets, analytics, audit, webhooks, health
)

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(articles.router, prefix="/articles", tags=["Articles"])
api_router.include_router(batches.router, prefix="/batches", tags=["Batches"])
api_router.include_router(rules.router, prefix="/rules", tags=["Rules"])
api_router.include_router(templates.router, prefix="/templates", tags=["Templates"])
api_router.include_router(targets.router, prefix="/targets", tags=["Publish Targets"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
api_router.include_router(audit.router, prefix="/audit", tags=["Audit"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])