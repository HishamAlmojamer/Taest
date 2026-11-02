"""
Period-End Closing procedures and Fiscal Period management.
"""

from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.accounting import FiscalPeriod, FiscalYear, JournalEntry, JournalEntryLine, Account
from app.models.audit import PeriodClosingEntry
from app.routers.accounting import _LEDGER_STATUSES
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log
from app.utils.validation import require_fields, parse_date_value
from app.services.settings_service import get_setting

router = APIRouter()


def _coerce_ts(value, field: str):
    """Parse a user-supplied date/timestamp, rejecting bad input with 422.

    These endpoints take a raw dict, so ``datetime.fromisoformat`` used to raise
    ValueError on malformed input and surface as a 500.
    """
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    parsed = parse_date_value(value, field)
    if parsed is None:
        return None
    return datetime(parsed.year, parsed.month, parsed.day)


async def _resolve_account_by_setting(
    db: AsyncSession,
    setting_key: str,
    fallback_codes: list[str],
) -> Optional[Account]:
    """Resolve an account code from app settings first, then fallback codes
    (e.g. "3400" in the FastAPI chart vs "3200" in the gateway chart)."""
    codes = list(fallback_codes)
    try:
        configured = (await get_setting(db, setting_key, default="")).strip()
    except Exception:
        configured = ""
    if configured:
        codes = [configured] + [c for c in fallback_codes if c != configured]
    for code in codes:
        r = await db.execute(select(Account).where(Account.account_code == code).limit(1))
        acc = r.scalar_one_or_none()
        if acc:
            return acc
    return None


@router.get("/fiscal-periods")
async def list_fiscal_periods(
    is_closed: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
             "is_soft_closed": getattr(p, "is_soft_closed", False),
             "fiscal_year_id": getattr(p, "fiscal_year_id", None),
             "closed_by": p.closed_by, "closed_at": str(p.closed_at) if p.closed_at else None} for p in periods]


@router.post("/fiscal-periods")
async def create_fiscal_period(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new fiscal period"""
    require_fields(data, ["name", "start_date", "end_date"])
    period = FiscalPeriod(
        name=data["name"],
        name_en=data.get("name_en"),
        start_date=_coerce_ts(data.get("start_date"), "start_date"),
        end_date=_coerce_ts(data.get("end_date"), "end_date"),
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
    current_user=Depends(get_current_user),
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
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
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
    current_user=Depends(require_permission("POST_JOURNAL")),
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
    # Get all ledger-affecting entries in this period
    entries_result = await db.execute(
        select(JournalEntry.id)
        .where(JournalEntry.entry_date >= period.start_date)
        .where(JournalEntry.entry_date <= period.end_date)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
    )
    entry_ids = [e for e in entries_result.scalars().all()]

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
            .select_from(JournalEntryLine)
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .join(Account, JournalEntryLine.account_id == Account.id)
            .where(JournalEntry.id.in_(entry_ids))
            .where(Account.account_type.in_(["revenue", "expense"]))
            .group_by(Account.id, Account.account_type, Account.account_code)
        )

        # Build closing lines
        closing_lines = []
        retained_earnings_total = 0.0

        for balance in account_balances:
            debit = float(balance.total_debit)
            credit = float(balance.total_credit)
            net = credit - debit if balance.account_type == "revenue" else debit - credit

            if abs(net) > 0.01:
                closing_lines.append({
                    "account_id": balance.id,
                    "debit": net if balance.account_type == "revenue" else 0,
                    "credit": 0 if balance.account_type == "revenue" else net,
                })
                retained_earnings_total += net if balance.account_type == "revenue" else -net

        # Add retained earnings line (account code configurable via settings)
        if abs(retained_earnings_total) > 0.01:
            re_account = await _resolve_account_by_setting(
                db, "retained_earnings_account_code", ["3400", "3200"]
            )
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
            closing_entry.posted_by = current_user.id if hasattr(current_user, "id") else None
            closing_entry.posted_at = datetime.now()

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

    await add_audit_log(db, "FiscalPeriod", period.id, "CLOSE", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} closed successfully"}


@router.post("/fiscal-periods/{period_id}/lock")
async def lock_fiscal_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Lock a fiscal period to prevent any new entries"""
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if period.is_locked:
        raise HTTPException(status_code=400, detail="Period is already locked")

    period.is_locked = True
    await add_audit_log(db, "FiscalPeriod", period.id, "LOCK", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} locked"}


@router.post("/fiscal-periods/{period_id}/unlock")
async def unlock_fiscal_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """Unlock a fiscal period so new entries can be recorded again."""
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if not period.is_locked:
        raise HTTPException(status_code=400, detail="Period is not locked")

    period.is_locked = False
    await add_audit_log(db, "FiscalPeriod", period.id, "UNLOCK", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} unlocked"}


@router.post("/fiscal-periods/{period_id}/reopen")
async def reopen_fiscal_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """
    Reopen a closed fiscal period: clears the closed/locked flags so postings
    may be adjusted again. This is a controlled correction step and is audited.
    """
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    if not period.is_closed and not period.is_locked:
        raise HTTPException(status_code=400, detail="Period is already open")

    period.is_closed = False
    period.is_locked = False
    period.closed_by = None
    period.closed_at = None
    await add_audit_log(db, "FiscalPeriod", period.id, "REOPEN", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} reopened"}


@router.post("/fiscal-periods/{period_id}/soft-close")
async def soft_close_fiscal_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("POST_JOURNAL")),
):
    """Soft-close a period: blocks routine postings but keeps it open for year-end adjustments."""
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")
    period.is_soft_closed = True
    await add_audit_log(db, "FiscalPeriod", period.id, "SOFT_CLOSE", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} soft-closed"}


@router.post("/fiscal-periods/{period_id}/reopen-soft")
async def reopen_soft_closed_period(
    period_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """Undo a soft-close: routine postings are allowed again."""
    result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == period_id))
    period = result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")
    period.is_soft_closed = False
    await add_audit_log(db, "FiscalPeriod", period.id, "REOPEN_SOFT", current_user,
                        {"period_name": period.name})
    await db.commit()
    return {"success": True, "message": f"Period {period.name} reopened for postings"}


# =============================================================================
# Fiscal Years
# =============================================================================

def _fiscal_year_dict(fy: FiscalYear) -> dict:
    return {
        "id": fy.id, "name": fy.name, "name_en": fy.name_en,
        "start_date": str(fy.start_date), "end_date": str(fy.end_date),
        "is_closed": fy.is_closed, "closed_by": fy.closed_by,
        "closed_at": str(fy.closed_at) if fy.closed_at else None,
        "opening_balances_posted": fy.opening_balances_posted,
        "notes": fy.notes, "created_at": str(fy.created_at) if fy.created_at else None,
    }


@router.get("/fiscal-years")
async def list_fiscal_years(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List fiscal years with period counts."""
    result = await db.execute(select(FiscalYear).order_by(FiscalYear.start_date.desc()))
    years = result.scalars().all()
    out = []
    for fy in years:
        total = (await db.execute(
            select(func.count(FiscalPeriod.id)).where(FiscalPeriod.fiscal_year_id == fy.id)
        )).scalar() or 0
        closed = (await db.execute(
            select(func.count(FiscalPeriod.id)).where(
                FiscalPeriod.fiscal_year_id == fy.id, FiscalPeriod.is_closed.is_(True)
            )
        )).scalar() or 0
        d = _fiscal_year_dict(fy)
        d["period_count"] = total
        d["closed_period_count"] = closed
        out.append(d)
    return out


@router.post("/fiscal-years")
async def create_fiscal_year(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """Create a fiscal year. Start/end dates are arbitrary (not assumed to start in January)."""
    try:
        start_date = data["start_date"] if isinstance(data["start_date"], datetime) else datetime.fromisoformat(str(data["start_date"]))
        end_date = data["end_date"] if isinstance(data["end_date"], datetime) else datetime.fromisoformat(str(data["end_date"]))
    except (KeyError, ValueError) as e:
        raise HTTPException(status_code=422, detail=f"Invalid date format: {e}")
    if end_date <= start_date:
        raise HTTPException(status_code=422, detail="End date must be after start date")

    overlap = await db.execute(
        select(FiscalYear).where(
            FiscalYear.start_date <= end_date, FiscalYear.end_date >= start_date
        ).limit(1)
    )
    if overlap.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Overlapping fiscal year already exists")

    fy = FiscalYear(
        name=data.get("name") or f"{start_date.year} - {end_date.year}",
        name_en=data.get("name_en"),
        start_date=start_date, end_date=end_date,
        is_closed=False, opening_balances_posted=False,
        notes=data.get("notes"), created_at=datetime.now(),
    )
    db.add(fy)
    await db.flush()
    await add_audit_log(db, "FiscalYear", fy.id, "CREATE", current_user,
                        {"name": fy.name, "start_date": str(fy.start_date), "end_date": str(fy.end_date)})
    await db.commit()
    await db.refresh(fy)
    return {"id": fy.id, "name": fy.name, "message": "Fiscal year created"}


@router.post("/fiscal-years/{fiscal_year_id}/generate-periods")
async def generate_fiscal_periods(
    fiscal_year_id: int,
    periods: int = Query(12, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """
    Generate monthly fiscal periods across the fiscal year. periods=1 creates a
    single period spanning the whole year. Existing periods for this year are
    kept and only missing slots are created.
    """
    result = await db.execute(select(FiscalYear).where(FiscalYear.id == fiscal_year_id))
    fy = result.scalar_one_or_none()
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found")

    existing = (await db.execute(
        select(FiscalPeriod.id).where(FiscalPeriod.fiscal_year_id == fiscal_year_id)
    )).scalars().all()
    created = 0
    def _add_months(d: datetime, n: int) -> datetime:
        m = d.month - 1 + n
        y = d.year + m // 12
        m = m % 12 + 1
        return datetime(y, m, 1)

    if periods == 1:
        overlap = await db.execute(
            select(FiscalPeriod.id).where(
                FiscalPeriod.fiscal_year_id == fiscal_year_id,
                FiscalPeriod.start_date == fy.start_date, FiscalPeriod.end_date == fy.end_date,
            ).limit(1)
        )
        if not overlap.scalar_one_or_none():
            db.add(FiscalPeriod(
                fiscal_year_id=fy.id, name=f"{fy.name} - Full year", name_en=f"{fy.name} - Full year",
                start_date=fy.start_date, end_date=fy.end_date,
                is_closed=False, is_locked=False, is_soft_closed=False, created_at=datetime.now(),
            ))
            created += 1
    elif periods == 12 and fy.start_date.day == 1:
        for i in range(12):
            seg_start = _add_months(fy.start_date, i)
            seg_end = _add_months(fy.start_date, i + 1) - timedelta(days=1)
            if seg_end > fy.end_date:
                seg_end = fy.end_date
            if seg_end < seg_start:
                continue
            overlap = await db.execute(
                select(FiscalPeriod.id).where(
                    FiscalPeriod.fiscal_year_id == fiscal_year_id,
                    FiscalPeriod.start_date >= seg_start,
                    FiscalPeriod.end_date <= seg_end,
                ).limit(1)
            )
            if not overlap.scalar_one_or_none():
                db.add(FiscalPeriod(
                    fiscal_year_id=fy.id,
                    name=f"{fy.name} {seg_start.strftime('%Y-%m')}",
                    start_date=seg_start,
                    end_date=seg_end,
                    is_closed=False, is_locked=False, is_soft_closed=False, created_at=datetime.now(),
                ))
                created += 1
    else:
        delta_days = (fy.end_date - fy.start_date).days
        for i in range(periods):
            seg_start = fy.start_date + timedelta(days=delta_days * i // periods)
            seg_end = fy.start_date + timedelta(days=delta_days * (i + 1) // periods)
            seg_start_d = seg_start.date()
            seg_end_d = seg_end.date()
            overlap = await db.execute(
                select(FiscalPeriod.id).where(
                    FiscalPeriod.fiscal_year_id == fiscal_year_id,
                    FiscalPeriod.start_date >= datetime.combine(seg_start_d, datetime.min.time()),
                    FiscalPeriod.end_date <= datetime.combine(seg_end_d, datetime.min.time()),
                ).limit(1)
            )
            if not overlap.scalar_one_or_none():
                db.add(FiscalPeriod(
                    fiscal_year_id=fy.id,
                    name=f"{seg_start_d.strftime('%Y-%m')}",
                    start_date=datetime.combine(seg_start_d, datetime.min.time()),
                    end_date=datetime.combine(seg_end_d, datetime.min.time()),
                    is_closed=False, is_locked=False, is_soft_closed=False, created_at=datetime.now(),
                ))
                created += 1
    await add_audit_log(db, "FiscalYear", fy.id, "GENERATE_PERIODS", current_user,
                        {"periods": periods, "created": created, "existing": len(existing)})
    await db.commit()
    return {"success": True, "message": f"{created} periods created (existing: {len(existing)})", "created": created}


@router.post("/fiscal-years/{fiscal_year_id}/closing")
async def close_fiscal_year(
    fiscal_year_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("POST_JOURNAL")),
):
    """
    Year-end closing: aggregate revenue/expense balances for the whole fiscal
    year into retained earnings, post the closing entry, and mark the year closed.
    """
    result = await db.execute(select(FiscalYear).where(FiscalYear.id == fiscal_year_id))
    fy = result.scalar_one_or_none()
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    if fy.is_closed:
        raise HTTPException(status_code=400, detail="Fiscal year is already closed")

    entries_result = await db.execute(
        select(JournalEntry.id).where(
            JournalEntry.entry_date >= fy.start_date,
            JournalEntry.entry_date <= fy.end_date,
            JournalEntry.status.in_(_LEDGER_STATUSES),
        )
    )
    entry_ids = [e for e in entries_result.scalars().all()]

    retained_earnings_total = 0.0
    closing_lines = []
    if entry_ids:
        account_balances = await db.execute(
        select(
            Account.id, Account.account_type, Account.account_code,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .select_from(JournalEntryLine)
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.id.in_(entry_ids), JournalEntry.status.in_(_LEDGER_STATUSES))
        .where(Account.account_type.in_(["revenue", "expense"]))
        .group_by(Account.id, Account.account_type, Account.account_code)
    )
    for b in account_balances:
        debit = float(b.total_debit)
        credit = float(b.total_credit)
        net = credit - debit if b.account_type == "revenue" else debit - credit
        if abs(net) > 0.01:
            closing_lines.append({
                "account_id": b.id,
                "debit": net if b.account_type == "revenue" else 0,
                "credit": 0 if b.account_type == "revenue" else net,
            })
            retained_earnings_total += net if b.account_type == "revenue" else -net

    created_entry_id = None
    if abs(retained_earnings_total) > 0.01:
        re_account = await _resolve_account_by_setting(db, "retained_earnings_account_code", ["3400", "3200"])
        if re_account:
            closing_lines.append({
                "account_id": re_account.id,
                "debit": 0 if retained_earnings_total > 0 else abs(retained_earnings_total),
                "credit": retained_earnings_total if retained_earnings_total > 0 else 0,
            })

    if closing_lines:
        # period_closing_entries.fiscal_period_id is NOT NULL - resolve the
        # period this year-end closing is recorded against (the year's last
        # period), falling back to any period covering the year end.
        closing_period_id = None
        period_result = await db.execute(
            select(FiscalPeriod.id).where(FiscalPeriod.fiscal_year_id == fy.id)
            .order_by(FiscalPeriod.end_date.desc()).limit(1)
        )
        closing_period_id = period_result.scalar_one_or_none()
        if closing_period_id is None:
            period_result = await db.execute(
                select(FiscalPeriod.id).where(
                    FiscalPeriod.start_date <= fy.end_date,
                    FiscalPeriod.end_date >= fy.end_date,
                ).order_by(FiscalPeriod.end_date.desc()).limit(1)
            )
            closing_period_id = period_result.scalar_one_or_none()

        closing_entry = JournalEntry(
            entry_number=f"YE-{fy.name}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            entry_date=fy.end_date,
            description=f"Year-end closing entries for {fy.name}",
            status="Posted",
            created_by=current_user.id if hasattr(current_user, "id") else None,
            posted_by=current_user.id if hasattr(current_user, "id") else None,
            posted_at=datetime.now(),
            company_id=None,
            created_at=datetime.now(),
        )
        db.add(closing_entry)
        await db.flush()
        for line in closing_lines:
            db.add(JournalEntryLine(
                journal_entry_id=closing_entry.id,
                account_id=line["account_id"],
                debit=line["debit"], credit=line["credit"], created_at=datetime.now(),
            ))
        created_entry_id = closing_entry.id
        db.add(PeriodClosingEntry(
            fiscal_period_id=closing_period_id,
            closing_type="YEAR_END",
            description=f"Year-end closing for {fy.name}",
            total_debit=sum(l["debit"] for l in closing_lines),
            total_credit=sum(l["credit"] for l in closing_lines),
            status="POSTED", journal_entry_id=closing_entry.id,
            posted_by=current_user.id if hasattr(current_user, "id") else None,
            posted_at=datetime.now(), created_at=datetime.now(),
        ))

    fy.is_closed = True
    fy.closed_by = current_user.id if hasattr(current_user, "id") else None
    fy.closed_at = datetime.now()
    await add_audit_log(db, "FiscalYear", fy.id, "CLOSE", current_user,
                        {"name": fy.name, "journal_entry_id": created_entry_id})
    await db.commit()
    return {"success": True, "message": f"Fiscal year {fy.name} closed",
            "journal_entry_id": created_entry_id, "retained_earnings": retained_earnings_total}


@router.post("/fiscal-years/{fiscal_year_id}/open-next-year")
async def open_next_fiscal_year(
    fiscal_year_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("POST_JOURNAL")),
):
    """
    Carry forward balance-sheet (asset/liability/equity) balances of a closed
    year into an opening-entry for the immediately following period of the next
    fiscal year. Creates/returns the opening journal entry and marks
    ``opening_balances_posted``.
    """
    result = await db.execute(select(FiscalYear).where(FiscalYear.id == fiscal_year_id))
    fy = result.scalar_one_or_none()
    if not fy:
        raise HTTPException(status_code=404, detail="Fiscal year not found")
    if not fy.is_closed:
        raise HTTPException(status_code=400, detail="Fiscal year must be closed before opening the next year")

    entries_result = await db.execute(
        select(JournalEntry.id).where(
            JournalEntry.entry_date >= fy.start_date,
            JournalEntry.entry_date <= fy.end_date,
            JournalEntry.status.in_(_LEDGER_STATUSES),
        )
    )
    entry_ids = [e for e in entries_result.scalars().all()]

    lines = []
    if entry_ids:
        balances = await db.execute(
            select(
                Account.id, Account.account_code, Account.account_name,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.id.in_(entry_ids), JournalEntry.status.in_(_LEDGER_STATUSES))
            .where(Account.account_type.in_(["asset", "liability", "equity"]))
            .group_by(Account.id, Account.account_code, Account.account_name)
        )
        for b in balances:
            net = float(b.total_debit) - float(b.total_credit)
            if abs(net) > 0.01:
                lines.append({
                    "account_id": b.id,
                    "debit": net if net > 0 else 0,
                    "credit": abs(net) if net < 0 else 0,
                    "description": f"Opening balance carried forward from {fy.name}",
                })

    # Find next period: the earliest period after this year
    next_period = await db.execute(
        select(FiscalPeriod).where(FiscalPeriod.start_date > fy.end_date)
        .order_by(FiscalPeriod.start_date.asc()).limit(1)
    )
    np = next_period.scalar_one_or_none()

    entry_id = None
    if lines:
        today = datetime.now()
        opening_entry = JournalEntry(
            entry_number=f"OB-{fy.name}-{today.strftime('%Y%m%d%H%M%S')}",
            entry_date=(np.start_date if np else fy.end_date),
            fiscal_period_id=np.id if np else None,
            reference_type="YEAR_OPENING",
            reference_id=fy.id,
            description=f"Opening balances for fiscal year ending {fy.name}",
            status="Posted",
            created_by=current_user.id if hasattr(current_user, "id") else None,
            posted_by=current_user.id if hasattr(current_user, "id") else None,
            posted_at=today,
            company_id=None,
            created_at=today,
        )
        db.add(opening_entry)
        await db.flush()
        for line in lines:
            db.add(JournalEntryLine(
                journal_entry_id=opening_entry.id,
                account_id=line["account_id"],
                description=line["description"],
                debit=line["debit"], credit=line["credit"], created_at=today,
            ))
        entry_id = opening_entry.id

    fy.opening_balances_posted = True
    await add_audit_log(db, "FiscalYear", fy.id, "OPEN_NEXT_YEAR", current_user,
                        {"name": fy.name, "journal_entry_id": entry_id, "lines": len(lines)})
    await db.commit()
    return {"success": True, "message": "Opening balances carried forward",
            "journal_entry_id": entry_id, "lines": len(lines)}
