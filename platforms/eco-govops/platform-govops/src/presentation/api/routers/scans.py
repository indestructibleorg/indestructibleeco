"""Scan management endpoints for the GovOps Platform API.

Provides endpoints to trigger new governance scans, list existing scan
reports, retrieve detailed scan results, and inspect individual findings.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = structlog.get_logger("govops.scans")

router = APIRouter(prefix="/api/v1/scans", tags=["scans"])


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class TriggerScanRequest(BaseModel):
    """Request body to trigger a new governance scan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    target: str = Field(..., min_length=1, description="Scan target identifier (module ID or path).")
    scan_type: str = Field(
        default="full", description="Scan type: full | incremental | targeted."
    )
    cycle_id: str | None = Field(default=None, description="Optional parent governance cycle ID.")
    include_patterns: list[str] = Field(
        default_factory=list, description="Glob patterns of resources to include."
    )
    exclude_patterns: list[str] = Field(
        default_factory=list, description="Glob patterns of resources to exclude."
    )
    timeout_seconds: int = Field(
        default=600, ge=30, le=7200, description="Scan timeout in seconds."
    )
    parallel_workers: int = Field(
        default=4, ge=1, le=32, description="Number of parallel scan workers."
    )

    @field_validator("scan_type")
    @classmethod
    def validate_scan_type(cls, v: str) -> str:
        allowed = {"full", "incremental", "targeted"}
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(f"Scan type must be one of: {', '.join(sorted(allowed))}")
        return normalised


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class ScanReportSummary(BaseModel):
    """Compact scan report representation for list views."""

    model_config = ConfigDict(from_attributes=True)

    report_id: str
    cycle_id: str = ""
    scanner_type: str = ""
    status: str
    modules_scanned: int = 0
    issues_found: int = 0
    issues_fixed: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None


class ScanReportDetail(ScanReportSummary):
    """Full scan report including severity breakdown and blocking status."""

    severity_counts: dict[str, int] = Field(
        default_factory=dict, description="Open finding counts by severity."
    )
    has_blockers: bool = Field(
        default=False, description="True if CRITICAL or HIGH unfixed findings exist."
    )


class FindingResponse(BaseModel):
    """Single scan finding."""

    model_config = ConfigDict(from_attributes=True)

    finding_id: str
    module_id: str = ""
    rule_id: str = ""
    severity: str
    title: str = ""
    description: str = ""
    location: str = ""
    remediation_hint: str = ""
    auto_fixable: bool = False
    fixed: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class PaginatedScanReportsResponse(BaseModel):
    """Paginated list of scan reports."""

    items: list[ScanReportSummary] = Field(default_factory=list)
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


class PaginatedFindingsResponse(BaseModel):
    """Paginated list of findings for a scan."""

    items: list[FindingResponse] = Field(default_factory=list)
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


class ScanTriggerResponse(BaseModel):
    """Response returned when a scan is successfully queued."""

    report_id: str
    status: str = "pending"
    message: str = "Scan queued successfully."


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=ScanTriggerResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger a new scan",
    description="Queue a new governance scan for the specified target.",
)
async def trigger_scan(body: TriggerScanRequest) -> ScanTriggerResponse:
    """Accept a scan request and enqueue it for asynchronous processing."""
    report_id = str(uuid.uuid4())
    logger.info(
        "scan_triggered",
        report_id=report_id,
        target=body.target,
        scan_type=body.scan_type,
        cycle_id=body.cycle_id,
    )

    # Placeholder — in production this enqueues via Celery / task executor
    return ScanTriggerResponse(
        report_id=report_id,
        status="pending",
        message=f"Scan queued for target '{body.target}' with type '{body.scan_type}'.",
    )


@router.get(
    "",
    response_model=PaginatedScanReportsResponse,
    status_code=status.HTTP_200_OK,
    summary="List scan reports",
    description="Returns a paginated list of scan reports with optional filtering.",
)
async def list_scans(
    skip: int = Query(default=0, ge=0, description="Number of items to skip."),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum items to return."),
    status_filter: str | None = Query(
        default=None,
        alias="status",
        description="Filter by scan status (pending, running, completed, failed, cancelled).",
    ),
    cycle_id: str | None = Query(default=None, description="Filter by parent cycle ID."),
    scanner_type: str | None = Query(default=None, description="Filter by scanner engine type."),
) -> PaginatedScanReportsResponse:
    """List scan reports with pagination and optional filters."""
    logger.info(
        "scans_list_requested",
        skip=skip,
        limit=limit,
        status_filter=status_filter,
        cycle_id=cycle_id,
    )

    # Placeholder — in production this queries the scan report repository
    return PaginatedScanReportsResponse(
        items=[],
        total=0,
        skip=skip,
        limit=limit,
        has_next=False,
    )


@router.get(
    "/{scan_id}",
    response_model=ScanReportDetail,
    status_code=status.HTTP_200_OK,
    summary="Get scan report detail",
    description="Returns the full detail of a specific scan report.",
    responses={404: {"description": "Scan report not found."}},
)
async def get_scan(
    scan_id: str = Path(..., description="UUID of the scan report."),
) -> ScanReportDetail:
    """Retrieve a single scan report by its identifier."""
    logger.info("scan_detail_requested", scan_id=scan_id)

    try:
        uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scan ID format: {scan_id}",
        )

    # Placeholder — in production this fetches from the scan report repository
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Scan report {scan_id} not found.",
    )


@router.get(
    "/{scan_id}/findings",
    response_model=PaginatedFindingsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get scan findings",
    description="Returns the paginated findings for a specific scan report.",
    responses={404: {"description": "Scan report not found."}},
)
async def get_scan_findings(
    scan_id: str = Path(..., description="UUID of the scan report."),
    skip: int = Query(default=0, ge=0, description="Number of items to skip."),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum items to return."),
    severity: str | None = Query(
        default=None, description="Filter by severity (critical, high, medium, low, info)."
    ),
    fixed: bool | None = Query(default=None, description="Filter by remediation status."),
) -> PaginatedFindingsResponse:
    """Retrieve findings for a specific scan report with optional filtering."""
    logger.info(
        "scan_findings_requested",
        scan_id=scan_id,
        skip=skip,
        limit=limit,
        severity=severity,
    )

    try:
        uuid.UUID(scan_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scan ID format: {scan_id}",
        )

    # Placeholder — in production this queries the findings store
    return PaginatedFindingsResponse(
        items=[],
        total=0,
        skip=skip,
        limit=limit,
        has_next=False,
    )
