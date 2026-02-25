"""API request/response schemas for the Governance Operations Platform.

Reusable Pydantic v2 schemas for standardised request validation and
response serialisation across all API routes.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# Standard envelopes
# ============================================================================

class StandardResponse(BaseModel):
    """Standard API success response wrapper."""

    success: bool = True
    data: Any = None
    message: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Correlation ID for tracing.",
    )


class ErrorResponse(BaseModel):
    """Structured error response returned by exception handlers."""

    model_config = ConfigDict(frozen=True)

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable summary.")
    details: list[dict[str, Any]] = Field(default_factory=list)
    severity: str = Field(default="medium", description="Error severity.")
    request_id: str | None = None
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z",
    )


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""

    items: list[Any]
    total: int = Field(ge=0)
    skip: int = Field(ge=0)
    limit: int = Field(ge=1)
    has_next: bool = False


# ============================================================================
# Governance cycle schemas
# ============================================================================

class CycleStatus(str, Enum):
    """Lifecycle status of a governance cycle."""

    PENDING = "pending"
    RUNNING = "running"
    SCANNING = "scanning"
    ENFORCING = "enforcing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CycleRequest(BaseModel):
    """Request to start a governance cycle."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=200, description="Cycle name.")
    description: str = Field(default="", max_length=2000)
    modules: list[str] = Field(default_factory=list, description="Module IDs to include.")
    auto_enforce: bool = Field(default=False, description="Auto-enforce findings above threshold.")
    severity_threshold: str = Field(default="warning", description="Minimum severity for enforcement.")
    tags: dict[str, str] = Field(default_factory=dict)

    @field_validator("severity_threshold")
    @classmethod
    def validate_severity(cls, v: str) -> str:
        allowed = {"info", "warning", "error", "critical"}
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(f"Severity must be one of: {', '.join(sorted(allowed))}")
        return normalised


class CycleResponse(BaseModel):
    """Full governance cycle response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str = ""
    status: str
    modules_total: int = 0
    modules_completed: int = 0
    findings_count: int = 0
    enforcements_count: int = 0
    auto_enforce: bool = False
    severity_threshold: str = "warning"
    tags: dict[str, str] = Field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    duration_seconds: float | None = None


class CycleSummary(BaseModel):
    """Compact summary of a governance cycle for list views."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: str
    findings_count: int = 0
    enforcements_count: int = 0
    created_at: datetime


# ============================================================================
# Scan schemas
# ============================================================================

class ScanRequest(BaseModel):
    """Request to initiate a compliance scan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    target: str = Field(..., min_length=1, description="Scan target identifier.")
    scan_type: str = Field(default="full", description="full | incremental | targeted.")
    cycle_id: str | None = Field(default=None, description="Optional parent cycle ID.")
    include_patterns: list[str] = Field(default_factory=list)
    exclude_patterns: list[str] = Field(default_factory=list)
    timeout_seconds: int = Field(default=600, ge=30, le=7200)

    @field_validator("scan_type")
    @classmethod
    def validate_scan_type(cls, v: str) -> str:
        allowed = {"full", "incremental", "targeted"}
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(f"Scan type must be one of: {', '.join(sorted(allowed))}")
        return normalised


class ScanResponse(BaseModel):
    """Compliance scan result."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    target: str
    scan_type: str
    status: str
    cycle_id: str | None = None
    findings_count: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None


# ============================================================================
# Enforcement schemas
# ============================================================================

class EnforcementRequest(BaseModel):
    """Request to trigger an enforcement run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    cycle_id: str = Field(..., description="Cycle ID to enforce findings for.")
    mode: str = Field(default="dry_run", description="dry_run | warn | enforce.")
    auto_remediate: bool = Field(default=False)
    require_approval: bool = Field(default=True)

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        allowed = {"dry_run", "warn", "enforce"}
        normalised = v.lower().strip()
        if normalised not in allowed:
            raise ValueError(f"Mode must be one of: {', '.join(sorted(allowed))}")
        return normalised


class EnforcementResponse(BaseModel):
    """Enforcement run result."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    cycle_id: str
    mode: str
    status: str
    total_findings: int = 0
    enforced_count: int = 0
    skipped_count: int = 0
    failed_count: int = 0
    remediations_applied: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ============================================================================
# Evidence schemas
# ============================================================================

class EvidenceResponse(BaseModel):
    """Single evidence record response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    cycle_id: str
    module_id: str | None = None
    evidence_type: str
    content_hash: str
    previous_hash: str = ""
    sealed: bool = False
    collected_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class ChainResponse(BaseModel):
    """Evidence chain for a governance cycle."""

    cycle_id: str
    chain_length: int = 0
    is_valid: bool = True
    first_evidence_at: datetime | None = None
    last_evidence_at: datetime | None = None
    entries: list[EvidenceResponse] = Field(default_factory=list)


# ============================================================================
# ETL pipeline schemas
# ============================================================================

class ETLPipelineStatus(str, Enum):
    """Lifecycle status of an ETL pipeline."""

    PENDING = "pending"
    EXTRACTING = "extracting"
    TRANSFORMING = "transforming"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ETLPipelineRequest(BaseModel):
    """Request to create or run an ETL pipeline."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=200, description="Pipeline name.")
    source: str = Field(..., min_length=1, description="Data source identifier.")
    destination: str = Field(..., min_length=1, description="Data destination identifier.")
    transform_config: dict[str, Any] = Field(
        default_factory=dict,
        description="Transformation rules and configuration.",
    )
    schedule: str | None = Field(
        default=None,
        description="Cron expression for scheduled runs.",
    )
    tags: dict[str, str] = Field(default_factory=dict)


class ETLPipelineResponse(BaseModel):
    """ETL pipeline status response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    source: str
    destination: str
    status: str
    records_extracted: int = 0
    records_transformed: int = 0
    records_loaded: int = 0
    errors_count: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: float | None = None


# ============================================================================
# Module and gate schemas
# ============================================================================

class ModuleResponse(BaseModel):
    """Governance module public representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str = ""
    module_type: str
    status: str
    version: str = "1.0.0"
    enabled: bool = True
    last_scan_at: datetime | None = None
    findings_count: int = 0
    created_at: datetime


class GateResponse(BaseModel):
    """Governance gate evaluation result."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    gate_type: str
    status: str
    passed: bool = False
    cycle_id: str | None = None
    conditions_met: int = 0
    conditions_total: int = 0
    evaluated_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Public API
# ============================================================================

__all__ = [
    "StandardResponse",
    "ErrorResponse",
    "PaginatedResponse",
    "CycleStatus",
    "CycleRequest",
    "CycleResponse",
    "CycleSummary",
    "ScanRequest",
    "ScanResponse",
    "EnforcementRequest",
    "EnforcementResponse",
    "EvidenceResponse",
    "ChainResponse",
    "ETLPipelineStatus",
    "ETLPipelineRequest",
    "ETLPipelineResponse",
    "ModuleResponse",
    "GateResponse",
]
