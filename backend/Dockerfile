FROM python:3.12-slim

LABEL maintainer="Proxmox Self-Service Portal"
LABEL description="FastAPI backend + APScheduler background worker"

WORKDIR /app

# Install OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Default command: run the FastAPI server
# For the worker, override with: python -m cronjob.worker
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
