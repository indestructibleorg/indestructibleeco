"""Shared Pydantic models used across application layers.

Provides canonical response envelopes, pagination, health checks, audit
logging, and generic operation wrappers so that every API endpoint and
internal service speaks the same structural language.
"""
from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field, field_validator, model_validator

T = TypeVar("T")


# ---------------------------------------------------------------------------
# Base response envelope
# ---------------------------------------------------------------------------

class BaseResponse(BaseModel):
    """Standard API response wrapper.

    Every successful response carries ``success=True``, a UTC ISO-8601
    timestamp, and the ``request_id`` injected by middleware.
    """

    success: bool = True
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )
    request_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Correlation ID for tracing; normally set by middleware.",
    )


# ---------------------------------------------------------------------------
# Error response
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Single error detail entry (e.g. a field validation error)."""

    field: str = ""
    message: str = ""
    code: str = ""


class ErrorResponse(BaseModel):
    """Structured error response returned by exception handlers.

    ``details`` provides an ordered list of granular error descriptions
    (validation failures, sub-errors from batch operations, etc.).
    """

    code: str = Field(..., description="Machine-readable error code.")
    message: str = Field(..., description="Human-readable summary.")
    details: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Ordered list of granular error details.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )
    request_id: str = Field(
        default="",
        description="Correlation ID for tracing.",
    )


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

class PageRequest(BaseModel):
    """Standard pagination request parameters."""

    skip: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$")


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


# Keep backward-compatible alias
PageResponse = PaginatedResponse


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class HealthResponse(BaseModel):
    """Service health check result.

    ``checks`` maps dependency names (``database``, ``redis``, etc.) to a
    dict containing at minimum ``{"status": "healthy"|"unhealthy"}``.
    """

    status: str = Field(
        ...,
        description="Overall status: healthy | degraded | unhealthy",
        pattern=r"^(healthy|degraded|unhealthy)$",
    )
    version: str = Field(..., description="Application semver.")
    uptime: float = Field(
        ...,
        ge=0,
        description="Seconds since application startup.",
    )
    checks: dict[str, Any] = Field(
        default_factory=dict,
        description="Per-dependency health status.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
    )


# Backward-compatible alias
HealthStatus = HealthResponse


# ---------------------------------------------------------------------------
# Audit log
# ---------------------------------------------------------------------------

class AuditLogEntry(BaseModel):
    """Immutable audit log record.

    Every mutation that changes system state should emit an ``AuditLogEntry``
    with enough context to reconstruct *who* did *what*, *when*, and *where*.
    The ``hash`` field provides tamper-evidence (SHA-256 of the canonical
    payload).
    """

    actor: str = Field(..., description="User ID or service principal that performed the action.")
    action: str = Field(..., description="Verb describing the action (e.g. 'user.create').")
    resource: str = Field(..., description="Resource identifier (e.g. 'user:abc-123').")
    result: str = Field(
        default="success",
        description="Outcome: success | failure | partial.",
    )
    hash: str = Field(
        default="",
        description="SHA-256 hex digest for tamper evidence.",
    )
    version: str = Field(
        default="1",
        description="Schema version of this audit entry.",
    )
    request_id: str = Field(
        default="",
        description="Correlation ID tying the entry to a request.",
    )
    correlation_id: str = Field(
        default="",
        description="Cross-service correlation ID.",
    )
    ip: str = Field(
        default="",
        description="Client IP address.",
    )
    user_agent: str = Field(
        default="",
        description="Client User-Agent header.",
    )
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        description="RFC 3339 UTC timestamp.",
    )
    details: dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary additional context.",
    )

    @model_validator(mode="after")
    def _compute_hash(self) -> "AuditLogEntry":
        """Compute a tamper-evidence hash if one was not explicitly provided."""
        if not self.hash:
            canonical = (
                f"{self.actor}|{self.action}|{self.resource}|"
                f"{self.result}|{self.timestamp}|{self.request_id}"
            )
            self.hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return self


# Backward-compatible alias
AuditEntry = AuditLogEntry


# ---------------------------------------------------------------------------
# Generic operation result
# ---------------------------------------------------------------------------

class OperationResult(BaseModel):
    """Generic operation result wrapper (for internal service-to-service use)."""

    success: bool
    message: str = ""
    data: Any = None
    errors: list[str] = Field(default_factory=list)

    @classmethod
    def ok(cls, data: Any = None, message: str = "Success") -> "OperationResult":
        return cls(success=True, message=message, data=data)

    @classmethod
    def fail(cls, message: str, errors: list[str] | None = None) -> "OperationResult":
        return cls(success=False, message=message, errors=errors or [])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "BaseResponse",
    "ErrorDetail",
    "ErrorResponse",
    "PageRequest",
    "PaginatedResponse",
    "PageResponse",
    "HealthResponse",
    "HealthStatus",
    "AuditLogEntry",
    "AuditEntry",
    "OperationResult",
]
