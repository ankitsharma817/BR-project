from celery import Celery
from ..config import settings

celery_app = Celery(
    "br_match",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "api.tasks.matching_tasks",
        "api.tasks.email_tasks",
        "api.tasks.embedding_tasks",
        "api.tasks.webhook_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=86400,           # 24h result retention
    task_soft_time_limit=300,       # 5 min soft limit per task
    task_time_limit=600,            # 10 min hard limit
    task_routes={
        "api.tasks.matching_tasks.*": {"queue": "matching"},
        "api.tasks.email_tasks.*": {"queue": "email"},
        "api.tasks.embedding_tasks.*": {"queue": "embedding"},
        "api.tasks.webhook_tasks.*": {"queue": "webhooks"},
    },
)
