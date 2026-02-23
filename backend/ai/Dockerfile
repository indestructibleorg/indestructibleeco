# -- indestructibleeco AI Service --
FROM python:3.13-slim AS base
WORKDIR /app
RUN pip install poetry --no-cache-dir

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-interaction --no-root || true

# Copy local source
COPY src ./src
COPY engines ./engines

# Copy shared src/core from repo root (injected by build context or CI)
# Fallback: create stub modules if src/core doesn't have registry/queue
RUN mkdir -p /app/src/core && \
    if [ ! -f /app/src/core/registry.py ]; then \
      echo 'class ModelRegistry:\n    def __init__(self): self._models = {}\n    @property\n    def count(self): return len(self._models)\n    async def list_models(self): return list(self._models.values())' > /app/src/core/registry.py; \
    fi && \
    if [ ! -f /app/src/core/queue.py ]; then \
      echo 'import asyncio\nclass RequestQueue:\n    def __init__(self): self._queue = asyncio.Queue()\n    def qsize(self): return self._queue.qsize()' > /app/src/core/queue.py; \
    fi && \
    touch /app/src/core/__init__.py

EXPOSE 8000 8001
RUN addgroup --system --gid 1001 eco && adduser --system --uid 1001 --ingroup eco eco
USER eco
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001"]