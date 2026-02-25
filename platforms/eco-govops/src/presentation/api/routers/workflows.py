"""Workflow management endpoints for the GovOps Platform API.

Provides endpoints to trigger governance analysis cycles, monitor their
progress, cancel running cycles, and inspect the workflow engine status.

All endpoints delegate to the :class:`ClosedLoopEngine` orchestrator which
manages the lifecycle of governance cycles.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

from engine.orchestrator.analysis_workflow import WorkflowConfig
from engine.orchestrator.closed_loop import ClosedLoopEngine

logger = structlog.get_logger("govops.workflows")

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])

# ---------------------------------------------------------------------------
# Singleton engine instance — started on module load.
# In production this would be initialised via app lifespan events with
# injected scanner/analyzer/enforcer dependencies.
# ---------------------------------------------------------------------------

_engine = ClosedLoopEngine()
_engine.start()


def get_engine() -> ClosedLoopEngine:
    """Return the module-level engine instance.

    Exposed as a function so tests can monkeypatch it.
    """
    return _engine


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TriggerCycleRequest(BaseModel):
    """Request body to trigger a new governance analysis cycle."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(
        ..., min_length=1, max_length=200, description="Human-readable cycle name."
    )
    description: str = Field(default="", max_length=2000, description="Cycle description.")
    modules: list[str] = Field(
        default_factory=list, description="Module IDs to include; empty means all."
    )
    auto_enforce: bool = Field(
        default=False,
        description="Automatically enforce findings above the severity threshold.",
    )
    severity_threshold: str = Field(
        default="warning",
        description="Minimum severity that triggers enforcement: info | warning | error | critical.",
    )
    max_duration_seconds: int = Field(
        default=3600, ge=60, le=86400, description="Maximum cycle duration in seconds."
    )
    tags: dict[str, str] = Field(default_factory=dict, description="Arbitrary tags for filtering.")

    @field_validator("severity_threshold")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"info", "warning", "error", "critical"}
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(sorted(allowed))}")
        return normalised


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class CycleSummary(BaseModel):
    """Compact governance cycle representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    cycle_id: str
    name: str
    status: str
    modules_total: int = 0
    modules_completed: int = 0
    findings_count: int = 0
    enforcements_count: int = 0
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None


class CycleDetail(CycleSummary):
    """Full governance cycle with configuration and timing metadata."""

    description: str = ""
    auto_enforce: bool = False
    severity_threshold: str = "warning"
    tags: dict[str, str] = Field(default_factory=dict)
    duration_seconds: float | None = None
    scan_report_ids: list[str] = Field(
        default_factory=list, description="Associated scan report IDs."
    )


class CycleTriggerResponse(BaseModel):
    """Response returned when a cycle is successfully queued."""

    cycle_id: str
    status: str = "pending"
    message: str = "Governance cycle queued successfully."


class CycleCancelResponse(BaseModel):
    """Response returned when a cycle cancellation is requested."""

    cycle_id: str
    status: str = "cancelled"
    message: str = "Cycle cancellation requested."


class PaginatedCyclesResponse(BaseModel):
    """Paginated list of governance cycles."""

    items: list[CycleSummary] = Field(default_factory=list)
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


class WorkflowEngineStatus(BaseModel):
    """Current status of the workflow engine."""

    engine_status: str = Field(description="Engine state: running | paused | stopped.")
    active_cycles: int = Field(default=0, ge=0, description="Number of currently active cycles.")
    queued_cycles: int = Field(default=0, ge=0, description="Number of cycles waiting to execute.")
    completed_today: int = Field(
        default=0, ge=0, description="Cycles completed in the last 24 hours."
    )
    failed_today: int = Field(default=0, ge=0, description="Cycles failed in the last 24 hours.")
    workers_available: int = Field(default=0, ge=0, description="Number of idle worker slots.")
    workers_total: int = Field(default=0, ge=0, description="Total worker capacity.")
    uptime_seconds: float = Field(default=0.0, ge=0, description="Engine uptime in seconds.")
    last_cycle_at: datetime | None = Field(
        default=None, description="Timestamp of the most recently completed cycle."
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/cycles",
    response_model=CycleTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger analysis cycle",
    description="Queue a new governance analysis cycle for asynchronous execution.",
)
async def trigger_cycle(body: TriggerCycleRequest) -> CycleTriggerResponse:
    """Accept a governance cycle request and enqueue it for processing."""
    engine = get_engine()

    config = WorkflowConfig(
        name=body.name,
        description=body.description,
        modules=body.modules,
        auto_enforce=body.auto_enforce,
        severity_threshold=body.severity_threshold,
        max_duration_seconds=body.max_duration_seconds,
        tags=body.tags,
    )

    try:
        cycle_id = await engine.submit_cycle(config)
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    logger.info(
        "cycle_triggered",
        cycle_id=cycle_id,
        name=body.name,
        modules_count=len(body.modules),
        auto_enforce=body.auto_enforce,
    )

    return CycleTriggerResponse(
        cycle_id=cycle_id,
        status="pending",
        message=f"Governance cycle '{body.name}' queued successfully.",
    )


@router.get(
    "/cycles",
    response_model=PaginatedCyclesResponse,
    status_code=status.HTTP_200_OK,
    summary="List cycles",
    description="Returns a paginated list of governance analysis cycles.",
)
async def list_cycles(
    skip: int = Query(default=0, ge=0, description="Number of items to skip."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items to return."),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by cycle status (pending, running, completed, failed, cancelled).",
    ),
) -> PaginatedCyclesResponse:
    """List governance cycles with pagination and optional status filter."""
    engine = get_engine()
    history = engine.history

    if status_filter:
        history = [r for r in history if r.state == status_filter]

    total = len(history)
    page = history[skip : skip + limit]

    items = [
        CycleSummary(
            cycle_id=r.cycle_id,
            name=r.name,
            status=r.state,
            modules_total=r.modules_scanned,
            findings_count=r.findings_count,
            created_at=r.started_at or datetime.now(timezone.utc),
            started_at=r.started_at,
            completed_at=r.completed_at,
        )
        for r in page
    ]

    logger.info(
        "cycles_list_requested",
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        total=total,
    )

    return PaginatedCyclesResponse(
        items=items,
        total=total,
        skip=skip,
        limit=limit,
        has_next=(skip + limit) < total,
    )


@router.get(
    "/status",
    response_model=WorkflowEngineStatus,
    status_code=status.HTTP_200_OK,
    summary="Workflow engine status",
    description="Returns the current operational status of the workflow engine.",
)
async def get_workflow_status() -> WorkflowEngineStatus:
    """Return the current state of the workflow engine."""
    engine = get_engine()
    engine_status = engine.status()

    logger.info("workflow_status_requested")

    return WorkflowEngineStatus(
        engine_status=engine_status.engine_status,
        active_cycles=1 if engine_status.active_cycle else 0,
        queued_cycles=engine_status.queued_cycles,
        completed_today=engine_status.completed_count,
        failed_today=engine_status.failed_count,
        workers_available=engine_status.workers_available,
        workers_total=engine_status.workers_total,
        uptime_seconds=engine_status.uptime_seconds,
        last_cycle_at=engine_status.last_cycle_at,
    )


@router.get(
    "/cycles/{cycle_id}",
    response_model=CycleDetail,
    status_code=status.HTTP_200_OK,
    summary="Get cycle status",
    description="Returns the full detail of a specific governance cycle.",
    responses={404: {"description": "Cycle not found."}},
)
async def get_cycle(
    cycle_id: str = Path(..., description="ID of the governance cycle."),
) -> CycleDetail:
    """Retrieve a single governance cycle by its identifier."""
    engine = get_engine()
    record = engine.get_cycle(cycle_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance cycle {cycle_id} not found.",
        )

    logger.info("cycle_detail_requested", cycle_id=cycle_id)

    return CycleDetail(
        cycle_id=record.cycle_id,
        name=record.name,
        status=record.state,
        modules_total=record.modules_scanned,
        findings_count=record.findings_count,
        created_at=record.started_at or datetime.now(timezone.utc),
        started_at=record.started_at,
        completed_at=record.completed_at,
        duration_seconds=record.duration_seconds,
    )


@router.post(
    "/cycles/{cycle_id}/cancel",
    response_model=CycleCancelResponse,
    status_code=status.HTTP_200_OK,
    summary="Cancel a cycle",
    description="Request cancellation of a running or queued governance cycle.",
    responses={
        404: {"description": "Cycle not found."},
        409: {"description": "Cycle cannot be cancelled (already completed/failed)."},
    },
)
async def cancel_cycle(
    cycle_id: str = Path(..., description="ID of the governance cycle to cancel."),
) -> CycleCancelResponse:
    """Request cancellation of a governance cycle.

    Only cycles in ``pending`` or ``running`` status can be cancelled.
    """
    engine = get_engine()
    cancelled = await engine.cancel_cycle(cycle_id)

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Governance cycle {cycle_id} not found or already completed.",
        )

    logger.info("cycle_cancel_requested", cycle_id=cycle_id)

    return CycleCancelResponse(
        cycle_id=cycle_id,
        status="cancelled",
        message="Cycle cancellation requested.",
    )
