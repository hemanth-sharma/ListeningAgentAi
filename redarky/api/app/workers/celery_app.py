from celery import Celery

from app.config import settings

celery = Celery(
    "redarky",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery.conf.task_routes = {
    "app.workers.tasks.*": {"queue": "default"},
}

# Optional: Ensure it works well with Windows
celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)