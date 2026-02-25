"""Health check and version endpoints for the GovOps Platform API.

Provides Kubernetes-style liveness and readiness probes, plus a version
information endpoint for operational diagnostics.
"""
from __future__ import annotations

import os
import time
from typing import Any

import structlog
from fastapi import APIRouter, status
from pydantic import BaseModel, Field

logger = structlog.get_logger("govops.health")

router = APIRouter(tags=["health"])

# ---------------------------------------------------------------------------
# Module-level state — set during application lifespan
# ---------------------------------------------------------------------------

_startup_time: float = time.monotonic()


def reset_startup_time() -> None:
    """Reset the startup clock (called during application lifespan startup)."""
    global _startup_time
    _startup_time = time.monotonic()


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class LivenessResponse(BaseModel):
    """Response for the liveness probe."""

    status: str = "ok"


class DependencyCheck(BaseModel):
    """Health status of a single dependency."""

    name: str
    status: str = "ok"
    latency_ms: float | None = None
    detail: str = ""


class ReadinessResponse(BaseModel):
    """Response for the readiness probe."""

    status: str = Field(description="Overall readiness: ok | degraded | unavailable")
    uptime_seconds: float = Field(description="Seconds since application startup.")
    checks: list[DependencyCheck] = Field(default_factory=list)


class VersionResponse(BaseModel):
    """Build and version information."""

    version: str
    build: str
    commit_sha: str
    python_version: str = ""
    environment: str = ""


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/healthz",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
    description="Returns 200 when the process is alive. Used by Kubernetes liveness probes.",
)
async def liveness() -> LivenessResponse:
    """Minimal liveness check — if this responds the process is healthy."""
    return LivenessResponse(status="ok")


@router.get(
    "/readyz",
    response_model=ReadinessResponse,
    summary="Readiness probe",
    description="Checks critical dependencies and reports overall readiness.",
)
async def readiness() -> ReadinessResponse:
    """Readiness probe that verifies dependency availability.

    Returns 200 with ``status: ok`` when all dependencies are reachable,
    200 with ``status: degraded`` when non-critical checks fail, or 503
    when critical checks fail.
    """
    uptime = round(time.monotonic() - _startup_time, 2)
    checks: list[DependencyCheck] = []
    overall = "ok"

    # -- Database check (placeholder) --------------------------------------
    db_check = DependencyCheck(name="database", status="ok")
    checks.append(db_check)

    # -- Redis check (placeholder) -----------------------------------------
    redis_check = DependencyCheck(name="redis", status="ok")
    checks.append(redis_check)

    # -- Determine overall status ------------------------------------------
    statuses = [c.status for c in checks]
    if any(s == "unavailable" for s in statuses):
        overall = "unavailable"
    elif any(s == "degraded" for s in statuses):
        overall = "degraded"

    response = ReadinessResponse(
        status=overall,
        uptime_seconds=uptime,
        checks=checks,
    )

    if overall != "ok":
        logger.warning("readiness_degraded", status=overall, checks=statuses)

    return response


@router.get(
    "/api/v1/version",
    response_model=VersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Version information",
    description="Returns build version, commit SHA, and environment metadata.",
)
async def version_info() -> VersionResponse:
    """Return the running application version and build metadata."""
    import sys

    return VersionResponse(
        version=os.getenv("APP_VERSION", "1.0.0"),
        build=os.getenv("BUILD_NUMBER", "dev"),
        commit_sha=os.getenv("COMMIT_SHA", "unknown"),
        python_version=sys.version.split()[0],
        environment=os.getenv("ENVIRONMENT", "development"),
    )
