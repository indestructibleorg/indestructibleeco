"""Test factories — factory-boy definitions for domain entities and ORM models."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from src.domain.entities.user import Email, HashedPassword, User, UserRole, UserStatus
from src.domain.entities.quantum_job import JobStatus, QuantumAlgorithm, QuantumJob
from src.domain.entities.ai_expert import AIExpert, ExpertDomain, ExpertStatus


# ---------------------------------------------------------------------------
# Fake password hash (valid bcrypt format, not a real hash)
# ---------------------------------------------------------------------------
_FAKE_BCRYPT = "$2b$12$LJ3m4ys3Lg.Ry5qFnGmMHOPbEEYpzOEjSMfB7xUqHCDeaIiqHuMy"


# ---------------------------------------------------------------------------
# User Factories
# ---------------------------------------------------------------------------

class UserFactory:
    """Factory for creating User domain entities in tests."""

    _counter: int = 0

    @classmethod
    def create(
        cls,
        username: str | None = None,
        email: str | None = None,
        role: UserRole = UserRole.DEVELOPER,
        status: UserStatus = UserStatus.ACTIVE,
        full_name: str = "Test User",
        hashed_password: str = _FAKE_BCRYPT,
        **overrides: Any,
    ) -> User:
        cls._counter += 1
        _username = username or f"testuser_{cls._counter}"
        _email = email or f"testuser_{cls._counter}@example.com"

        user = User(
            id=overrides.get("id", str(uuid.uuid4())),
            username=_username,
            email=Email(value=_email),
            hashed_password=HashedPassword(value=hashed_password),
            full_name=full_name,
            role=role,
            status=status,
            created_at=overrides.get("created_at", datetime.now(timezone.utc)),
            updated_at=overrides.get("updated_at", datetime.now(timezone.utc)),
            version=overrides.get("version", 0),
        )
        return user

    @classmethod
    def create_admin(cls, **overrides: Any) -> User:
        return cls.create(role=UserRole.ADMIN, **overrides)

    @classmethod
    def create_viewer(cls, **overrides: Any) -> User:
        return cls.create(role=UserRole.VIEWER, **overrides)

    @classmethod
    def create_scientist(cls, **overrides: Any) -> User:
        return cls.create(role=UserRole.SCIENTIST, **overrides)

    @classmethod
    def create_batch(cls, count: int, **overrides: Any) -> list[User]:
        return [cls.create(**overrides) for _ in range(count)]


# ---------------------------------------------------------------------------
# QuantumJob Factories
# ---------------------------------------------------------------------------

class QuantumJobFactory:
    """Factory for creating QuantumJob domain entities in tests."""

    _counter: int = 0

    @classmethod
    def create(
        cls,
        user_id: str | None = None,
        algorithm: str = "bell",
        num_qubits: int = 2,
        shots: int = 1024,
        backend: str = "aer_simulator",
        status: JobStatus = JobStatus.SUBMITTED,
        **overrides: Any,
    ) -> QuantumJob:
        cls._counter += 1
        _user_id = user_id or f"user-{cls._counter}"

        job = QuantumJob(
            id=overrides.get("id", str(uuid.uuid4())),
            user_id=_user_id,
            algorithm=QuantumAlgorithm(algorithm),
            num_qubits=num_qubits,
            shots=shots,
            backend=backend,
            status=status,
            parameters=overrides.get("parameters", {}),
            result=overrides.get("result", {}),
            created_at=overrides.get("created_at", datetime.now(timezone.utc)),
            updated_at=overrides.get("updated_at", datetime.now(timezone.utc)),
        )
        return job

    @classmethod
    def create_completed(cls, **overrides: Any) -> QuantumJob:
        job = cls.create(**overrides)
        job.start()
        job.complete(
            result={"counts": {"00": 512, "11": 512}},
            execution_time_ms=25.0,
        )
        return job

    @classmethod
    def create_failed(cls, error: str = "Backend unavailable", **overrides: Any) -> QuantumJob:
        job = cls.create(**overrides)
        job.start()
        job.fail(error)
        return job


# ---------------------------------------------------------------------------
# AIExpert Factories
# ---------------------------------------------------------------------------

class AIExpertFactory:
    """Factory for creating AIExpert domain entities in tests."""

    _counter: int = 0

    @classmethod
    def create(
        cls,
        name: str | None = None,
        domain: str = "general",
        owner_id: str | None = None,
        model: str = "gpt-4-turbo-preview",
        **overrides: Any,
    ) -> AIExpert:
        cls._counter += 1
        _name = name or f"Expert_{cls._counter}"
        _owner = owner_id or f"owner-{cls._counter}"

        expert = AIExpert(
            id=overrides.get("id", str(uuid.uuid4())),
            name=_name,
            domain=ExpertDomain(domain),
            owner_id=_owner,
            model=model,
            temperature=overrides.get("temperature", 0.7),
            system_prompt=overrides.get("system_prompt", ""),
            status=overrides.get("status", ExpertStatus.ACTIVE),
            knowledge_base_ids=overrides.get("knowledge_base_ids", []),
            created_at=overrides.get("created_at", datetime.now(timezone.utc)),
            updated_at=overrides.get("updated_at", datetime.now(timezone.utc)),
        )
        return expert

    @classmethod
    def create_quantum_expert(cls, **overrides: Any) -> AIExpert:
        return cls.create(domain="quantum", name="QuantumExpert", **overrides)

    @classmethod
    def create_ml_expert(cls, **overrides: Any) -> AIExpert:
        return cls.create(domain="ml", name="MLExpert", **overrides)


__all__ = ["UserFactory", "QuantumJobFactory", "AIExpertFactory"]