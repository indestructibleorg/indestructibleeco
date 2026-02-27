"""Data Transfer Objects — layer boundary crossing types."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    """User data for cross-layer transfer."""
    id: str
    username: str
    email: str
    full_name: str
    role: str
    status: str
    created_at: str
    last_login_at: str | None = None
    login_count: int = 0

    @classmethod
    def from_entity(cls, entity: Any) -> UserDTO:
        email_str = entity.email.value if hasattr(entity.email, "value") else str(entity.email)
        role_str = entity.role.value if hasattr(entity.role, "value") else str(entity.role)
        status_str = entity.status.value if hasattr(entity.status, "value") else str(entity.status)
        created = entity.created_at.isoformat() if isinstance(entity.created_at, datetime) else str(entity.created_at)
        last_login = None
        if hasattr(entity, "last_login_at") and entity.last_login_at:
            last_login = entity.last_login_at.isoformat() if isinstance(entity.last_login_at, datetime) else str(entity.last_login_at)
        return cls(
            id=entity.id,
            username=entity.username,
            email=email_str,
            full_name=entity.full_name,
            role=role_str,
            status=status_str,
            created_at=created,
            last_login_at=last_login,
            login_count=getattr(entity, "login_count", 0),
        )


class TokenDTO(BaseModel):
    """Authentication token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class PaginatedDTO(BaseModel):
    """Generic paginated response."""
    items: list[Any]
    total: int
    skip: int
    limit: int

    @property
    def has_next(self) -> bool:
        return (self.skip + self.limit) < self.total

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0
        return -(-self.total // self.limit) if self.limit > 0 else 1


class QuantumJobDTO(BaseModel):
    """Quantum job result transfer."""
    job_id: str
    status: str
    algorithm: str = ""
    result: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    execution_time_ms: float = 0.0


__all__ = ["UserDTO", "TokenDTO", "PaginatedDTO", "QuantumJobDTO"]