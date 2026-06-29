#!/bin/bash
set -e

echo "================──────────────────────────────────"
echo "⚙️ Starting Monolithic Stack Setup..."
echo "================──────────────────────────────────"

# 1. Initialize and Start PostgreSQL Natively
echo "🚀 Initializing and configuring PostgreSQL..."
# Create Postgres runtime directories if they don't exist
mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql

# Initialize database cluster if empty
if [ ! -d "/var/lib/postgresql/data" ]; then
    mkdir -p /var/lib/postgresql/data
    chown -R postgres:postgres /var/lib/postgresql/data
    su - postgres -c "/usr/lib/postgresql/15/bin/initdb -D /var/lib/postgresql/data"
fi

# Start PostgreSQL service via the postgres system user
su - postgres -c "/usr/lib/postgresql/15/bin/pg_ctl -D /var/lib/postgresql/data -l /var/log/postgresql.log start"

# 2. Bootstrap application schemas and users
echo "🔑 Provisioning default system database user roles..."
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'password';\"" || true
su - postgres -c "psql -c \"CREATE DATABASE redarky_db;\"" || true

# 3. Run Alembic Migrations automatically on startup
if [ -f "alembic.ini" ]; then
    echo "📦 Executing structural Alembic migrations..."
    # Use standard python path to run migrations against localhost db
    python -m alembic upgrade head
fi

# 4. Start Redis Server in background daemon mode
echo "🧠 Initializing local structural cache engine (Redis)..."
redis-server --daemonize yes

# 5. Start background worker subsystem
echo "🐝 Launching Celery background task ingestion queues..."
celery -A app.workers.celery_app.celery worker --loglevel=info &

# 6. Boot FastAPI in the foreground
echo "📡 Launching core FastAPI production engine..."
echo "================──────────────────────────────────"
exec uvicorn app.main:app --host 0.0.0.0 --port 8000