"""Domain events — immutable records of things that happened in the domain."""
from __future__ import annotations

from src.domain.entities.base import DomainEvent


class UserCreatedEvent(DomainEvent):
    """Raised when a new user is registered."""
    event_type: str = "user.created"
    aggregate_type: str = "User"


class UserUpdatedEvent(DomainEvent):
    """Raised when user profile is modified."""
    event_type: str = "user.updated"
    aggregate_type: str = "User"


class UserDeletedEvent(DomainEvent):
    """Raised when a user is soft-deleted."""
    event_type: str = "user.deleted"
    aggregate_type: str = "User"


class UserActivatedEvent(DomainEvent):
    """Raised when a suspended user is reactivated."""
    event_type: str = "user.activated"
    aggregate_type: str = "User"


class UserSuspendedEvent(DomainEvent):
    """Raised when a user account is suspended."""
    event_type: str = "user.suspended"
    aggregate_type: str = "User"


class UserAuthenticatedEvent(DomainEvent):
    """Raised on successful authentication."""
    event_type: str = "user.authenticated"
    aggregate_type: str = "User"


class UserAuthFailedEvent(DomainEvent):
    """Raised on failed authentication attempt."""
    event_type: str = "user.auth_failed"
    aggregate_type: str = "User"


class QuantumJobSubmittedEvent(DomainEvent):
    """Raised when a quantum job is submitted for execution."""
    event_type: str = "quantum.job_submitted"
    aggregate_type: str = "QuantumJob"


class QuantumJobCompletedEvent(DomainEvent):
    """Raised when a quantum job finishes execution."""
    event_type: str = "quantum.job_completed"
    aggregate_type: str = "QuantumJob"


class AIExpertCreatedEvent(DomainEvent):
    """Raised when a new AI expert is instantiated."""
    event_type: str = "ai.expert_created"
    aggregate_type: str = "AIExpert"


__all__ = [
    "UserCreatedEvent",
    "UserUpdatedEvent",
    "UserDeletedEvent",
    "UserActivatedEvent",
    "UserSuspendedEvent",
    "UserAuthenticatedEvent",
    "UserAuthFailedEvent",
    "QuantumJobSubmittedEvent",
    "QuantumJobCompletedEvent",
    "AIExpertCreatedEvent",
]