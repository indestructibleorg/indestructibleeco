"""Integration test conftest — real PostgreSQL and Redis fixtures.

These tests require live infrastructure services.  In CI they are provided
via GitHub Actions service containers (see ci.yaml).  Locally, use:

    docker-compose -f docker-compose.test.yml up -d
    pytest tests/integration/

Environment variables consumed:
    DATABASE_URL      – async SQLAlchemy URL (asyncpg)
    DATABASE_URL_SYNC – sync SQLAlchemy URL (psycopg2)
    REDIS_URL         – redis:// URL
"""
from __future__ import annotations

import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Force testing environment before any src imports
# ---------------------------------------------------------------------------
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://superai_test:superai_test_secret@localhost:5433/superai_test",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://superai_test:superai_test_secret@localhost:5433/superai_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/15")
os.environ.setdefault("REDIS_PASSWORD", "")

# ---------------------------------------------------------------------------
# Async DB fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create the async engine and initialise schema once per session."""
    from sqlalchemy.ext.asyncio import create_async_engine
    from src.infrastructure.persistence.models import (  # noqa: F401
        AIExpertModel, QuantumJobModel, UserModel,
    )
    from src.infrastructure.persistence.database import Base

    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        pool_size=5,
        max_overflow=0,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator:
    """Provide a transactional session that is rolled back after each test.

    Using nested transactions (SAVEPOINT) ensures each test is fully isolated
    without truncating tables — significantly faster on large schemas.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        async with session.begin():
            yield session
            await session.rollback()


# ---------------------------------------------------------------------------
# Redis fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def redis_client():
    """Return a live RedisClient pointed at the test Redis instance."""
    import redis.asyncio as aioredis
    from src.infrastructure.cache.redis_client import RedisClient

    r = aioredis.from_url(os.environ["REDIS_URL"], decode_responses=False)
    await r.flushdb()

    client = RedisClient(prefix=f"test:{uuid.uuid4().hex[:8]}:", default_ttl=60)
    yield client

    await r.flushdb()
    await r.aclose()


# ---------------------------------------------------------------------------
# FastAPI TestClient fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Create the FastAPI application instance once per session."""
    from src.presentation.api.main import app as _app
    return _app


@pytest.fixture
def client(app):
    """Synchronous TestClient for route-level integration tests."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Admin JWT token headers for authenticated requests."""
    from src.infrastructure.security import JWTHandler
    handler = JWTHandler()
    token = handler.create_access_token(
        subject="integration_admin",
        role="admin",
        extra={"user_id": str(uuid.uuid4())},
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers() -> dict[str, str]:
    """Viewer-role JWT token headers (read-only permissions)."""
    from src.infrastructure.security import JWTHandler
    handler = JWTHandler()
    token = handler.create_access_token(
        subject="integration_viewer",
        role="viewer",
        extra={"user_id": str(uuid.uuid4())},
    )
    return {"Authorization": f"Bearer {token}"}
