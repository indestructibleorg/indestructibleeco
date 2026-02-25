"""User management use cases — orchestrate domain logic through repository ports."""
from __future__ import annotations

from typing import Any

import structlog

from src.application.dto import UserDTO, TokenDTO, PaginatedDTO
from src.application.events import get_event_bus
from src.application.services import AuthService
from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.events import (
    UserActivatedEvent,
    UserAuthenticatedEvent,
    UserAuthFailedEvent,
    UserCreatedEvent,
    UserDeletedEvent,
    UserSuspendedEvent,
    UserUpdatedEvent,
)
from src.domain.exceptions import (
    AuthenticationException,
    EntityNotFoundException,
    EntityAlreadyExistsException,
)
from src.domain.repositories import UserRepository
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword

logger = structlog.get_logger(__name__)


class CreateUserUseCase:
    """Register a new user."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._auth = AuthService()
        self._bus = get_event_bus()

    async def execute(self, username: str, email: str, password: str, full_name: str, role: str) -> dict[str, Any]:
        email_vo = Email.create(email)
        hashed = HashedPassword.from_plain(password)

        user = User.create(
            username=username,
            email=email_vo,
            hashed_password=hashed,
            full_name=full_name,
            role=UserRole(role),
        )

        saved = await self._repo.save(user)

        event = UserCreatedEvent(
            aggregate_id=saved.id,
            payload={"username": username, "email": email_vo.value, "role": role},
        )
        saved.raise_event(event)
        await self._bus.publish_all(saved.collect_events())

        logger.info("user_created", user_id=saved.id, username=username)
        return UserDTO.from_entity(saved).model_dump()


class AuthenticateUserUseCase:
    """Authenticate user and issue JWT tokens."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._auth = AuthService()
        self._bus = get_event_bus()

    async def execute(self, username: str, password: str) -> dict[str, Any]:
        user = await self._repo.find_by_username(username)
        if not user:
            await self._bus.publish(UserAuthFailedEvent(
                aggregate_id="unknown",
                payload={"username": username, "reason": "user_not_found"},
            ))
            raise AuthenticationException("Invalid credentials")

        pwd_value = user.hashed_password.value if hasattr(user.hashed_password, "value") else str(user.hashed_password)
        if not self._auth.verify_password(password, pwd_value):
            await self._bus.publish(UserAuthFailedEvent(
                aggregate_id=user.id,
                payload={"username": username, "reason": "invalid_password"},
            ))
            raise AuthenticationException("Invalid credentials")

        if hasattr(user.status, "value"):
            status_str = user.status.value
        else:
            status_str = str(user.status)

        if status_str != "active":
            raise AuthenticationException(f"Account is {status_str}")

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
        tokens = self._auth.create_tokens(user_id=user.id, username=user.username, role=role_str)

        await self._bus.publish(UserAuthenticatedEvent(
            aggregate_id=user.id,
            payload={"username": username},
        ))

        logger.info("user_authenticated", user_id=user.id)
        return tokens


class ListUsersUseCase:
    """List users with pagination and search."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, skip: int = 0, limit: int = 20, search: str | None = None) -> dict[str, Any]:
        users, total = await self._repo.list_users(skip=skip, limit=limit, search=search)
        items = [UserDTO.from_entity(u).model_dump() for u in users]
        return PaginatedDTO(items=items, total=total, skip=skip, limit=limit).model_dump()


class GetUserUseCase:
    """Get a single user by ID."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo

    async def execute(self, user_id: str) -> dict[str, Any]:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        return UserDTO.from_entity(user).model_dump()


class UpdateUserUseCase:
    """Update user profile fields."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._bus = get_event_bus()

    async def execute(self, user_id: str, **kwargs: Any) -> dict[str, Any]:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        changed_fields: dict[str, Any] = {}
        if "full_name" in kwargs and kwargs["full_name"] is not None:
            user.full_name = kwargs["full_name"]
            changed_fields["full_name"] = kwargs["full_name"]
        if "role" in kwargs and kwargs["role"] is not None:
            user.role = UserRole(kwargs["role"])
            changed_fields["role"] = kwargs["role"]

        user.increment_version()
        updated = await self._repo.update(user)

        await self._bus.publish(UserUpdatedEvent(
            aggregate_id=user.id,
            payload={"changed_fields": changed_fields},
        ))

        return UserDTO.from_entity(updated).model_dump()


class DeleteUserUseCase:
    """Soft-delete a user."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._bus = get_event_bus()

    async def execute(self, user_id: str) -> None:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        await self._repo.delete(user_id)

        await self._bus.publish(UserDeletedEvent(
            aggregate_id=user_id,
            payload={"username": user.username},
        ))
        logger.info("user_deleted", user_id=user_id)


class ActivateUserUseCase:
    """Reactivate a suspended user."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._bus = get_event_bus()

    async def execute(self, user_id: str) -> dict[str, Any]:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        user.activate()
        user.increment_version()
        updated = await self._repo.update(user)

        await self._bus.publish(UserActivatedEvent(
            aggregate_id=user_id,
            payload={"username": user.username},
        ))

        return UserDTO.from_entity(updated).model_dump()


class SuspendUserUseCase:
    """Suspend a user account."""

    def __init__(self, repo: UserRepository) -> None:
        self._repo = repo
        self._bus = get_event_bus()

    async def execute(self, user_id: str, reason: str = "") -> dict[str, Any]:
        user = await self._repo.find_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)

        user.suspend(reason)
        user.increment_version()
        updated = await self._repo.update(user)

        await self._bus.publish(UserSuspendedEvent(
            aggregate_id=user_id,
            payload={"username": user.username, "reason": reason},
        ))

        return UserDTO.from_entity(updated).model_dump()


__all__ = [
    "CreateUserUseCase",
    "AuthenticateUserUseCase",
    "ListUsersUseCase",
    "GetUserUseCase",
    "UpdateUserUseCase",
    "DeleteUserUseCase",
    "ActivateUserUseCase",
    "SuspendUserUseCase",
]