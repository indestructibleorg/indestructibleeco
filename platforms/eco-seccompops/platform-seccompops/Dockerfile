# =============================================================================
# SecCompOps Platform — ECO Namespace: eco-seccompops | Port: 8095
# Multi-stage build for production
# =============================================================================
FROM python:3.11-slim AS base

LABEL org.opencontainers.image.title="seccompops-platform"
LABEL org.opencontainers.image.description="Security & Compliance Operations Platform"
LABEL app.kubernetes.io/name="seccompops-platform"
LABEL app.kubernetes.io/part-of="eco-base"
LABEL app.kubernetes.io/managed-by="argocd"
LABEL eco-base/platform="platform-seccompops"
LABEL eco-base/namespace="eco-seccompops"

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

EXPOSE 8095 9095

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8095/healthz')"]

CMD ["uvicorn", "presentation.api.main:app", "--host", "0.0.0.0", "--port", "8095"]
