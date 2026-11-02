"""
Background scheduler for recurring journal entry templates.

Scans for due, active templates on an interval and runs them automatically,
so templates do not require manual "run now" clicks. Runs as an asyncio
background task spawned in the FastAPI lifespan.
"""

import asyncio
import logging
import os
from datetime import UTC, datetime

from sqlalchemy import text

from app.database import async_session_factory, engine
from app.services.recurring_je import (
    fetch_due_templates,
    run_template,
)

logger = logging.getLogger(__name__)

DEFAULT_INTERVAL_SECONDS = 60


def get_interval_seconds() -> int:
    try:
        return int(os.getenv("RECURRING_JE_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS))
    except ValueError:
        return DEFAULT_INTERVAL_SECONDS


async def _process_due_templates(session, now) -> int:
    from sqlalchemy.exc import SQLAlchemyError
    count = 0
    try:
        due = await fetch_due_templates(session, as_of=now)
        for template in due:
            # Isolate each template in a nested transaction (savepoint) so a
            # single failure doesn't poison the whole run / other templates.
            try:
                async with session.begin_nested():
                    await run_template(
                        session,
                        template,
                        company_id=getattr(template, "company_id", None),
                    )
                count += 1
                logger.info("Auto-ran recurring template #%s (%s)", template.id, template.name)
            except ValueError as e:
                # Unbalanced/missing lines: pause the template so it stops retrying.
                logger.warning("Recurring template #%s skipped: %s", template.id, e)
                try:
                    async with session.begin_nested():
                        template.is_active = False
                except Exception:
                    pass
            except Exception as e:
                logger.error("Recurring template #%s failed: %s", template.id, e)
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error("Recurring scheduler DB error, rolled back: %s", e)
    return count


async def run_once():
    """Process all due recurring templates exactly once. Returns count run.

    A PostgreSQL advisory lock guarantees only one process/worker runs the
    scheduler at a time (uvicorn workers or multiple service instances).
    """
    now = datetime.now(UTC).replace(tzinfo=None)

    if engine.dialect.name != "postgresql":
        async with async_session_factory() as session:
            return await _process_due_templates(session, now)

    lock_key = int(os.getenv("RECURRING_JE_LOCK_KEY", "918273645"))
    # Hold the lock on its own connection: SQLAlchemy may return the session's
    # connection to the pool on commit, which would silently drop the lock.
    async with engine.connect() as lock_conn:
        acquired = (
            await lock_conn.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": lock_key})
        ).scalar()
        if not acquired:
            return 0
        try:
            async with async_session_factory() as session:
                return await _process_due_templates(session, now)
        finally:
            await lock_conn.execute(
                text("SELECT pg_advisory_unlock(:k)"), {"k": lock_key}
            )
            await lock_conn.commit()


async def scheduler_loop():
    interval = get_interval_seconds()
    logger.info("Recurring JE scheduler started (interval=%ss)", interval)
    while True:
        try:
            count = await run_once()
            if count:
                logger.info("Recurring scheduler ran %s template(s)", count)
        except Exception as e:
            logger.exception("Recurring scheduler iteration failed: %s", e)
        await asyncio.sleep(interval)
