"""FastAPI application for the Data Platform.

Endpoints:
    POST /evidence          — ingest a new evidence record
    GET  /evidence/{id}     — retrieve a single record
    POST /quality/evaluate  — run quality rules against data
    POST /replay/create     — create a new replay session
    POST /replay/{id}/step  — step through one event
    GET  /health            — health check
"""

from __future__ import annotations

from typing import Any

from data_platform.engines.evidence_engine import EvidenceEngine
from data_platform.engines.quality_engine import QualityEngine
from data_platform.engines.replay_engine import ReplayEngine
from data_platform.domain.entities import EvidenceRecord, QualityRule
from data_platform.domain.value_objects import EvidenceType, ReplayMode

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError:
    # FastAPI/pydantic may not be installed in test environments.
    # The module can still be imported for attribute inspection,
    # but the app won't run.
    FastAPI = None  # type: ignore[assignment,misc]
    BaseModel = object  # type: ignore[assignment,misc]
    HTTPException = Exception  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Application singletons
# ---------------------------------------------------------------------------

evidence_engine = EvidenceEngine()
quality_engine = QualityEngine()
replay_engine = ReplayEngine()


def create_app() -> Any:
    """Build and return the FastAPI application."""
    if FastAPI is None:
        raise RuntimeError("FastAPI is not installed")

    app = FastAPI(title="Data Platform API", version="1.0.0")

    # -- Request/Response models -----------------------------------------------

    class EvidenceRequest(BaseModel):  # type: ignore[misc]
        type: str = "event"
        payload: dict[str, Any] = Field(default_factory=dict)
        parent_id: str | None = None

    class EvidenceResponse(BaseModel):  # type: ignore[misc]
        id: str
        type: str
        payload: dict[str, Any]
        hash: str
        parent_id: str | None
        timestamp: float

    class QualityRuleRequest(BaseModel):  # type: ignore[misc]
        name: str
        field: str
        check_type: str
        threshold: float = 0.0
        parameters: dict[str, Any] = Field(default_factory=dict)

    class QualityEvaluateRequest(BaseModel):  # type: ignore[misc]
        data: list[dict[str, Any]]
        rules: list[QualityRuleRequest]

    class ReplayCreateRequest(BaseModel):  # type: ignore[misc]
        events: list[dict[str, Any]]
        mode: str = "sequential"

    # -- Evidence endpoints ---------------------------------------------------

    @app.post("/evidence", response_model=EvidenceResponse)
    async def ingest_evidence(req: EvidenceRequest) -> dict[str, Any]:
        try:
            evidence_type = EvidenceType(req.type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid evidence type: {req.type}")

        record = EvidenceRecord(
            type=evidence_type,
            payload=req.payload,
            parent_id=req.parent_id,
        )
        try:
            result = evidence_engine.ingest(record)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "id": result.id,
            "type": result.type.value,
            "payload": result.payload,
            "hash": result.hash,
            "parent_id": result.parent_id,
            "timestamp": result.timestamp,
        }

    @app.get("/evidence/{record_id}", response_model=EvidenceResponse)
    async def get_evidence(record_id: str) -> dict[str, Any]:
        record = evidence_engine.get(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Evidence record not found")
        return {
            "id": record.id,
            "type": record.type.value,
            "payload": record.payload,
            "hash": record.hash,
            "parent_id": record.parent_id,
            "timestamp": record.timestamp,
        }

    # -- Quality endpoints ----------------------------------------------------

    @app.post("/quality/evaluate")
    async def evaluate_quality(req: QualityEvaluateRequest) -> dict[str, Any]:
        rules = [
            QualityRule(
                name=r.name,
                field=r.field,
                check_type=r.check_type,
                threshold=r.threshold,
                parameters=r.parameters,
            )
            for r in req.rules
        ]
        try:
            report = quality_engine.evaluate(req.data, rules)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        return {
            "overall_score": report.overall_score.value,
            "passed": report.passed,
            "rule_count": report.rule_count,
            "field_results": [
                {
                    "rule_name": fr.rule_name,
                    "field_name": fr.field_name,
                    "score": fr.score.value,
                    "passed": fr.score.passed,
                    "total_records": fr.total_records,
                    "passed_records": fr.passed_records,
                }
                for fr in report.field_results
            ],
        }

    # -- Replay endpoints -----------------------------------------------------

    @app.post("/replay/create")
    async def create_replay(req: ReplayCreateRequest) -> dict[str, Any]:
        try:
            mode = ReplayMode(req.mode)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid replay mode: {req.mode}")

        session = replay_engine.create_session(req.events, mode=mode)
        return {
            "session_id": session.id,
            "total_events": len(session.events),
            "mode": session.mode.value,
        }

    @app.post("/replay/{session_id}/step")
    async def step_replay(session_id: str) -> dict[str, Any]:
        try:
            event = replay_engine.step(session_id)
        except Exception as exc:
            raise HTTPException(status_code=404, detail=str(exc))

        state = replay_engine.get_state(session_id)
        return {
            "event": event,
            "position": state["position"],
            "is_complete": state["is_complete"],
            "remaining": state["remaining"],
        }

    # -- Health endpoint -------------------------------------------------------

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {
            "status": "healthy",
            "platform": "data-platform",
            "version": "1.0.0",
            "engines": {
                "evidence": {"record_count": evidence_engine.record_count},
                "quality": {"event_count": len(quality_engine.events)},
                "replay": {"session_count": replay_engine.session_count},
            },
        }

    return app
