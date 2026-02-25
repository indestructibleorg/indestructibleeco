"""Distributed tracing endpoints for ObservOps Platform."""
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

_traces_store: List[Dict] = []


@router.post("/spans")
async def ingest_span(span: Dict):
    """Ingest a trace span."""
    _traces_store.append(span)
    return {"status": "accepted", "trace_id": span.get("trace_id")}


@router.get("/")
async def list_traces(limit: int = 50):
    """List recent traces."""
    trace_ids = list({s.get("trace_id") for s in _traces_store})
    return {"trace_ids": trace_ids[-limit:], "total": len(trace_ids)}


@router.get("/{trace_id}")
async def get_trace(trace_id: str):
    """Get all spans for a trace."""
    spans = [s for s in _traces_store if s.get("trace_id") == trace_id]
    return {"trace_id": trace_id, "spans": spans, "span_count": len(spans)}


@router.get("/{trace_id}/timeline")
async def trace_timeline(trace_id: str):
    """Get trace timeline sorted by start_time."""
    spans = [s for s in _traces_store if s.get("trace_id") == trace_id]
    spans.sort(key=lambda s: s.get("start_time", ""))
    return {"trace_id": trace_id, "timeline": spans}
