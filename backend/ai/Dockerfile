FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY backend/services/ai/pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install fastapi uvicorn pydantic pydantic-settings httpx redis numpy scikit-learn \
    networkx scipy prometheus-client gunicorn sentence-transformers

COPY backend/services/ai/ ./
COPY packages/shared-types/ /app/shared-types/

EXPOSE 8000

CMD ["gunicorn", "src.app:app", "-k", "uvicorn.workers.UvicornWorker", \
     "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120"]