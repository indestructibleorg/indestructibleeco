"""Health check endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Readiness probe."""
    return {"status": "ok", "service": "dataops-platform"}


@router.get("/livez")
async def livez():
    """Liveness probe."""
    return {"status": "alive"}
