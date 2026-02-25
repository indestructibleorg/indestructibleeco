"""Domain repository interfaces (ports) — abstract contracts for persistence."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from src.domain.entities.base import AggregateRoot

T = TypeVar("T", bound=AggregateRoot)


class Repository(ABC, Generic[T]):
    """Base repository interface."""

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> T | None: ...

    @abstractmethod
    async def save(self, entity: T) -> T: ...

    @abstractmethod
    async def delete(self, entity_id: str) -> None: ...

    @abstractmethod
    async def exists(self, entity_id: str) -> bool: ...


class UserRepository(Repository):
    """User aggregate repository port."""

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Any | None: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> Any | None: ...

    @abstractmethod
    async def find_by_email(self, email: str) -> Any | None: ...

    @abstractmethod
    async def save(self, entity: Any) -> Any: ...

    @abstractmethod
    async def delete(self, entity_id: str) -> None: ...

    @abstractmethod
    async def exists(self, entity_id: str) -> bool: ...

    @abstractmethod
    async def list_users(
        self, skip: int = 0, limit: int = 20, search: str | None = None
    ) -> tuple[list[Any], int]: ...

    @abstractmethod
    async def count(self) -> int: ...

    @abstractmethod
    async def update(self, entity: Any) -> Any: ...


class QuantumJobRepository(Repository):
    """Quantum job repository port."""

    @abstractmethod
    async def find_by_id(self, entity_id: str) -> Any | None: ...

    @abstractmethod
    async def save(self, entity: Any) -> Any: ...

    @abstractmethod
    async def delete(self, entity_id: str) -> None: ...

    @abstractmethod
    async def exists(self, entity_id: str) -> bool: ...

    @abstractmethod
    async def find_by_status(self, status: str, limit: int = 50) -> list[Any]: ...

    @abstractmethod
    async def find_by_user(self, user_id: str, skip: int = 0, limit: int = 20) -> list[Any]: ...


__all__ = ["Repository", "UserRepository", "QuantumJobRepository"]