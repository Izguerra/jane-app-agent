FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (needed for some python packages like psycopg2)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code into /app/backend to match the import structure (backend.routers...)
COPY backend /app/backend

# Set PYTHONPATH so python can find the 'backend' module
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# Run the application with Gunicorn on PORT
CMD gunicorn -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120 --log-level debug
