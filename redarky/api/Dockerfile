FROM python:3.11-slim

WORKDIR /app

# Install system dependencies, PostgreSQL client, AND Redis Server
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    build-essential \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set up environment variables
ENV PYTHONPATH=/app
# Point Celery and app to the local internal Redis instance we are about to boot
ENV CELERY_BROKER_URL=redis://localhost:6379/0

EXPOSE 8000

# Make the start script executable
RUN chmod +x start.sh

# Run our all-in-one process bootloader script
CMD ["./start.sh"]