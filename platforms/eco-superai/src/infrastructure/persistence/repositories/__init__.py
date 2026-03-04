from typing import List, Optional
from sqlalchemy import select, exists as sql_exists
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.entities.ai_expert import AIExpert
from src.domain.entities.quantum_job import QuantumJob
from src.domain.value_objects.email import Email
from src.domain.repositories import UserRepository, AIExpertRepository, QuantumJobRepository
from src.infrastructure.persistence.models import UserModel, AIExpertModel, QuantumJobModel

class SQLAlchemyUserRepository(UserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: str) -> Optional[User]:
        result = await self.session.execute(select(UserModel).filter(UserModel.id == user_id))
        model = result.scalars().first()
        if not model:
            return None
        return User(
            id=model.id,
            username=model.username,
            email=Email(model.email),
            is_active=model.is_active,
            role=model.role,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def get_by_email(self, email: Email) -> Optional[User]:
        result = await self.session.execute(select(UserModel).filter(UserModel.email == str(email)))
        model = result.scalars().first()
        if not model:
            return None
        return User(
            id=model.id,
            username=model.username,
            email=Email(model.email),
            is_active=model.is_active,
            role=model.role,
            status=model.status,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def save(self, user: User) -> None:
        model = UserModel(
            id=user.id,
            username=user.username,
            email=str(user.email),
            is_active=user.is_active,
            role=user.role,
            status=user.status,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        await self.session.merge(model)

    async def exists(self, email: Email) -> bool:
        result = await self.session.execute(select(sql_exists().where(UserModel.email == str(email))))
        return result.scalar()

class SQLAlchemyAIExpertRepository(AIExpertRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, expert_id: str) -> Optional[AIExpert]:
        result = await self.session.execute(select(AIExpertModel).filter(AIExpertModel.id == expert_id))
        model = result.scalars().first()
        if not model:
            return None
        return AIExpert(
            id=model.id,
            name=model.name,
            specialty=model.specialty,
            bio=model.bio,
            status=model.status,
            domain=model.domain,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def save(self, expert: AIExpert) -> None:
        model = AIExpertModel(
            id=expert.id,
            name=expert.name,
            specialty=expert.specialty,
            bio=expert.bio,
            status=expert.status,
            domain=expert.domain,
            created_at=expert.created_at,
            updated_at=expert.updated_at
        )
        await self.session.merge(model)

class SQLAlchemyQuantumJobRepository(QuantumJobRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, job_id: str) -> Optional[QuantumJob]:
        result = await self.session.execute(select(QuantumJobModel).filter(QuantumJobModel.id == job_id))
        model = result.scalars().first()
        if not model:
            return None
        return QuantumJob(
            id=model.id,
            name=model.name,
            status=model.status,
            job_type=model.job_type,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    async def save(self, job: QuantumJob) -> None:
        model = QuantumJobModel(
            id=job.id,
            name=job.name,
            status=job.status,
            job_type=job.job_type,
            created_at=job.created_at,
            updated_at=job.updated_at
        )
        await self.session.merge(model)
