"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Readiness probe."""
    return {"status": "ok", "service": "seccompops-platform"}


@router.get("/livez")
async def livez():
    """Liveness probe."""
    return {"status": "alive"}
