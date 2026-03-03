FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Security: Create non-root user
RUN groupadd -r worker && useradd -r -g worker worker

WORKDIR /app

# Install dependencies
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Browsers are pre-installed in this image! 
# We just need to make sure the environment is ready.

COPY worker.py .

# Security: Change ownership
RUN chown -R worker:worker /app

# Security: Switch to non-root user
USER worker

# Expose port (default 8000, but will be overridden by host mapping)
EXPOSE 8000

# Entrypoint
CMD ["python", "worker.py"]
