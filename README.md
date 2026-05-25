## Testing pending for airflow-ai-phase

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
Go: go mod tidy
Go: go run cmd/main.go

docker run -d -p 6379:6379 redis

Airflow working testing commands: on linux
`killall airflow uvicorn 2>/dev/null || pkill -f airflow`
`export AIRFLOW_HOME="/mnt/d/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/pipeline"`
`export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite://///mnt/d/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/pipeline/airflow.db"`
`export AIRFLOW__API_AUTH__JWT_SECRET="super-secret-shared-key-for-airflow3-local-dev-12345"`
`airflow db migrate`
`airflow standalone`

export AIRFLOW_HOME="/mnt/d/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/pipeline"
export AIRFLOW__DATABASE__SQL_ALCHEMY_CONN="sqlite://///mnt/d/SaaS/ListeningAIAgent/ListeningAgentAi/redarky/pipeline/airflow.db"
export AIRFLOW__API_AUTH__JWT_SECRET="super-secret-shared-key-for-airflow3-local-dev-12345"

## Phase 1: Go Scrappers to extract data

- Go routine scrapers are done
- Further refinements later

## Phase 2: Backend CRUD skeleton (FastAPI)

- Done
- Add Airflow

## Phase 2: Data Pipeline

- Basic Data pipeline is ready
- Storing raw data locally -> Later replaced by s3
- Using Celery tasks -> Later with Airflow DAG

## Phase 3: Create AI Agent

- DONE
- Testing and Integrating with frontend pending

## Phase 4: Clean and Analyze data via AI agents
- Full flow testing pending

## Phase 5: Frontend Next JS
- Design frontend - DONE
- Build frontend application

## Phase 6: Improve and test security
