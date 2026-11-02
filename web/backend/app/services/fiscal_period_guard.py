"""
Central fiscal-period guard.

Every posting path (journal save/post, sales approval, purchases approval,
payments, cheques, fixed-asset depreciation/disposal, bank transactions, ...)
must call ``check_period_open`` before creating a journal entry so that
postings into closed/soft-closed/locked periods are rejected on the backend.
"""

from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import FiscalPeriod


async def check_period_open(
    db: AsyncSession,
    entry_date: datetime,
    period_id: int | None = None,
) -> FiscalPeriod | None:
    """
    Return the fiscal period covering ``entry_date`` or ``None`` when no
    period is defined (periods are optional by design). Raise HTTP 400 when
    the covering period is closed, soft-closed, or locked.
    """
    if period_id is not None:
        result = await db.execute(
            select(FiscalPeriod).where(FiscalPeriod.id == period_id).limit(1)
        )
        period = result.scalar_one_or_none()
    else:
        # Prefer the narrowest covering period (smallest date range) so that
        # monthly periods inside a full-year shell period take precedence.
        result = await db.execute(
            select(FiscalPeriod)
            .where(FiscalPeriod.start_date <= entry_date)
            .where(FiscalPeriod.end_date >= entry_date)
            .order_by(FiscalPeriod.end_date.asc())
            .limit(1)
        )
        period = result.scalar_one_or_none()

    if period is None:
        return None

    if period.is_closed or period.is_locked:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Posting is not allowed: fiscal period '{period.name}' "
                "is closed or locked. Reopen the period first (requires special permission)."
            ),
        )
    if period.is_soft_closed:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Posting is not allowed: fiscal period '{period.name}' is "
                "soft-closed. Only year-end adjustments are permitted."
            ),
        )
    return period