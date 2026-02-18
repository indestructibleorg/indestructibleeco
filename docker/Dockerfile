# IndestructibleEco v1.0 — API Gateway Docker Image
# URI: indestructibleeco://docker/api-gateway
# Build: docker build -t ghcr.io/indestructibleorg/api:v1.0.0 -f docker/Dockerfile .
# Context: repository root (.)

# ── Stage 1: Builder ──────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: Production ──────────────────────────────────────────────
FROM python:3.11-slim AS production

LABEL org.opencontainers.image.title="IndestructibleEco API Gateway" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="IndestructibleEco" \
      org.opencontainers.image.source="https://github.com/indestructibleorg/indestructibleeco" \
      org.opencontainers.image.description="Enterprise Cloud-Native AI Platform — API Gateway"

RUN groupadd -r ecouser && useradd -r -g ecouser -d /app -s /sbin/nologin ecouser

WORKDIR /app

# Install dependencies from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY src/ ./src/
COPY pyproject.toml .
COPY requirements.txt .

# Create runtime directories
RUN mkdir -p /models /data /logs && \
    chown -R ecouser:ecouser /app /models /data /logs

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import httpx; r = httpx.get('http://localhost:8000/health'); r.raise_for_status()" || exit 1

# Runtime configuration
EXPOSE 8000

ENV ECO_ENVIRONMENT=production \
    ECO_HOST=0.0.0.0 \
    ECO_PORT=8000 \
    ECO_WORKERS=4 \
    ECO_LOG_LEVEL=INFO

USER ecouser

CMD ["uvicorn", "src.app:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log"]