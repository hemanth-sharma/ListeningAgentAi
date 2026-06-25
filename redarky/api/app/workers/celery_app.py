from celery import Celery
from app.config import settings

celery = Celery(
    "redarky",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

# Active eager execution allows debugging inside FastAPI's event loop during local tests
celery.conf.task_always_eager = True
celery.conf.task_eager_propagates = True

celery.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)