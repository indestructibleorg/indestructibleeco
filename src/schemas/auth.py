"""Authentication schemas — API Key management and user roles.

URI: indestructibleeco://src/schemas/auth

Contracts defined by: tests/unit/test_auth.py, tests/unit/test_schemas.py
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""

    name: str
    role: UserRole = UserRole.DEVELOPER
    rate_limit_per_minute: int = 60
    expires_in_days: Optional[int] = None


class APIKeyInfo(BaseModel):
    """Metadata about an existing API key (never exposes the raw key)."""

    key_id: str
    name: str
    role: UserRole
    is_active: bool = True
    rate_limit_per_minute: int = 60
    total_requests: int = 0
    created_at: str = ""


class APIKeyResult(BaseModel):
    """Returned once on key creation — contains the raw key + info."""

    key: str
    info: APIKeyInfo