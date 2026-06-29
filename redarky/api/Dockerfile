FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, compiling tools, Redis, AND PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    build-essential \
    redis-server \
    postgresql \
    postgresql-contrib \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set up environment variables
ENV PYTHONPATH=/app
ENV CELERY_BROKER_URL=redis://localhost:6379/0
# Hardcode the database URL to point to our local internal Postgres database instance
ENV DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/redarky_db

EXPOSE 8000

RUN chmod +x start.sh

CMD ["./start.sh"]