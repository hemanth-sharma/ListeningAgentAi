from celery import Celery

celery = Celery(
    "redarky",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
)

celery.conf.task_routes = {
    "app.workers.tasks.*": {"queue": "default"},
}