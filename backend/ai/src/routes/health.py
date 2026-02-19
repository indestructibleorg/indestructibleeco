from fastapi import APIRouter
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat()}

@router.get("/ready")
async def ready():
    return {"status": "ready"}