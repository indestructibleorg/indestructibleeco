"""Shared utility functions — datetime, pagination, hashing, serialization."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any


# --- ID Generation ---

def generate_id() -> str:
    """Generate a UUID4 string."""
    return str(uuid.uuid4())


def generate_short_id(prefix: str = "") -> str:
    """Generate a short prefixed ID (e.g., 'usr-a1b2c3d4')."""
    short = uuid.uuid4().hex[:8]
    return f"{prefix}-{short}" if prefix else short


# --- DateTime ---

def utc_now() -> datetime:
    """Current UTC datetime (timezone-aware)."""
    return datetime.now(timezone.utc)


def to_iso(dt: datetime | None) -> str | None:
    """Convert datetime to ISO 8601 string."""
    return dt.isoformat() if dt else None


def from_iso(iso_str: str) -> datetime:
    """Parse ISO 8601 string to datetime."""
    return datetime.fromisoformat(iso_str)


# --- Hashing ---

def sha256_hex(data: str) -> str:
    """SHA-256 hex digest of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def md5_hex(data: str) -> str:
    """MD5 hex digest (non-cryptographic, for checksums only)."""
    return hashlib.md5(data.encode("utf-8")).hexdigest()


# --- Pagination ---

def paginate_params(skip: int = 0, limit: int = 20, max_limit: int = 100) -> tuple[int, int]:
    """Sanitize pagination parameters."""
    skip = max(0, skip)
    limit = max(1, min(limit, max_limit))
    return skip, limit


def paginate_response(items: list[Any], total: int, skip: int, limit: int) -> dict[str, Any]:
    """Build a standard paginated response dict."""
    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_next": (skip + limit) < total,
        "total_pages": max(1, -(-total // limit)),
    }


# --- String Helpers ---

def truncate(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max_length with suffix."""
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    parts = name.split("_")
    return parts[0] + "".join(p.capitalize() for p in parts[1:])


def camel_to_snake(name: str) -> str:
    """Convert camelCase to snake_case."""
    import re
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


# --- Dict Helpers ---

def compact_dict(d: dict[str, Any]) -> dict[str, Any]:
    """Remove None values from a dict."""
    return {k: v for k, v in d.items() if v is not None}


def deep_merge(base: dict, override: dict) -> dict:
    """Deep merge two dicts, override takes precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


__all__ = [
    "generate_id", "generate_short_id",
    "utc_now", "to_iso", "from_iso",
    "sha256_hex", "md5_hex",
    "paginate_params", "paginate_response",
    "truncate", "snake_to_camel", "camel_to_snake",
    "compact_dict", "deep_merge",
]