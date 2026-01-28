# Mock Service Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install Flask
RUN pip install --no-cache-dir flask gunicorn

# Copy application
COPY app.py .
COPY mock_log.txt .
COPY deployments.log .

# Create empty trigger files directory
RUN mkdir -p /app/mock_service

# Expose port
EXPOSE 8000

# Run with gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
