from celery import Celery

celery = Celery(
    "redarky",
    broker="redis://localhost:6379/0", # "redis://redis:6379/0", # for docker 
    backend="redis://localhost:6379/0", # "redis://redis:6379/0", # for docker
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