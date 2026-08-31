FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY sentinel ./sentinel
RUN pip install --no-cache-dir .

FROM python:3.11-slim

WORKDIR /app

RUN useradd --create-home --shell /bin/bash sentinel

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --chown=sentinel:sentinel sentinel ./sentinel
COPY --chown=sentinel:sentinel pyproject.toml README.md ./

USER sentinel

EXPOSE 8080

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV SENTINEL_MODE=local

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://127.0.0.1:8080/health')" || exit 1

# Containers must listen on all interfaces. `sentinel serve` itself defaults to 127.0.0.1.
CMD ["python", "-m", "uvicorn", "sentinel.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
