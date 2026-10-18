"""
Period-End Closing procedures and Fiscal Period management.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.accounting import FiscalPeriod, JournalEntry, JournalEntryLine, Account
from app.models.audit import PeriodClosingEntry
from app.utils.deps import get_current_active_user

router = APIRouter()


@router.get("/fiscal-periods")
async def list_fiscal_periods(
    is_closed: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all fiscal periods"""
    query = select(FiscalPeriod).order_by(FiscalPeriod.start_date.desc())
    if is_closed is not None:
        query = query.where(FiscalPeriod.is_closed == is_closed)
    result = await db.execute(query)
    periods = result.scalars().all()
    return [{"id": p.id, "name": p.name, "name_en": p.name_en,
             "start_date": str(p.start_date), "end_date": str(p.end_date),
             "is_closed": p.is_closed, "is_locked": p.is_locked,
             "closed_by": p.closed_by, "closed_at": str(p.closed_at) if p.closed_at else None} for p in periods]


@router.post("/fiscal-periods")
async def create_fiscal_period(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new fiscal period"""
    period = FiscalPeriod(
        name=data["name"],
        name_en=data.get("name_en"),
        start_date=datetime.fromisoformat(data["start_date"]) if isinstance(data.get("start_date"), str) else data.get("start_date"),
        end_date=datetime.fromisoformat(data["end_date"]) if isinstance(data.get("end_date"), str) else data.get("end_date"),
        is_closed=False,
        is_locked=False,
        created_at=datetime.now(),
    )
    db.add(period)
    await db.commit()
    await db.refresh(period)
    return {"id": period.id, "name": period.name, "message": "Fiscal period created"}


@router.get("/fiscal-periods/{period_id}/validate")
async def validate_period_for_closing(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Validate if a fiscal period can be closed.
    Checks for unposted entries, unbalanced books, etc.
    """
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if period.is_closed:
        return {"can_close": False, "reason": "Period is already closed"}

    # Check for unposted journal entries in this period
    unposted_result = await db.execute(
        select(func.count(JournalEntry.id))
        .where(JournalEntry.entry_date >= period.start_date)
        .where(JournalEntry.entry_date <= period.end_date)
        .where(JournalEntry.status == "Draft")
    )
    unposted_count = unposted_result.scalar()

    issues = []
    if unposted_count > 0:
        issues.append(f"{unposted_count} unposted journal entries")

    # Check if debits = credits for all posted entries
    balance_check = await db.execute(
        select(
            func.sum(JournalEntryLine.debit).label("total_debit"),
            func.sum(JournalEntryLine.credit).label("total_credit")
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntry.entry_date >= period.start_date)
        .where(JournalEntry.entry_date <= period.end_date)
        .where(JournalEntry.status == "Posted")
    )
    balance = balance_check.one_or_none()
    if balance:
        total_debit = float(balance.total_debit or 0)
        total_credit = float(balance.total_credit or 0)
        if abs(total_debit - total_credit) > 0.01:
            issues.append(f"Books are not balanced. Debit: {total_debit}, Credit: {total_credit}")

    return {
        "can_close": len(issues) == 0,
        "period_name": period.name,
        "issues": issues,
        "unposted_entries": unposted_count,
    }


@router.post("/fiscal-periods/{period_id}/close")
async def close_fiscal_period(
    period_id: int,
    data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Close a fiscal period:
    1. Validate period can be closed
    2. Create closing entries (revenue/expense -> retained earnings)
    3. Mark period as closed
    4. Carry forward opening balances
    """
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if period.is_closed:
        raise HTTPException(status_code=400, detail="Period is already closed")

    # First validate
    validation = await validate_period_for_closing(period_id, db, current_user)
    if not validation["can_close"]:
        raise HTTPException(status_code=400, detail=f"Cannot close period: {', '.join(validation['issues'])}")

    # Create closing entry for revenue and expense accounts
    # Get all posted entries in this period
    entries_result = await db.execute(
        select(JournalEntry.id)
        .where(JournalEntry.entry_date >= period.start_date)
        .where(JournalEntry.entry_date <= period.end_date)
        .where(JournalEntry.status == "Posted")
    )
    entry_ids = [e.id for e in entries_result.scalars().all()]

    if entry_ids:
        # Get revenue and expense account balances
        account_balances = await db.execute(
            select(
                Account.account_type,
                Account.id,
                Account.account_code,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit")
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.id.in_(entry_ids))
            .where(Account.account_type.in_(["Revenue", "Expense"]))
            .group_by(Account.id, Account.account_type, Account.account_code)
        )

        # Build closing lines
        closing_lines = []
        retained_earnings_total = 0.0

        for balance in account_balances:
            debit = float(balance.total_debit)
            credit = float(balance.total_credit)
            net = credit - debit if balance.account_type == "Revenue" else debit - credit

            if abs(net) > 0.01:
                closing_lines.append({
                    "account_id": balance.id,
                    "debit": net if balance.account_type == "Revenue" else 0,
                    "credit": 0 if balance.account_type == "Revenue" else net,
                })
                retained_earnings_total += net

        # Add retained earnings line
        if abs(retained_earnings_total) > 0.01:
            # Find retained earnings account
            re_result = await db.execute(
                select(Account).where(Account.account_code == "3200").limit(1)
            )
            re_account = re_result.scalar_one_or_none()
            if re_account:
                closing_lines.append({
                    "account_id": re_account.id,
                    "debit": 0 if retained_earnings_total > 0 else abs(retained_earnings_total),
                    "credit": retained_earnings_total if retained_earnings_total > 0 else 0,
                })

        # Create the closing journal entry if there are lines
        if closing_lines:
            closing_entry = JournalEntry(
                entry_number=f"CL-{period.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                entry_date=period.end_date,
                description=f"Period closing entries for {period.name}",
                status="Draft",
                created_by=current_user.id if hasattr(current_user, "id") else None,
                company_id=None,
                created_at=datetime.now(),
            )
            db.add(closing_entry)
            await db.flush()

            for line in closing_lines:
                je_line = JournalEntryLine(
                    journal_entry_id=closing_entry.id,
                    account_id=line["account_id"],
                    debit=line["debit"],
                    credit=line["credit"],
                    created_at=datetime.now(),
                )
                db.add(je_line)

            # Auto-post the closing entry
            closing_entry.status = "Posted"
            closing_entry.approved_by = current_user.id if hasattr(current_user, "id") else None
            closing_entry.approved_at = datetime.now()

            # Record the closing entry
            period_closing = PeriodClosingEntry(
                fiscal_period_id=period_id,
                closing_type="REVENUE_EXPENSE",
                description=f"Period closing for {period.name}",
                total_debit=sum(l["debit"] for l in closing_lines),
                total_credit=sum(l["credit"] for l in closing_lines),
                status="POSTED",
                journal_entry_id=closing_entry.id,
                posted_by=current_user.id if hasattr(current_user, "id") else None,
                posted_at=datetime.now(),
                created_at=datetime.now(),
            )
            db.add(period_closing)

    # Mark period as closed
    period.is_closed = True
    period.closed_by = current_user.id if hasattr(current_user, "id") else None
    period.closed_at = datetime.now()

    await db.commit()
    return {"success": True, "message": f"Period {period.name} closed successfully"}


@router.post("/fiscal-periods/{period_id}/lock")
async def lock_fiscal_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Lock a fiscal period to prevent any new entries"""
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if period.is_locked:
        raise HTTPException(status_code=400, detail="Period is already locked")

    period.is_locked = True
    await db.commit()
    return {"success": True, "message": f"Period {period.name} locked"}
