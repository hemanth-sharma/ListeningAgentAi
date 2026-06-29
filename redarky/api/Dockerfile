FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and minimal compiling utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from its explicit nested subfolder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything inside redarky/api into the working container directory
COPY . .

EXPOSE 8000

# Set Python path explicitly so imports like 'app.config' don't break
ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]