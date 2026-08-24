from typing import AsyncGenerator
from app.core.config import settings
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.logging import get_logger

# Create logger instance
logger = get_logger()

# Create async engine
engine = create_async_engine(settings.DATABASE_URL)

# Create asynchronous session factory
async_session = async_sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

# Dependency to get the database session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"An error occurred while getting the database session: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Database initialization function (to be populated later)
async def init_db() -> None:
    pass