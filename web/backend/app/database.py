import asyncio
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    retries = 3
    for attempt in range(retries):
        async with async_session_factory() as session:
            try:
                yield session
                await session.commit()
                return
            except SQLAlchemyError as e:
                await session.rollback()
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    logger.warning(f"DB failover, retry %d/%d after %ds: %s", attempt + 1, retries, wait, e)
                    await asyncio.sleep(wait)
                else:
                    logger.error(f"DB exhausted %d attempts: %s", retries, e)
                    raise