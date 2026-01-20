from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "news_aggregator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Beat schedule
celery_app.conf.beat_schedule = {
    # Fetch sources every 5 minutes
    "fetch-sources": {
        "task": "app.workers.tasks.fetch_all_sources",
        "schedule": crontab(minute="*/5"),
    },
    # Create batches every 10 minutes
    "create-batches": {
        "task": "app.workers.tasks.create_moderation_batches",
        "schedule": crontab(minute="*/10"),
    },
    # Send batches to Telegram every 15 minutes
    "send-batches": {
        "task": "app.workers.tasks.send_batches_to_telegram",
        "schedule": crontab(minute="*/15"),
    },
    # Execute scheduled publish jobs every minute
    "execute-scheduled": {
        "task": "app.workers.tasks.execute_scheduled_jobs",
        "schedule": crontab(minute="*"),
    },
    # Housekeeping daily at 3 AM
    "housekeeping": {
        "task": "app.workers.tasks.housekeeping",
        "schedule": crontab(hour=3, minute=0),
    },
    # Update source reputations daily at 4 AM
    "update-reputations": {
        "task": "app.workers.tasks.update_source_reputations",
        "schedule": crontab(hour=4, minute=0),
    },
}