"""Metrics endpoints for ObservOps Platform."""
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

# In-memory store for demo
_metrics_store: List[Dict] = []


@router.post("/ingest")
async def ingest_metric(metric: Dict):
    """Ingest a metric data point."""
    _metrics_store.append(metric)
    return {"status": "accepted", "count": len(_metrics_store)}


@router.get("/")
async def list_metrics(limit: int = 100):
    """List recent metrics."""
    return {"metrics": _metrics_store[-limit:], "total": len(_metrics_store)}


@router.get("/query")
async def query_metrics(name: str):
    """Query metrics by name."""
    filtered = [m for m in _metrics_store if m.get("name") == name]
    return {"metrics": filtered, "count": len(filtered)}


@router.delete("/")
async def clear_metrics():
    """Clear all metrics (admin)."""
    _metrics_store.clear()
    return {"status": "cleared"}
