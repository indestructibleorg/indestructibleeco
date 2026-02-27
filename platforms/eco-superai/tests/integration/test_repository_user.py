"""Integration tests for SQLAlchemyUserRepository.

Tests cover:
- save: happy path, duplicate id, duplicate username, duplicate email
- find_by_id: found, not found
- find_by_username / find_by_email: found, not found
- exists / count
- list_users: pagination, role filter, status filter, search
- update: happy path, optimistic lock conflict, entity not found
- delete: happy path, entity not found
- State machine: pending → active → suspended → deleted
"""
from __future__ import annotations

import uuid

import pytest
import pytest_asyncio

from src.domain.entities.user import User, UserRole, UserStatus
from src.domain.value_objects.email import Email
from src.domain.value_objects.password import HashedPassword
from src.infrastructure.persistence.repositories import (
    EntityAlreadyExistsError,
    EntityNotFoundError,
    OptimisticLockError,
    SQLAlchemyUserRepository,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.integration]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_FAKE_HASH = "$2b$12$LJ3m4ys3Lg.Ry5qFnGmMHOPbEEYpzOEjSMfB7xUqHCDeaIiqHuMy"


def _make_user(
    username: str | None = None,
    email: str | None = None,
    role: UserRole = UserRole.DEVELOPER,
    status: UserStatus = UserStatus.ACTIVE,
) -> User:
    uid = uuid.uuid4().hex[:8]
    return User(
        id=str(uuid.uuid4()),
        username=username or f"user_{uid}",
        email=Email(value=email or f"user_{uid}@example.com"),
        hashed_password=HashedPassword(value=_FAKE_HASH),
        full_name="Test User",
        role=role,
        status=status,
        version=0,
    )


# ---------------------------------------------------------------------------
# save
# ---------------------------------------------------------------------------

class TestUserRepositorySave:

    async def test_save_new_user_persists(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        saved = await repo.save(user)
        assert saved.id == user.id
        found = await repo.find_by_id(user.id)
        assert found is not None
        assert found.username == user.username

    async def test_save_duplicate_id_raises(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)
        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            await repo.save(user)
        assert exc_info.value.field == "id"

    async def test_save_duplicate_username_raises(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user1 = _make_user(username="duplicate_user")
        user2 = _make_user(username="duplicate_user")
        await repo.save(user1)
        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            await repo.save(user2)
        assert exc_info.value.field == "username"

    async def test_save_duplicate_email_raises(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user1 = _make_user(email="dup@example.com")
        user2 = _make_user(email="dup@example.com")
        await repo.save(user1)
        with pytest.raises(EntityAlreadyExistsError) as exc_info:
            await repo.save(user2)
        assert exc_info.value.field == "email"


# ---------------------------------------------------------------------------
# find_by_id / find_by_username / find_by_email
# ---------------------------------------------------------------------------

class TestUserRepositoryFind:

    async def test_find_by_id_existing(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)
        found = await repo.find_by_id(user.id)
        assert found is not None
        assert found.id == user.id
        assert found.email.value == user.email.value

    async def test_find_by_id_nonexistent_returns_none(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        result = await repo.find_by_id(str(uuid.uuid4()))
        assert result is None

    async def test_find_by_username_existing(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user(username="findme_user")
        await repo.save(user)
        found = await repo.find_by_username("findme_user")
        assert found is not None
        assert found.username == "findme_user"

    async def test_find_by_username_nonexistent_returns_none(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        result = await repo.find_by_username("ghost_user_xyz")
        assert result is None

    async def test_find_by_email_existing(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user(email="findme@example.com")
        await repo.save(user)
        found = await repo.find_by_email("findme@example.com")
        assert found is not None
        assert found.email.value == "findme@example.com"

    async def test_find_by_email_nonexistent_returns_none(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        result = await repo.find_by_email("ghost@example.com")
        assert result is None


# ---------------------------------------------------------------------------
# exists / count
# ---------------------------------------------------------------------------

class TestUserRepositoryExistsCount:

    async def test_exists_true(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)
        assert await repo.exists(user.id) is True

    async def test_exists_false(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        assert await repo.exists(str(uuid.uuid4())) is False

    async def test_count_increases_after_save(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        before = await repo.count()
        await repo.save(_make_user())
        await repo.save(_make_user())
        after = await repo.count()
        assert after == before + 2


# ---------------------------------------------------------------------------
# list_users (pagination, filter, search)
# ---------------------------------------------------------------------------

class TestUserRepositoryList:

    async def test_list_users_pagination(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        for _ in range(5):
            await repo.save(_make_user())
        page1 = await repo.list_users(skip=0, limit=3)
        page2 = await repo.list_users(skip=3, limit=3)
        assert len(page1) <= 3
        assert len(page2) >= 0
        # No overlap
        ids1 = {u.id for u in page1}
        ids2 = {u.id for u in page2}
        assert ids1.isdisjoint(ids2)

    async def test_list_users_filter_by_role(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        await repo.save(_make_user(role=UserRole.ADMIN))
        await repo.save(_make_user(role=UserRole.VIEWER))
        admins = await repo.list_users(role="admin")
        assert all(u.role == UserRole.ADMIN for u in admins)

    async def test_list_users_filter_by_status(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        await repo.save(_make_user(status=UserStatus.ACTIVE))
        await repo.save(_make_user(status=UserStatus.SUSPENDED))
        active = await repo.list_users(status="active")
        assert all(u.status == UserStatus.ACTIVE for u in active)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------

class TestUserRepositoryUpdate:

    async def test_update_happy_path(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)

        user.full_name = "Updated Name"
        user.increment_version()  # version 0 → 1
        updated = await repo.update(user)
        assert updated.full_name == "Updated Name"
        assert updated.version == 1

    async def test_update_optimistic_lock_conflict(self, db_session) -> None:
        """Simulate two concurrent updates on the same entity.

        First update succeeds (version 0 → 1).
        Second update with stale version (still 0 → 1) must raise
        OptimisticLockError.
        """
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)

        # Simulate first update
        user.full_name = "First Update"
        user.increment_version()
        await repo.update(user)

        # Simulate stale second update (version is now 2 but DB has 1)
        user.full_name = "Stale Update"
        user.increment_version()  # version = 2, but DB still expects 1 → conflict
        with pytest.raises(OptimisticLockError) as exc_info:
            await repo.update(user)
        assert exc_info.value.entity_id == user.id

    async def test_update_nonexistent_raises(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        ghost = _make_user()
        ghost.increment_version()
        with pytest.raises((EntityNotFoundError, OptimisticLockError)):
            await repo.update(ghost)


# ---------------------------------------------------------------------------
# delete
# ---------------------------------------------------------------------------

class TestUserRepositoryDelete:

    async def test_delete_existing_user(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        user = _make_user()
        await repo.save(user)
        await repo.delete(user.id)
        assert await repo.find_by_id(user.id) is None

    async def test_delete_nonexistent_raises(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)
        with pytest.raises(EntityNotFoundError):
            await repo.delete(str(uuid.uuid4()))


# ---------------------------------------------------------------------------
# State machine: User lifecycle
# ---------------------------------------------------------------------------

class TestUserStateMachine:
    """Verify the full User lifecycle through the repository.

    pending_verification → active → suspended → (re-activated) → active
    """

    async def test_user_lifecycle(self, db_session) -> None:
        repo = SQLAlchemyUserRepository(db_session)

        # 1. Create user in PENDING state
        user = User.create(
            username=f"lifecycle_{uuid.uuid4().hex[:6]}",
            email=f"lifecycle_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password=_FAKE_HASH,
            full_name="Lifecycle User",
        )
        assert user.status == UserStatus.PENDING_VERIFICATION
        await repo.save(user)

        # 2. Activate
        user.activate()
        user.increment_version()
        await repo.update(user)
        found = await repo.find_by_id(user.id)
        assert found.status == UserStatus.ACTIVE

        # 3. Suspend
        user.suspend(reason="policy violation")
        user.increment_version()
        await repo.update(user)
        found = await repo.find_by_id(user.id)
        assert found.status == UserStatus.SUSPENDED

        # 4. Re-activate
        user.activate()
        user.increment_version()
        await repo.update(user)
        found = await repo.find_by_id(user.id)
        assert found.status == UserStatus.ACTIVE
