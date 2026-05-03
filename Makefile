.PHONY: run-go run-fastapi run-worker run-flower run-sync help

## --- GO SCRAPER ---
run-go:
	@echo "Starting Go Scraper..."
	cd redarky/scraper && go mod tidy && go run cmd/main.go

## --- FASTAPI & PYTHON (Using UV) ---
run-fastapi:
	@echo "Starting FastAPI with uv..."
	cd redarky/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-worker:
	@echo "Starting Celery Worker with solo pool..."
	cd redarky/api && uv run celery -A app.workers.celery_app.celery worker --loglevel=info -P solo
	
run-flower:
	@echo "Starting Celery Flower with uv..."
	cd redarky/api && uv run celery -A app.workers.celery_app.celery flower --port=5555

## --- UV ENVIRONMENT MANAGEMENT ---
# 'uv sync' is the modern way to ensure venv exists and deps are installed
run-sync:
	@echo "Syncing virtual environment with uv..."
	uv sync

# Help command to show you how to activate manually if needed
run-venv:
	@echo "Activating venv: "
	.venv\scripts\activate

run-dir:
	@echo "Go to working directories"
	cd redarky/api

## --- HELP ---
help:
	@echo "Usage:"
	@echo "  make run-go      - Run Go Scraper"
	@echo "  make run-fastapi - Run FastAPI server (via uv)"
	@echo "  make run-worker  - Run Celery worker (via uv)"
	@echo "  make run-flower  - Run Celery Flower (via uv)"
	@echo "  make run-sync    - Create/Sync venv and install all deps"
	@echo "  make run-venv    - Show manual activation command"