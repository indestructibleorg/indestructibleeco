"""User aggregate root with complete DDD implementation."""
from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import Field, field_validator

from .base import AggregateRoot, DomainEvent, ValueObject


class Email(ValueObject):
    value: str

    @field_validator("value")
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, v):
            raise ValueError(f"Invalid email format: {v}")
        return v.lower()


class HashedPassword(ValueObject):
    value: str

    @field_validator("value")
    @classmethod
    def validate_not_empty(cls, v: str) -> str:
        if not v or len(v) < 10:
            raise ValueError("Hashed password cannot be empty or too short")
        return v


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"
    SCIENTIST = "scientist"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


# --- Domain Events ---
class UserCreated(DomainEvent):
    event_type: str = "user.created"
    aggregate_type: str = "User"

class UserActivated(DomainEvent):
    event_type: str = "user.activated"
    aggregate_type: str = "User"

class UserSuspended(DomainEvent):
    event_type: str = "user.suspended"
    aggregate_type: str = "User"

class UserRoleChanged(DomainEvent):
    event_type: str = "user.role_changed"
    aggregate_type: str = "User"

class UserPasswordChanged(DomainEvent):
    event_type: str = "user.password_changed"
    aggregate_type: str = "User"


class User(AggregateRoot):
    """User aggregate root."""

    username: str = Field(..., min_length=3, max_length=50)
    email: Email
    hashed_password: HashedPassword
    full_name: str = Field(default="", max_length=200)
    role: UserRole = UserRole.VIEWER
    status: UserStatus = UserStatus.PENDING_VERIFICATION
    permissions: list[str] = Field(default_factory=list)
    last_login_at: datetime | None = None
    failed_login_attempts: int = Field(default=0, ge=0)
    locked_until: datetime | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain alphanumeric, underscore, and hyphen")
        return v

    @classmethod
    def create(cls, username: str, email: Any, hashed_password: Any, full_name: str = "", role: UserRole = UserRole.VIEWER) -> User:
        # Accept both raw strings and value objects (Email / HashedPassword)
        email_str = email.value if hasattr(email, "value") else email
        pwd_str = hashed_password.value if hasattr(hashed_password, "value") else hashed_password
        user = cls(
            username=username,
            email=Email(value=email_str),
            hashed_password=HashedPassword(value=pwd_str),
            full_name=full_name,
            role=role,
        )
        user.raise_event(UserCreated(aggregate_id=user.id, payload={"username": username, "email": email_str, "role": role.value}))
        return user

    def activate(self) -> None:
        if self.status == UserStatus.ACTIVE:
            return
        self.status = UserStatus.ACTIVE
        self.increment_version()
        self.raise_event(UserActivated(aggregate_id=self.id, payload={"username": self.username}))

    def suspend(self, reason: str = "") -> None:
        self.status = UserStatus.SUSPENDED
        self.increment_version()
        self.raise_event(UserSuspended(aggregate_id=self.id, payload={"username": self.username, "reason": reason}))

    def change_role(self, new_role: UserRole) -> None:
        old_role = self.role
        self.role = new_role
        self.increment_version()
        self.raise_event(UserRoleChanged(aggregate_id=self.id, payload={"old_role": old_role.value, "new_role": new_role.value}))

    def change_password(self, new_hashed_password: str) -> None:
        self.hashed_password = HashedPassword(value=new_hashed_password)
        self.failed_login_attempts = 0
        self.locked_until = None
        self.increment_version()
        self.raise_event(UserPasswordChanged(aggregate_id=self.id, payload={"username": self.username}))

    def record_login_success(self) -> None:
        self.last_login_at = datetime.now(timezone.utc)
        self.failed_login_attempts = 0
        self.locked_until = None

    def record_login_failure(self, max_attempts: int = 5) -> None:
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            from datetime import timedelta
            self.locked_until = datetime.now(timezone.utc) + timedelta(minutes=30)

    @property
    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return datetime.now(timezone.utc) < self.locked_until

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and not self.is_locked

    def has_permission(self, permission: str) -> bool:
        if self.role == UserRole.ADMIN:
            return True
        return permission in self.permissions

    def grant_permission(self, permission: str) -> None:
        if permission not in self.permissions:
            self.permissions.append(permission)
            self.increment_version()

    def revoke_permission(self, permission: str) -> None:
        if permission in self.permissions:
            self.permissions.remove(permission)
            self.increment_version()