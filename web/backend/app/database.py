import logging
from typing import AsyncGenerator
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.exc import SQLAlchemyError
from app.config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


def _normalize_database_url(raw_url: str) -> tuple[URL, dict]:
    """Translate cloud-provider URLs into values asyncpg accepts.

    Render/Heroku hand out ``postgres://`` or ``postgresql://`` URLs, which
    SQLAlchemy would route to psycopg2. asyncpg also rejects the libpq-only
    ``sslmode`` query parameter, so it is converted to ``ssl=True``.
    """
    url = make_url(raw_url)

    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+asyncpg")

    query = dict(url.query)
    sslmode = query.pop("sslmode", None)
    if sslmode is None:
        sslmode = query.pop("ssl", None)

    # libpq-only parameters that asyncpg does not understand (Neon includes
    # channel_binding in its copy-paste connection strings).
    for key in (
        "channel_binding",
        "gssencmode",
        "target_session_attrs",
        "options",
        "application_name",
    ):
        query.pop(key, None)
    url = url.set(query=query)

    connect_args: dict = {}
    if sslmode and str(sslmode).lower() not in {"disable", "allow", "prefer", "false", "0"}:
        connect_args["ssl"] = True

    # Neon/Supabase poolers use PgBouncer in transaction mode. asyncpg's
    # prepared-statement cache is not compatible with that mode.
    if "-pooler" in (url.host or ""):
        connect_args["statement_cache_size"] = 0

    return url, connect_args


_database_url, _connect_args = _normalize_database_url(settings.DATABASE_URL)

engine = create_async_engine(
    _database_url,
    echo=settings.DEBUG,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
    connect_args=_connect_args,
)

async_session_factory = async_sessionmaker(
    engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # NOTE: never retry around `yield` — a dependency generator that yields
    # again after an exception is thrown into it raises
    # RuntimeError("generator didn't stop after athrow()").
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("DB error, transaction rolled back: %s", e)
            raise
        except Exception:
            await session.rollback()
            raise
