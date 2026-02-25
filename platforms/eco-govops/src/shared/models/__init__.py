"""Base Pydantic v2 models for the Governance Operations Platform.

Provides canonical base models, mixins, response envelopes, health checks,
and governance-specific configuration models shared across all layers.
"""
from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class GovOpsBaseModel(BaseModel):
    """Base model for all Governance Operations Platform entities.

    Enforces strict configuration and provides common fields.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        use_enum_values=True,
        str_strip_whitespace=True,
        validate_default=True,
    )

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier (UUID).",
    )


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class TimestampMixin(BaseModel):
    """Adds ``created_at`` and ``updated_at`` UTC timestamps."""

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC creation timestamp.",
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="UTC last-update timestamp.",
    )


class AuditMixin(BaseModel):
    """Adds ``created_by`` and ``updated_by`` actor fields."""

    created_by: str = Field(
        default="system",
        description="Actor who created the resource.",
    )
    updated_by: str = Field(
        default="system",
        description="Actor who last updated the resource.",
    )


# ---------------------------------------------------------------------------
# Generic response wrappers
# ---------------------------------------------------------------------------

class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response with navigation metadata.

    ``total_pages`` is computed from ``total`` and ``limit``.
    ``has_next`` indicates whether the client can request more pages.
    """

    items: list[T]
    total: int = Field(..., ge=0)
    skip: int = Field(..., ge=0)
    limit: int = Field(..., ge=1)
    has_next: bool = False
    total_pages: int = 1

    @model_validator(mode="after")
    def _compute_pagination(self) -> "PaginatedResponse[T]":
        if self.limit > 0 and self.total >= 0:
            self.total_pages = max(1, math.ceil(self.total / self.limit))
            self.has_next = (self.skip + self.limit) < self.total
        return self


class BatchResult(BaseModel, Generic[T]):
    """Result of a batch operation with per-item success/failure tracking."""

    total: int = Field(..., ge=0)
    succeeded: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    results: list[T] = Field(default_factory=list)
    errors: list[dict[str, Any]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate_counts(self) -> "BatchResult[T]":
        if self.succeeded + self.failed != self.total:
            self.total = self.succeeded + self.failed
        return self


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthStatus(BaseModel):
    """Service health check result."""

    status: str = Field(
        ...,
        description="Overall status: healthy | degraded | unhealthy",
    )
    version: str = Field(default="1.0.0", description="Application semver.")
    uptime: float = Field(
        default=0.0,
        ge=0,
        description="Seconds since application startup.",
    )
    checks: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-dependency health status.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%S.%f"
        )[:-3]
        + "Z",
    )


class ServiceInfo(BaseModel):
    """Metadata about a running service instance."""

    name: str = Field(default="govops-platform", description="Service name.")
    version: str = Field(default="1.0.0", description="Semver version.")
    environment: str = Field(default="development", description="Deployment environment.")
    instance_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique instance identifier.",
    )
    started_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 startup timestamp.",
    )


# ---------------------------------------------------------------------------
# Governance-specific configuration models
# ---------------------------------------------------------------------------

class CycleSeverity(str, Enum):
    """Governance cycle severity thresholds."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class GovernanceCycleConfig(BaseModel):
    """Configuration for a governance cycle run."""

    model_config = ConfigDict(str_strip_whitespace=True)

    name: str = Field(..., min_length=1, max_length=200, description="Cycle display name.")
    description: str = Field(default="", max_length=2000, description="Cycle description.")
    modules: list[str] = Field(
        default_factory=list,
        description="List of module IDs to include in the cycle.",
    )
    severity_threshold: CycleSeverity = Field(
        default=CycleSeverity.WARNING,
        description="Minimum severity that triggers enforcement.",
    )
    auto_enforce: bool = Field(
        default=False,
        description="Whether to automatically enforce findings above threshold.",
    )
    max_duration_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Maximum cycle duration in seconds.",
    )
    tags: dict[str, str] = Field(
        default_factory=dict,
        description="Arbitrary key-value tags for filtering.",
    )


class ScanConfig(BaseModel):
    """Configuration for a compliance scan."""

    model_config = ConfigDict(str_strip_whitespace=True)

    target: str = Field(..., min_length=1, description="Scan target identifier.")
    scan_type: str = Field(
        default="full",
        description="Scan type: full | incremental | targeted.",
    )
    include_patterns: list[str] = Field(
        default_factory=list,
        description="Glob patterns of resources to include.",
    )
    exclude_patterns: list[str] = Field(
        default_factory=list,
        description="Glob patterns of resources to exclude.",
    )
    timeout_seconds: int = Field(
        default=600,
        ge=30,
        le=7200,
        description="Scan timeout in seconds.",
    )
    parallel_workers: int = Field(
        default=4,
        ge=1,
        le=32,
        description="Number of parallel scan workers.",
    )


class EnforcementConfig(BaseModel):
    """Configuration for an enforcement action."""

    model_config = ConfigDict(str_strip_whitespace=True)

    mode: str = Field(
        default="dry_run",
        description="Enforcement mode: dry_run | warn | enforce.",
    )
    auto_remediate: bool = Field(
        default=False,
        description="Attempt automatic remediation of findings.",
    )
    require_approval: bool = Field(
        default=True,
        description="Require human approval before enforcement.",
    )
    notification_channels: list[str] = Field(
        default_factory=list,
        description="Channels to notify on enforcement actions.",
    )
    rollback_on_failure: bool = Field(
        default=True,
        description="Rollback changes if enforcement fails.",
    )


# ---------------------------------------------------------------------------
# Audit log entry
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    """Immutable audit log record with tamper-evidence hash."""

    actor: str = Field(..., description="User ID or service principal.")
    action: str = Field(..., description="Verb describing the action.")
    resource: str = Field(..., description="Resource identifier.")
    result: str = Field(default="success", description="Outcome: success | failure | partial.")
    hash: str = Field(default="", description="SHA-256 hex digest for tamper evidence.")
    request_id: str = Field(default="", description="Correlation ID.")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    details: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _compute_hash(self) -> "AuditLogEntry":
        if not self.hash:
            canonical = (
                f"{self.actor}|{self.action}|{self.resource}|"
                f"{self.result}|{self.timestamp}|{self.request_id}"
            )
            self.hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "GovOpsBaseModel",
    "TimestampMixin",
    "AuditMixin",
    "PaginatedResponse",
    "BatchResult",
    "HealthStatus",
    "ServiceInfo",
    "CycleSeverity",
    "GovernanceCycleConfig",
    "ScanConfig",
    "EnforcementConfig",
    "AuditLogEntry",
]
