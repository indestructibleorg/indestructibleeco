# -- indestructibleeco AI Service --
FROM python:3.11-slim AS base
WORKDIR /app
RUN pip install poetry --no-cache-dir

COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false \
 && poetry install --only main --no-interaction --no-root

COPY src ./src
COPY engines ./engines
EXPOSE 8000 8001
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8001"]
