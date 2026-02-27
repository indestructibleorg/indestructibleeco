"""Common Pydantic schema validators and reusable field types.

These building-block schemas are designed to be composed into request/response
models across the presentation layer.  They enforce consistent validation
rules for IDs, emails, pagination, sorting, and date-range filtering.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# ID field (UUID)
# ---------------------------------------------------------------------------

class IDField(BaseModel):
    """Validated UUID identifier.

    Accepts both hyphenated (``550e8400-...``) and non-hyphenated
    (``550e8400...``) UUID strings and normalises to the standard
    hyphenated lower-case form.
    """

    id: str = Field(..., description="UUID identifier.")

    @field_validator("id")
    @classmethod
    def validate_uuid(cls, v: str) -> str:
        try:
            return str(uuid.UUID(v))
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid UUID format: {v!r}") from exc


# ---------------------------------------------------------------------------
# Email field
# ---------------------------------------------------------------------------

# RFC-5321-ish pattern: good enough for UI validation; real verification
# requires an SMTP handshake.
_EMAIL_PATTERN = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)


class EmailField(BaseModel):
    """Validated and normalised email address.

    The address is stripped of surrounding whitespace and lower-cased to
    guarantee consistent storage and look-up.
    """

    email: str = Field(..., max_length=254, description="Valid email address.")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        normalised = v.strip().lower()
        if not _EMAIL_PATTERN.match(normalised):
            raise ValueError(f"Invalid email address: {normalised!r}")
        if len(normalised) > 254:
            raise ValueError("Email address exceeds maximum length of 254 characters")
        return normalised


# ---------------------------------------------------------------------------
# Pagination parameters
# ---------------------------------------------------------------------------

class PaginationParams(BaseModel):
    """Query-string pagination parameters with safe defaults and bounds.

    ``skip`` defaults to **0**; ``limit`` defaults to **20** and is clamped
    to the range [1, 100].
    """

    skip: int = Field(default=0, ge=0, description="Number of records to skip.")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum records to return.")

    @field_validator("skip")
    @classmethod
    def clamp_skip(cls, v: int) -> int:
        return max(0, v)

    @field_validator("limit")
    @classmethod
    def clamp_limit(cls, v: int) -> int:
        return max(1, min(v, 100))

    @property
    def offset(self) -> int:
        """Alias for ``skip`` (useful with SQL OFFSET)."""
        return self.skip


# ---------------------------------------------------------------------------
# Sort parameters
# ---------------------------------------------------------------------------

class SortDirection(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"


class SortParams(BaseModel):
    """Sort specification.

    ``field`` names the column/attribute; ``direction`` is ``asc`` or
    ``desc``.  A whitelist of allowed sort fields can be enforced at the
    use-case level.
    """

    field: str = Field(
        default="created_at",
        min_length=1,
        max_length=64,
        description="Field name to sort by.",
    )
    direction: SortDirection = Field(
        default=SortDirection.DESC,
        description="Sort direction: asc or desc.",
    )

    @field_validator("field")
    @classmethod
    def validate_field_name(cls, v: str) -> str:
        """Prevent SQL injection via the sort field name.

        Only alphanumeric characters, underscores, and dots are allowed.
        """
        cleaned = v.strip()
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_.]*$", cleaned):
            raise ValueError(
                f"Invalid sort field name: {cleaned!r}. "
                "Only letters, digits, underscores, and dots are permitted."
            )
        return cleaned

    @property
    def is_ascending(self) -> bool:
        return self.direction == SortDirection.ASC

    @property
    def sql_direction(self) -> str:
        """Return the SQL keyword for the current direction."""
        return "ASC" if self.is_ascending else "DESC"


# ---------------------------------------------------------------------------
# Date-range filter
# ---------------------------------------------------------------------------

class DateRangeFilter(BaseModel):
    """Inclusive date-range filter.

    Both ``start`` and ``end`` are optional; omitting one side creates an
    open-ended range.  When both are supplied, ``start`` must not be later
    than ``end``.
    """

    start: datetime | None = Field(
        default=None,
        description="Inclusive lower bound (UTC).",
    )
    end: datetime | None = Field(
        default=None,
        description="Inclusive upper bound (UTC).",
    )

    @field_validator("start", "end", mode="before")
    @classmethod
    def parse_datetime(cls, v: Any) -> Any:
        """Accept ISO-8601 strings as well as native datetime objects."""
        if v is None:
            return v
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace("Z", "+00:00"))
            except ValueError as exc:
                raise ValueError(f"Invalid datetime format: {v!r}") from exc
        return v

    @model_validator(mode="after")
    def validate_range(self) -> "DateRangeFilter":
        if self.start is not None and self.end is not None:
            if self.start > self.end:
                raise ValueError(
                    f"'start' ({self.start.isoformat()}) must not be after "
                    f"'end' ({self.end.isoformat()})."
                )
        return self

    @property
    def is_bounded(self) -> bool:
        """True when both bounds are specified."""
        return self.start is not None and self.end is not None

    @property
    def is_open(self, encoding='utf-8') -> bool:
        """True when neither bound is specified."""
        return self.start is None and self.end is None


# ---------------------------------------------------------------------------
# Backward-compatible re-exports
# ---------------------------------------------------------------------------

class BaseResponse(BaseModel):
    """Standard API response wrapper (light version for schema layer)."""

    success: bool = True
    data: Any = None
    message: str = ""


class ErrorSchema(BaseModel):
    """Standard error response (light version for schema layer)."""

    code: str
    message: str
    details: list[dict[str, Any]] = Field(default_factory=list)


class BatchOperationResult(BaseModel):
    """Result of a batch operation."""

    total: int
    succeeded: int
    failed: int
    errors: list[dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

__all__ = [
    "IDField",
    "EmailField",
    "PaginationParams",
    "SortDirection",
    "SortParams",
    "DateRangeFilter",
    # Backward-compatible
    "BaseResponse",
    "ErrorSchema",
    "BatchOperationResult",
]
