# =============================================================================
# DataOps Platform — ECO Namespace: eco-dataops | Port: 8092
# =============================================================================
FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="dataops-platform"
LABEL org.opencontainers.image.description="Data & Evidence Operations Platform"
LABEL app.kubernetes.io/name="dataops-platform"
LABEL app.kubernetes.io/part-of="eco-base"
LABEL app.kubernetes.io/managed-by="argocd"
LABEL eco-base/platform="platform-dataops"
LABEL eco-base/namespace="eco-dataops"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

FROM base AS builder
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

FROM base AS production
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src/ ./src/

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
USER appuser

EXPOSE 8092 9092

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8092/healthz')"]

CMD ["uvicorn", "presentation.api.main:app", "--host", "0.0.0.0", "--port", "8092"]
