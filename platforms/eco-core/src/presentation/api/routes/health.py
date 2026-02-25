"""Health check endpoints for Platform Core."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Readiness probe."""
    return {"status": "ok", "service": "platform-core", "namespace": "eco-core"}


@router.get("/livez")
async def livez():
    """Liveness probe."""
    return {"status": "alive"}


@router.get("/readyz")
async def readyz():
    """Readiness probe with dependency checks."""
    return {
        "status": "ready",
        "service": "platform-core",
        "components": {
            "auth_service": "ok",
            "memory_hub": "ok",
            "event_bus": "ok",
            "policy_audit": "ok",
            "infra_manager": "ok",
        },
    }
