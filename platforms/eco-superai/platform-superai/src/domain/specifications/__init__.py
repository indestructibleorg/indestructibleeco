"""Specification pattern — composable query predicates for domain filtering."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class Specification(ABC, Generic[T]):
    """Base specification interface."""

    @abstractmethod
    def is_satisfied_by(self, candidate: T) -> bool: ...

    def and_(self, other: Specification[T]) -> AndSpecification[T]:
        return AndSpecification(self, other)

    def or_(self, other: Specification[T]) -> OrSpecification[T]:
        return OrSpecification(self, other)

    def not_(self) -> NotSpecification[T]:
        return NotSpecification(self)


class AndSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) and self._right.is_satisfied_by(candidate)


class OrSpecification(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self._left = left
        self._right = right

    def is_satisfied_by(self, candidate: T) -> bool:
        return self._left.is_satisfied_by(candidate) or self._right.is_satisfied_by(candidate)


class NotSpecification(Specification[T]):
    def __init__(self, spec: Specification[T]) -> None:
        self._spec = spec

    def is_satisfied_by(self, candidate: T) -> bool:
        return not self._spec.is_satisfied_by(candidate)


# --- User Specifications ---

class ActiveUserSpecification(Specification):
    """Matches users with 'active' status."""
    def is_satisfied_by(self, candidate: Any) -> bool:
        return getattr(candidate, "status", None) == "active" or (
            hasattr(candidate, "status") and hasattr(candidate.status, "value") and candidate.status.value == "active"
        )


class UserByRoleSpecification(Specification):
    """Matches users with a specific role."""
    def __init__(self, role: str) -> None:
        self._role = role

    def is_satisfied_by(self, candidate: Any) -> bool:
        role = getattr(candidate, "role", None)
        if hasattr(role, "value"):
            return role.value == self._role
        return role == self._role


class UserByEmailDomainSpecification(Specification):
    """Matches users whose email belongs to a specific domain."""
    def __init__(self, domain: str) -> None:
        self._domain = domain.lower()

    def is_satisfied_by(self, candidate: Any) -> bool:
        email = getattr(candidate, "email", None)
        if email is None:
            return False
        email_str = email.value if hasattr(email, "value") else str(email)
        return email_str.lower().endswith(f"@{self._domain}")


__all__ = [
    "Specification",
    "AndSpecification",
    "OrSpecification",
    "NotSpecification",
    "ActiveUserSpecification",
    "UserByRoleSpecification",
    "UserByEmailDomainSpecification",
]