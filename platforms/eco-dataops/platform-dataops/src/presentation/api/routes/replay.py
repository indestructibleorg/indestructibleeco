"""Replay API — State reconstruction and timeline management endpoints."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from engines.replay_engine.engine import ReplayEngine, ReplayMode

router = APIRouter()

_replay = ReplayEngine()


class RecordEventRequest(BaseModel):
    """Request to record a timeline event."""

    event_type: str
    actor: str
    payload: dict[str, Any] = {}


class ReplayRequest(BaseModel):
    """Request to initiate a replay session."""

    mode: str = "PARTIAL"
    start_sequence: int = 0
    end_sequence: int | None = None


@router.post("/events")
async def record_event(request: RecordEventRequest):
    """Record a new timeline event."""
    event = _replay.record_event(
        event_type=request.event_type,
        actor=request.actor,
        payload=request.payload,
    )
    return {
        "event_id": event.event_id,
        "sequence_number": event.sequence_number,
        "hash_value": event.hash_value,
    }


@router.post("/sessions")
async def create_replay_session(request: ReplayRequest):
    """Create a new replay session."""
    mode = ReplayMode[request.mode]
    session = _replay.replay(
        mode=mode,
        start_seq=request.start_sequence,
        end_seq=request.end_sequence,
    )
    return {
        "session_id": session.session_id,
        "mode": session.mode.value,
        "status": session.status,
        "events_replayed": len(session.events),
    }


@router.get("/timeline/integrity")
async def verify_timeline():
    """Verify timeline integrity."""
    is_valid, errors = _replay.verify_timeline_integrity()
    return {
        "valid": is_valid,
        "errors": errors,
        "timeline_length": len(_replay.timeline),
    }


@router.get("/stats")
async def replay_stats():
    """Get replay engine statistics."""
    return _replay.get_timeline_stats()
