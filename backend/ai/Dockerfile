# IndestructibleEco v1.0 — AI Inference Service Docker Image
# URI: indestructibleeco://docker/ai-service
# Build context: backend/ai/
# Build: docker build -t ghcr.io/indestructibleorg/ai:v1.0.0 -f backend/ai/Dockerfile backend/ai/

FROM python:3.11-slim AS base

WORKDIR /app

LABEL org.opencontainers.image.title="IndestructibleEco AI Service" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="IndestructibleEco" \
      org.opencontainers.image.source="https://github.com/indestructibleorg/indestructibleeco" \
      org.opencontainers.image.description="AI Inference Service — Folding, Compute, Index, Governance Engines"

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-cache-dir ".[dev]" || \
    pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings httpx redis gunicorn prometheus-client

COPY . ./

EXPOSE 8000 8001

ENV ECO_ENVIRONMENT=production \
    ECO_AI_HTTP_PORT=8001 \
    ECO_AI_GRPC_PORT=8000 \
    ECO_LOG_LEVEL=info

CMD ["gunicorn", "src.app:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8001", "--workers", "2", "--timeout", "120"]