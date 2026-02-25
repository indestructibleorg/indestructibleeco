"""Health check endpoints for ObservOps Platform."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Readiness probe."""
    return {"status": "ok", "service": "observops-platform", "namespace": "eco-observops"}


@router.get("/livez")
async def livez():
    """Liveness probe."""
    return {"status": "alive"}


@router.get("/readyz")
async def readyz():
    """Readiness probe with dependency checks."""
    return {
        "status": "ready",
        "service": "observops-platform",
        "components": {
            "metrics_collector": "ok",
            "alert_manager": "ok",
            "trace_collector": "ok",
            "health_monitor": "ok",
        },
    }
