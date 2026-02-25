"""Database seed script — populate development data."""
from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger(__name__)


async def seed_users() -> None:
    """Seed default users for development."""
    from src.infrastructure.persistence.database import async_session_factory, init_db
    from src.infrastructure.persistence.models import UserModel
    from passlib.context import CryptContext

    pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    await init_db()

    users = [
        {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "email": "admin@superai.local",
            "hashed_password": pwd_ctx.hash("AdminP@ss123"),
            "full_name": "System Administrator",
            "role": "admin",
            "status": "active",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "username": "scientist",
            "email": "scientist@superai.local",
            "hashed_password": pwd_ctx.hash("ScienceP@ss123"),
            "full_name": "Lead Scientist",
            "role": "scientist",
            "status": "active",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "username": "developer",
            "email": "dev@superai.local",
            "hashed_password": pwd_ctx.hash("DevP@ss123"),
            "full_name": "Platform Developer",
            "role": "developer",
            "status": "active",
            "is_active": True,
        },
        {
            "id": str(uuid.uuid4()),
            "username": "viewer",
            "email": "viewer@superai.local",
            "hashed_password": pwd_ctx.hash("ViewP@ss123"),
            "full_name": "Read-Only User",
            "role": "viewer",
            "status": "active",
            "is_active": True,
        },
    ]

    async with async_session_factory() as session:
        for user_data in users:
            from sqlalchemy import select
            existing = await session.execute(
                select(UserModel).where(UserModel.username == user_data["username"])
            )
            if existing.scalar_one_or_none() is None:
                model = UserModel(**user_data)
                session.add(model)
                logger.info("user_seeded", username=user_data["username"], role=user_data["role"])
            else:
                logger.info("user_exists", username=user_data["username"])
        await session.commit()

    logger.info("seed_complete", users_processed=len(users))


async def main() -> None:
    logger.info("seed_starting")
    await seed_users()
    logger.info("seed_finished")


if __name__ == "__main__":
    asyncio.run(main())