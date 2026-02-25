"""SQLAlchemy repository implementations -- infrastructure adapters for domain ports.

Each repository:
* Accepts an ``AsyncSession`` (unit-of-work boundary managed by the caller).
* Converts between ORM models and rich domain entities.
* Enforces optimistic concurrency via the ``version`` column.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete as sa_delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.ai_expert import AIExpert, ExpertDomain, ExpertStatus
from src.domain.entities.quantum_job import JobStatus, QuantumAlgorithm, QuantumJob
from src.domain.entities.user import Email, HashedPassword, User, UserRole, UserStatus
from src.domain.repositories import QuantumJobRepository, UserRepository
from src.infrastructure.persistence.models import (
    AIExpertModel,
    QuantumJobModel,
    UserModel,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OptimisticLockError(Exception):
    """Raised when a concurrent modification is detected via version mismatch."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            f"Optimistic lock conflict on {entity_type} id={entity_id}. "
            "The entity was modified by another transaction."
        )


class EntityNotFoundError(Exception):
    """Raised when a required entity does not exist."""

    def __init__(self, entity_type: str, entity_id: str) -> None:
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(f"{entity_type} with id={entity_id} not found.")


class EntityAlreadyExistsError(Exception):
    """Raised when inserting an entity that violates a uniqueness constraint."""

    def __init__(self, entity_type: str, field: str, value: str) -> None:
        self.entity_type = entity_type
        self.field = field
        self.value = value
        super().__init__(
            f"{entity_type} with {field}={value!r} already exists."
        )


# ===================================================================
# SQLAlchemyUserRepository
# ===================================================================

class SQLAlchemyUserRepository(UserRepository):
    """Concrete ``UserRepository`` backed by PostgreSQL via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def find_by_id(self, entity_id: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_username(self, username: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == email.lower())
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists(self, entity_id: str) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(UserModel).where(
                UserModel.id == entity_id,
            )
        )
        return (result.scalar() or 0) > 0

    async def count(self) -> int:
        result = await self._session.execute(
            select(func.count()).select_from(UserModel)
        )
        return result.scalar() or 0

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 20,
        search: str | None = None,
    ) -> tuple[list[User], int]:
        base_filter = []

        if search:
            search_pattern = f"%{search}%"
            base_filter.append(
                or_(
                    UserModel.username.ilike(search_pattern),
                    UserModel.email.ilike(search_pattern),
                    UserModel.full_name.ilike(search_pattern),
                )
            )

        # Total count
        count_q = select(func.count()).select_from(UserModel)
        if base_filter:
            count_q = count_q.where(*base_filter)
        total = (await self._session.execute(count_q)).scalar() or 0

        # Page
        query = select(UserModel)
        if base_filter:
            query = query.where(*base_filter)
        query = query.order_by(UserModel.created_at.desc()).offset(skip).limit(limit)

        result = await self._session.execute(query)
        models = result.scalars().all()
        return [self._to_entity(m) for m in models], total

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def save(self, entity: User) -> User:  # type: ignore[override]
        """Insert a new user. Raises on duplicate id / username / email."""
        existing = await self._session.get(UserModel, entity.id)
        if existing is not None:
            raise EntityAlreadyExistsError("User", "id", entity.id)

        dup_username = await self.find_by_username(entity.username)
        if dup_username is not None:
            raise EntityAlreadyExistsError("User", "username", entity.username)

        email_str = entity.email.value if isinstance(entity.email, Email) else str(entity.email)
        dup_email = await self.find_by_email(email_str)
        if dup_email is not None:
            raise EntityAlreadyExistsError("User", "email", email_str)

        model = self._to_model(entity)
        self._session.add(model)
        await self._session.flush()
        return entity

    async def update(self, entity: User) -> User:  # type: ignore[override]
        """Update an existing user with optimistic concurrency control.

        The UPDATE only matches the row when the persisted ``version`` equals
        the *previous* version the caller read (entity.version - 1 is NOT used;
        instead the caller is expected to have already incremented via
        ``increment_version``).  We compare against the DB row's current
        version being one less than the entity version the caller passes.
        """
        email_str = entity.email.value if isinstance(entity.email, Email) else str(entity.email)
        pwd_str = (
            entity.hashed_password.value
            if isinstance(entity.hashed_password, HashedPassword)
            else str(entity.hashed_password)
        )
        role_str = entity.role.value if isinstance(entity.role, UserRole) else str(entity.role)
        status_str = entity.status.value if isinstance(entity.status, UserStatus) else str(entity.status)

        expected_version = entity.version - 1 if entity.version > 0 else 0

        stmt = (
            update(UserModel)
            .where(
                UserModel.id == entity.id,
                UserModel.version == expected_version,
            )
            .values(
                username=entity.username,
                email=email_str,
                hashed_password=pwd_str,
                full_name=entity.full_name,
                role=role_str,
                status=status_str,
                permissions=entity.permissions,
                last_login_at=entity.last_login_at,
                failed_login_attempts=entity.failed_login_attempts,
                locked_until=entity.locked_until,
                version=entity.version,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            # Either entity was deleted or version has diverged.
            exists = await self.exists(entity.id)
            if not exists:
                raise EntityNotFoundError("User", entity.id)
            raise OptimisticLockError("User", entity.id)

        await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> None:
        stmt = sa_delete(UserModel).where(UserModel.id == entity_id)
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise EntityNotFoundError("User", entity_id)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=Email(value=model.email),
            hashed_password=HashedPassword(value=model.hashed_password),
            full_name=model.full_name,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            permissions=model.permissions or [],
            last_login_at=model.last_login_at,
            failed_login_attempts=model.failed_login_attempts,
            locked_until=model.locked_until,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        email_str = entity.email.value if isinstance(entity.email, Email) else str(entity.email)
        pwd_str = (
            entity.hashed_password.value
            if isinstance(entity.hashed_password, HashedPassword)
            else str(entity.hashed_password)
        )
        role_str = entity.role.value if isinstance(entity.role, UserRole) else str(entity.role)
        status_str = entity.status.value if isinstance(entity.status, UserStatus) else str(entity.status)

        return UserModel(
            id=entity.id,
            username=entity.username,
            email=email_str,
            hashed_password=pwd_str,
            full_name=entity.full_name,
            role=role_str,
            status=status_str,
            permissions=entity.permissions,
            last_login_at=entity.last_login_at,
            failed_login_attempts=entity.failed_login_attempts,
            locked_until=entity.locked_until,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


# ===================================================================
# SQLAlchemyQuantumJobRepository
# ===================================================================

class SQLAlchemyQuantumJobRepository(QuantumJobRepository):
    """Concrete ``QuantumJobRepository`` backed by PostgreSQL via SQLAlchemy async."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    async def find_by_id(self, entity_id: str) -> QuantumJob | None:
        result = await self._session.execute(
            select(QuantumJobModel).where(QuantumJobModel.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists(self, entity_id: str) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(QuantumJobModel).where(
                QuantumJobModel.id == entity_id,
            )
        )
        return (result.scalar() or 0) > 0

    async def find_by_status(self, status: str, limit: int = 50) -> list[QuantumJob]:
        result = await self._session.execute(
            select(QuantumJobModel)
            .where(QuantumJobModel.status == status)
            .order_by(QuantumJobModel.submitted_at.desc())
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def find_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 20,
    ) -> list[QuantumJob]:
        result = await self._session.execute(
            select(QuantumJobModel)
            .where(QuantumJobModel.user_id == user_id)
            .order_by(QuantumJobModel.submitted_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    async def save(self, entity: QuantumJob) -> QuantumJob:  # type: ignore[override]
        """Insert *or* update a quantum job (upsert semantics).

        * If the job does not yet exist in the DB it is inserted.
        * If the job already exists, an optimistic-concurrency-controlled
          update is performed.
        """
        existing = await self._session.get(QuantumJobModel, entity.id)
        if existing is None:
            model = self._to_model(entity)
            self._session.add(model)
            await self._session.flush()
            return entity

        # --- optimistic update ------------------------------------------------
        expected_version = entity.version - 1 if entity.version > 0 else 0

        stmt = (
            update(QuantumJobModel)
            .where(
                QuantumJobModel.id == entity.id,
                QuantumJobModel.version == expected_version,
            )
            .values(
                user_id=entity.user_id,
                algorithm=entity.algorithm.value
                if isinstance(entity.algorithm, QuantumAlgorithm)
                else str(entity.algorithm),
                backend=entity.backend,
                status=entity.status.value
                if isinstance(entity.status, JobStatus)
                else str(entity.status),
                num_qubits=entity.num_qubits,
                shots=entity.shots,
                parameters=entity.parameters,
                result=entity.result,
                error_message=entity.error_message,
                execution_time_ms=entity.execution_time_ms,
                submitted_at=entity.submitted_at,
                started_at=entity.started_at,
                completed_at=entity.completed_at,
                version=entity.version,
                updated_at=datetime.now(timezone.utc),
            )
        )
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise OptimisticLockError("QuantumJob", entity.id)

        await self._session.flush()
        return entity

    async def delete(self, entity_id: str) -> None:
        stmt = sa_delete(QuantumJobModel).where(QuantumJobModel.id == entity_id)
        result = await self._session.execute(stmt)
        if result.rowcount == 0:
            raise EntityNotFoundError("QuantumJob", entity_id)
        await self._session.flush()

    # ------------------------------------------------------------------
    # Mappers
    # ------------------------------------------------------------------

    @staticmethod
    def _to_entity(model: QuantumJobModel) -> QuantumJob:
        return QuantumJob(
            id=model.id,
            user_id=model.user_id,
            algorithm=QuantumAlgorithm(model.algorithm),
            backend=model.backend,
            status=JobStatus(model.status),
            num_qubits=model.num_qubits,
            shots=model.shots,
            parameters=model.parameters or {},
            result=model.result or {},
            error_message=model.error_message,
            execution_time_ms=model.execution_time_ms,
            submitted_at=model.submitted_at,
            started_at=model.started_at,
            completed_at=model.completed_at,
            version=model.version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: QuantumJob) -> QuantumJobModel:
        algo_str = (
            entity.algorithm.value
            if isinstance(entity.algorithm, QuantumAlgorithm)
            else str(entity.algorithm)
        )
        status_str = (
            entity.status.value
            if isinstance(entity.status, JobStatus)
            else str(entity.status)
        )

        return QuantumJobModel(
            id=entity.id,
            user_id=entity.user_id,
            algorithm=algo_str,
            backend=entity.backend,
            status=status_str,
            num_qubits=entity.num_qubits,
            shots=entity.shots,
            parameters=entity.parameters,
            result=entity.result,
            error_message=entity.error_message,
            execution_time_ms=entity.execution_time_ms,
            submitted_at=entity.submitted_at,
            started_at=entity.started_at,
            completed_at=entity.completed_at,
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )


__all__ = [
    "OptimisticLockError",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "SQLAlchemyUserRepository",
    "SQLAlchemyQuantumJobRepository",
]
