from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from backend.app.core.config import DATABASE_URL
from backend.app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Create the async engine, but fall back to the settings default (sqlite) if the
# requested driver isn't available (e.g., asyncpg missing in test/dev venv).
try:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        future=True
    )
except ModuleNotFoundError as exc:
    logger.warning("Could not create async engine for %s: %s. Falling back to settings.DATABASE_URL", DATABASE_URL, exc)
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True
    )

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
