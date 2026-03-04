from abc import ABC, abstractmethod
from typing import List, Optional

from src.domain.entities.quantum_job import QuantumJob
from src.domain.entities.user import User
from src.domain.entities.ai_expert import AIExpert
from src.domain.value_objects.email import Email

class UserRepository(ABC):
    @abstractmethod
    async def get_by_id(self, user_id: str) -> Optional[User]:
        pass

    @abstractmethod
    async def get_by_email(self, email: Email) -> Optional[User]:
        pass

    @abstractmethod
    async def exists(self, email: Email) -> bool:
        pass

    @abstractmethod
    async def save(self, user: User) -> User:
        pass

class QuantumJobRepository(ABC):
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[QuantumJob]:
        pass

    @abstractmethod
    async def list_by_user(
        self, user_id: str, skip: int = 0, limit: int = 100
    ) -> List[QuantumJob]:
        pass

    @abstractmethod
    async def save(self, job: QuantumJob) -> QuantumJob:
        pass

    @abstractmethod
    async def delete(self, job_id: str) -> None:
        pass

class AIExpertRepository(ABC):
    @abstractmethod
    async def get_by_id(self, expert_id: str) -> Optional[AIExpert]:
        pass

    @abstractmethod
    async def save(self, expert: AIExpert) -> AIExpert:
        pass
