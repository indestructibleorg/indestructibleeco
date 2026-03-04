from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.infrastructure.config import get_settings

settings = get_settings()

# Use SQLite for testing, PostgreSQL for others
if settings.app_env.value == "testing":
    DATABASE_URL = "sqlite+aiosqlite:///:memory:"
else:
    DATABASE_URL = str(settings.database.url)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True
)

async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def get_session():
    async with async_session_factory() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
