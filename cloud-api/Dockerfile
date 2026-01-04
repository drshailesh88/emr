FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Environment variables (override with -e or docker-compose)
ENV DATABASE_PATH=/data/cloud_api.db
ENV BACKUP_STORAGE_PATH=/data/backups

# Create data directory
RUN mkdir -p /data/backups

# Volume for persistent data
VOLUME ["/data"]

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
