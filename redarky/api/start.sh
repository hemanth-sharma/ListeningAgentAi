#!/bin/bash

# 1. Start Redis Server in the background
echo "Starting local Redis Server..."
redis-server --daemonize yes

# 2. Start Celery Worker in the background
echo "Starting Celery worker process..."
celery -A app.workers.celery_app.celery worker --loglevel=info &

# 3. Start FastAPI in the foreground (keeps the Docker container alive)
echo "Starting FastAPI app via Uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000