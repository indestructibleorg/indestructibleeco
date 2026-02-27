"""Targeted tests for remaining uncovered lines in repositories/__init__.py.

Covers:
- UserSQLRepository: count (111-114), list_users with search (125-126, 137, 143),
  save duplicate id (158), save duplicate username (162), save duplicate email (167),
  delete not found (230)
- QuantumJobSQLRepository: exists (307-312), find_by_status (315-321),
  save update optimistic lock (357-392), delete not found (395-399)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_user_model(
    user_id: str | None = None,
    username: str = "alice",
    email: str = "alice@example.com",
    status: str = "active",
    role: str = "viewer",
    version: int = 0,
) -> MagicMock:
    m = MagicMock()
    m.id = user_id or str(uuid.uuid4())
    m.username = username
    m.email = email
    m.hashed_password = "$2b$12$fakehash"
    m.status = status
    m.role = role
    m.version = version
    m.full_name = ""
    m.permissions = []
    m.last_login_at = None
    m.failed_login_attempts = 0
    m.locked_until = None
    m.created_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    return m


def _make_job_model(
    job_id: str | None = None,
    user_id: str = "user-1",
    status: str = "submitted",
    version: int = 0,
) -> MagicMock:
    m = MagicMock()
    m.id = job_id or str(uuid.uuid4())
    m.user_id = user_id
    m.algorithm = "vqe"
    m.backend = "aer_simulator"
    m.status = status
    m.num_qubits = 2
    m.shots = 1024
    m.parameters = {}
    m.result = None
    m.error_message = None
    m.execution_time_ms = None
    m.submitted_at = datetime.now(timezone.utc)
    m.started_at = None
    m.completed_at = None
    m.version = version
    m.created_at = datetime.now(timezone.utc)
    m.updated_at = datetime.now(timezone.utc)
    return m


def _make_user_entity(username: str = "alice", email: str = "alice@example.com"):
    from src.domain.entities.user import User, UserRole
    return User.create(
        username=username,
        email=email,
        hashed_password="$2b$12$fakehash",
        role=UserRole.VIEWER,
    )


def _make_job_entity(job_id: str | None = None, version: int = 1):
    from src.domain.entities.quantum_job import QuantumJob
    job = QuantumJob.submit(
        user_id="user-1",
        algorithm="vqe",
        num_qubits=2,
        shots=1024,
    )
    if job_id:
        object.__setattr__(job, "id", job_id)
    object.__setattr__(job, "version", version)
    return job


# ---------------------------------------------------------------------------
# UserSQLRepository – count (lines 111-114)
# ---------------------------------------------------------------------------

class TestUserRepoCount:
    """Cover lines 111-114: count() method."""

    @pytest.mark.asyncio
    async def test_count_returns_integer(self):
        """Lines 111-114 – count() executes SELECT COUNT and returns int."""
        from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyUserRepository(session)
        count = await repo.count()
        assert count == 5

    @pytest.mark.asyncio
    async def test_count_returns_zero_when_none(self):
        """Lines 111-114 – count() returns 0 when scalar returns None."""
        from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyUserRepository(session)
        count = await repo.count()
        assert count == 0


# ---------------------------------------------------------------------------
# UserSQLRepository – list_users with search (lines 125-126, 137, 143)
# ---------------------------------------------------------------------------

class TestUserRepoListUsersSearch:
    """Cover lines 125-126, 137, 143: list_users with search filter."""

    @pytest.mark.asyncio
    async def test_list_users_with_search_filter(self):
        """Lines 125-126, 137, 143 – search filter is applied to query."""
        from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

        session = AsyncMock()
        mock_model = _make_user_model(username="alice")

        # First execute call = count query, second = page query
        count_result = MagicMock()
        count_result.scalar.return_value = 1
        page_result = MagicMock()
        page_result.scalars.return_value.all.return_value = [mock_model]

        session.execute = AsyncMock(side_effect=[count_result, page_result])

        repo = SQLAlchemyUserRepository(session)
        users, total = await repo.list_users(skip=0, limit=10, search="alice")

        assert total == 1
        assert len(users) == 1
        assert session.execute.call_count == 2


# ---------------------------------------------------------------------------
# UserSQLRepository – save duplicate id (line 158)
# ---------------------------------------------------------------------------

class TestUserRepoSaveDuplicateId:
    """Cover line 158: save raises EntityAlreadyExistsError for duplicate id."""

    @pytest.mark.asyncio
    async def test_save_duplicate_id_raises(self):
        """Line 158 – duplicate id raises EntityAlreadyExistsError."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyUserRepository,
            EntityAlreadyExistsError,
        )

        session = AsyncMock()
        existing_model = _make_user_model()
        session.get = AsyncMock(return_value=existing_model)

        repo = SQLAlchemyUserRepository(session)
        entity = _make_user_entity()
        # Override entity id to match existing model
        object.__setattr__(entity, "id", existing_model.id)

        with pytest.raises(EntityAlreadyExistsError):
            await repo.save(entity)


# ---------------------------------------------------------------------------
# UserSQLRepository – save duplicate username (line 162)
# ---------------------------------------------------------------------------

class TestUserRepoSaveDuplicateUsername:
    """Cover line 162: save raises EntityAlreadyExistsError for duplicate username."""

    @pytest.mark.asyncio
    async def test_save_duplicate_username_raises(self):
        """Line 162 – duplicate username raises EntityAlreadyExistsError."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyUserRepository,
            EntityAlreadyExistsError,
        )

        session = AsyncMock()
        # No existing by id
        session.get = AsyncMock(return_value=None)

        # find_by_username returns a model (duplicate)
        dup_model = _make_user_model(username="alice")
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = dup_model
        session.execute = AsyncMock(return_value=dup_result)

        repo = SQLAlchemyUserRepository(session)
        entity = _make_user_entity(username="alice")

        with pytest.raises(EntityAlreadyExistsError):
            await repo.save(entity)


# ---------------------------------------------------------------------------
# UserSQLRepository – save duplicate email (line 167)
# ---------------------------------------------------------------------------

class TestUserRepoSaveDuplicateEmail:
    """Cover line 167: save raises EntityAlreadyExistsError for duplicate email."""

    @pytest.mark.asyncio
    async def test_save_duplicate_email_raises(self):
        """Line 167 – duplicate email raises EntityAlreadyExistsError."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyUserRepository,
            EntityAlreadyExistsError,
        )

        session = AsyncMock()
        session.get = AsyncMock(return_value=None)

        # First execute (find_by_username) returns None, second (find_by_email) returns dup
        no_dup = MagicMock()
        no_dup.scalar_one_or_none.return_value = None
        dup_email_model = _make_user_model(email="alice@example.com")
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = dup_email_model

        session.execute = AsyncMock(side_effect=[no_dup, dup_result])

        repo = SQLAlchemyUserRepository(session)
        entity = _make_user_entity(email="alice@example.com")

        with pytest.raises(EntityAlreadyExistsError):
            await repo.save(entity)


# ---------------------------------------------------------------------------
# UserSQLRepository – delete not found (line 230)
# ---------------------------------------------------------------------------

class TestUserRepoDeleteNotFound:
    """Cover line 230: delete raises EntityNotFoundError when no rows deleted."""

    @pytest.mark.asyncio
    async def test_delete_not_found_raises(self):
        """Line 230 – delete raises EntityNotFoundError when rowcount == 0."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyUserRepository,
            EntityNotFoundError,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyUserRepository(session)
        with pytest.raises(EntityNotFoundError):
            await repo.delete("nonexistent-id")


# ---------------------------------------------------------------------------
# QuantumJobSQLRepository – exists (lines 307-312)
# ---------------------------------------------------------------------------

class TestQuantumJobRepoExists:
    """Cover lines 307-312: exists() method."""

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_found(self):
        """Lines 307-312 – exists returns True when count > 0."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 1
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        result = await repo.exists("job-1")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_when_not_found(self):
        """Lines 307-312 – exists returns False when count == 0."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        result = await repo.exists("missing-job")
        assert result is False


# ---------------------------------------------------------------------------
# QuantumJobSQLRepository – find_by_status (lines 315-321)
# ---------------------------------------------------------------------------

class TestQuantumJobRepoFindByStatus:
    """Cover lines 315-321: find_by_status() method."""

    @pytest.mark.asyncio
    async def test_find_by_status_returns_jobs(self):
        """Lines 315-321 – find_by_status returns list of QuantumJob entities."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        session = AsyncMock()
        job_model = _make_job_model(status="submitted")
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [job_model]
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        jobs = await repo.find_by_status("submitted")
        assert len(jobs) == 1

    @pytest.mark.asyncio
    async def test_find_by_status_returns_empty_list(self):
        """Lines 315-321 – find_by_status returns empty list when no matches."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        jobs = await repo.find_by_status("completed")
        assert jobs == []


# ---------------------------------------------------------------------------
# QuantumJobSQLRepository – save update optimistic lock (lines 357-392)
# ---------------------------------------------------------------------------

class TestQuantumJobRepoSaveUpdate:
    """Cover lines 357-392: save() with existing entity (update path)."""

    @pytest.mark.asyncio
    async def test_save_update_success(self):
        """Lines 357-391 – save updates existing job successfully."""
        from src.infrastructure.persistence.repositories import SQLAlchemyQuantumJobRepository

        session = AsyncMock()
        job_id = str(uuid.uuid4())
        existing_model = _make_job_model(job_id=job_id, version=0)

        # get() returns existing model
        session.get = AsyncMock(return_value=existing_model)
        # execute() returns rowcount=1 (update succeeded)
        mock_result = MagicMock()
        mock_result.rowcount = 1
        session.execute = AsyncMock(return_value=mock_result)
        session.flush = AsyncMock()

        repo = SQLAlchemyQuantumJobRepository(session)
        entity = _make_job_entity(job_id=job_id, version=1)
        result = await repo.save(entity)
        assert result.id == job_id

    @pytest.mark.asyncio
    async def test_save_update_optimistic_lock_raises(self):
        """Line 389 – save raises OptimisticLockError when rowcount == 0."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyQuantumJobRepository,
            OptimisticLockError,
        )

        session = AsyncMock()
        job_id = str(uuid.uuid4())
        existing_model = _make_job_model(job_id=job_id, version=0)

        session.get = AsyncMock(return_value=existing_model)
        mock_result = MagicMock()
        mock_result.rowcount = 0  # optimistic lock conflict
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        entity = _make_job_entity(job_id=job_id, version=1)

        with pytest.raises(OptimisticLockError):
            await repo.save(entity)


# ---------------------------------------------------------------------------
# QuantumJobSQLRepository – delete not found (lines 395-399)
# ---------------------------------------------------------------------------

class TestQuantumJobRepoDeleteNotFound:
    """Cover lines 395-399: delete raises EntityNotFoundError when no rows deleted."""

    @pytest.mark.asyncio
    async def test_delete_not_found_raises(self):
        """Lines 395-399 – delete raises EntityNotFoundError when rowcount == 0."""
        from src.infrastructure.persistence.repositories import (
            SQLAlchemyQuantumJobRepository,
            EntityNotFoundError,
        )

        session = AsyncMock()
        mock_result = MagicMock()
        mock_result.rowcount = 0
        session.execute = AsyncMock(return_value=mock_result)

        repo = SQLAlchemyQuantumJobRepository(session)
        with pytest.raises(EntityNotFoundError):
            await repo.delete("nonexistent-job")
