import uuid
from datetime import datetime, timezone
from typing import List, Optional, Type, TypeVar

from sqlalchemy import delete as sa_delete
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.quantum_job import QuantumJob, QuantumAlgorithm, JobStatus
from src.domain.entities.user import User
from src.domain.entities.ai_expert import AIExpert
from src.domain.repositories import (
    AIExpertRepository,
    QuantumJobRepository,
    UserRepository,
)
from src.domain.value_objects.email import Email
from src.infrastructure.persistence.models import (
    AIExpertModel,
    QuantumJobModel,
    UserModel,
)

T = TypeVar("T")

class OptimisticLockError(Exception):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"Optimistic lock failure for {entity_type} with ID {entity_id}")

class EntityNotFoundError(Exception):
    def __init__(self, entity_type: str, entity_id: str):
        super().__init__(f"{entity_type} with ID {entity_id} not found")

class EntityAlreadyExistsError(Exception):
    def __init__(self, entity_type: str, identity: str):
        super().__init__(f"{entity_type} with identity {identity} already exists")

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def get_by_email(self, email: Email) -> Optional[User]:
        result = await self._session.execute(
            select(UserModel).where(UserModel.email == str(email))
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def exists(self, email: Email) -> bool:
        result = await self._session.execute(
            select(UserModel.id).where(UserModel.email == str(email))
        )
        return result.scalar_one_or_none() is not None

    async def save(self, user: User) -> User:
        existing = await self._session.get(UserModel, user.id)
        if existing is None:
            model = self._to_model(user)
            self._session.add(model)
        else:
            existing.username = user.username
            existing.email = str(user.email)
            existing.is_active = user.is_active
            existing.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return user

    @staticmethod
    def _to_entity(model: UserModel) -> User:
        return User(
            id=model.id,
            username=model.username,
            email=Email(model.email),
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: User) -> UserModel:
        return UserModel(
            id=entity.id,
            username=entity.username,
            email=str(entity.email),
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

class SQLAlchemyQuantumJobRepository(QuantumJobRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, job_id: str) -> Optional[QuantumJob]:
        result = await self._session.execute(
            select(QuantumJobModel).where(QuantumJobModel.id == job_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_by_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[QuantumJob]:
        result = await self._session.execute(
            select(QuantumJobModel)
            .where(QuantumJobModel.user_id == user_id)
            .order_by(QuantumJobModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def save(self, entity: QuantumJob) -> QuantumJob:
        existing = await self._session.get(QuantumJobModel, entity.id)
        if existing is None:
            model = self._to_model(entity)
            self._session.add(model)
            await self._session.flush()
            return entity
        
        expected_version = entity.version - 1 if entity.version > 0 else 0
        stmt = (
            update(QuantumJobModel)
            .where(
                QuantumJobModel.id == entity.id,
                QuantumJobModel.version == expected_version,
            )
            .values(
                user_id=entity.user_id,
                algorithm=entity.algorithm.value if isinstance(entity.algorithm, QuantumAlgorithm) else str(entity.algorithm),
                backend=entity.backend,
                status=entity.status.value if isinstance(entity.status, JobStatus) else str(entity.status),
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
        return QuantumJobModel(
            id=entity.id,
            user_id=entity.user_id,
            algorithm=entity.algorithm.value if isinstance(entity.algorithm, QuantumAlgorithm) else str(entity.algorithm),
            backend=entity.backend,
            status=entity.status.value if isinstance(entity.status, JobStatus) else str(entity.status),
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

class SQLAlchemyAIExpertRepository(AIExpertRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_by_id(self, expert_id: str) -> Optional[AIExpert]:
        result = await self._session.execute(
            select(AIExpertModel).where(AIExpertModel.id == expert_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def save(self, expert: AIExpert) -> AIExpert:
        existing = await self._session.get(AIExpertModel, expert.id)
        if existing is None:
            model = self._to_model(expert)
            self._session.add(model)
        else:
            existing.name = expert.name
            existing.specialty = expert.specialty
            existing.bio = expert.bio
            existing.updated_at = datetime.now(timezone.utc)
        await self._session.flush()
        return expert

    @staticmethod
    def _to_entity(model: AIExpertModel) -> AIExpert:
        return AIExpert(
            id=model.id,
            name=model.name,
            specialty=model.specialty,
            bio=model.bio,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    @staticmethod
    def _to_model(entity: AIExpert) -> AIExpertModel:
        return AIExpertModel(
            id=entity.id,
            name=entity.name,
            specialty=entity.specialty,
            bio=entity.bio,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

__all__ = [
    "OptimisticLockError",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "SQLAlchemyUserRepository",
    "SQLAlchemyQuantumJobRepository",
    "SQLAlchemyAIExpertRepository",
]
