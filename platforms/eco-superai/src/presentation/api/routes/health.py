"""Health check and system status endpoints."""
from __future__ import annotations

import platform
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Response
from fastapi.responses import ORJSONResponse

router = APIRouter()

_START_TIME = time.time()


@router.get("/health", response_class=ORJSONResponse)
async def health_check() -> dict[str, Any]:
    """Basic health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
    }


@router.get("/health/detailed", response_class=ORJSONResponse)
async def detailed_health() -> dict[str, Any]:
    """Detailed health check with dependency status."""
    checks: dict[str, Any] = {}

    # Database check
    try:
        from src.infrastructure.persistence.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy", "type": "postgresql"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis check
    try:
        from src.infrastructure.cache.redis_client import get_redis
        redis = await get_redis()
        await redis.ping()
        checks["redis"] = {"status": "healthy", "type": "redis"}
    except Exception as e:
        checks["redis"] = {"status": "unhealthy", "error": str(e)}

    # Overall status
    all_healthy = all(c.get("status") == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "uptime_seconds": round(time.time() - _START_TIME, 2),
        "system": {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "processor": platform.processor() or "unknown",
        },
        "checks": checks,
    }


@router.get("/ready")
async def readiness() -> Response:
    """Kubernetes readiness probe."""
    try:
        from src.infrastructure.persistence.database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return Response(status_code=200, content="OK")
    except Exception:
        return Response(status_code=503, content="NOT READY")


@router.get("/live")
async def liveness() -> Response:
    """Kubernetes liveness probe."""
    return Response(status_code=200, content="OK")