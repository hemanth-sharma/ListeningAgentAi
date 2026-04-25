from celery import Celery

celery = Celery(
    "redarky",
    broker="redis://localhost:6379/0", # "redis://redis:6379/0", # for docker 
    backend="redis://localhost:6379/0", # "redis://redis:6379/0", # for docker
)

celery.conf.task_routes = {
    "app.workers.tasks.*": {"queue": "default"},
}