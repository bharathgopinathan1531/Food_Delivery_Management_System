from celery import Celery

from app.config import settings


celery_app = Celery(
    "food_delivery",
    broker=getattr(
        settings,
        "REDIS_URL",
        "redis://localhost:6379/0"
    ),
    backend=getattr(
        settings,
        "REDIS_URL",
        "redis://localhost:6379/0"
    ),
)


celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=False,
)