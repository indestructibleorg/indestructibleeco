"""Alert management endpoints for ObservOps Platform."""
from fastapi import APIRouter
from typing import List, Dict

router = APIRouter()

_alerts_store: List[Dict] = []


@router.post("/")
async def create_alert(alert: Dict):
    """Create a new alert."""
    _alerts_store.append(alert)
    return {"status": "created", "alert_id": alert.get("alert_id", len(_alerts_store))}


@router.get("/")
async def list_alerts(severity: str = None):
    """List alerts, optionally filtered by severity."""
    if severity:
        filtered = [a for a in _alerts_store if a.get("severity") == severity]
        return {"alerts": filtered, "count": len(filtered)}
    return {"alerts": _alerts_store, "count": len(_alerts_store)}


@router.get("/active")
async def active_alerts():
    """List active (unresolved) alerts."""
    active = [a for a in _alerts_store if not a.get("resolved_at")]
    return {"alerts": active, "count": len(active)}


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert."""
    from datetime import datetime, timezone
    for a in _alerts_store:
        if a.get("alert_id") == alert_id:
            a["resolved_at"] = datetime.now(timezone.utc).isoformat()
            return {"status": "resolved", "alert_id": alert_id}
    return {"status": "not_found", "alert_id": alert_id}
