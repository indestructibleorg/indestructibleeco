import pytest
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.user import User
from src.domain.value_objects.email import Email
from src.infrastructure.persistence.repositories import SQLAlchemyUserRepository

@pytest.mark.asyncio
async def test_save_and_get_user(db_session: AsyncSession):
    # Arrange
    repo = SQLAlchemyUserRepository(db_session)
    user_id = str(uuid.uuid4())
    email = Email(f"test-{user_id}@example.com")
    user = User(
        id=user_id,
        username=f"user-{user_id}",
        email=email,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    # Act
    await repo.save(user)
    await db_session.commit()

    # Assert
    retrieved_user = await repo.get_by_id(user_id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert retrieved_user.username == user.username
    assert str(retrieved_user.email) == str(user.email)
    assert retrieved_user.is_active == user.is_active

@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession):
    # Arrange
    repo = SQLAlchemyUserRepository(db_session)
    user_id = str(uuid.uuid4())
    email_str = f"test-{user_id}@example.com"
    email = Email(email_str)
    user = User(
        id=user_id,
        username=f"user-{user_id}",
        email=email
    )
    await repo.save(user)
    await db_session.commit()

    # Act
    retrieved_user = await repo.get_by_email(email)

    # Assert
    assert retrieved_user is not None
    assert retrieved_user.id == user.id
    assert str(retrieved_user.email) == email_str

@pytest.mark.asyncio
async def test_user_exists(db_session: AsyncSession):
    # Arrange
    repo = SQLAlchemyUserRepository(db_session)
    user_id = str(uuid.uuid4())
    email = Email(f"test-{user_id}@example.com")
    user = User(id=user_id, username=f"user-{user_id}", email=email)
    await repo.save(user)
    await db_session.commit()

    # Act & Assert
    assert await repo.exists(email) is True
    assert await repo.exists(Email("nonexistent@example.com")) is False
