# redarky (working name)
## Commands to run Locally
cd redarky/scraper
go run cmd/main.go
go runs here "http://localhost:8081"

cd redarky/api
<!-- celery -A app.workers.celery_app worker --loglevel=info -P solo -->
Celery: celery -A app.workers.celery_app.celery worker --loglevel=info
Flower: celery -A app.workers.celery_app.celery flower --port=5555
Fastapi: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker run -d -p 6379:6379 redis


## Phase 1: Go Scrappers to extract data
- Go routine scrapers are done
- Further refinements later

## Phase 2: Backend CRUD skeleton (FastAPI)
- Done

## Phase 2: Data Pipeline
- Basic Data pipeline is ready
- Storing raw data locally -> Later replaced by s3
- Using Celery tasks -> Later with Airflow DAG

## Phase 3: Create AI Agent
- Pending

## Phase 4: Clean and Analyze data via AI agents