"""
AI / Analytics Module.

Reusable analytical endpoints that work on real ledger/operational data:

  GET /analysis/summary                     — key financial KPIs
  GET /analysis/cash-flow-forecast          — cash flow projection
  GET /analysis/anomalies                   — anomaly detection on journal entries
  GET /analysis/duplicates                  — duplicate document detection
  GET /analysis/account-suggestions         — chart-of-accounts suggestion by keywords
  GET /analysis/reconciliation-suggestions  — assisted bank reconciliation matching

All endpoints are read-only and expose underlying data so the results stay
auditable (the AI acts as an assistant, never mutating the ledger).
"""

import logging
import re
import statistics
from datetime import UTC, datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.models.payments import Bank, BankTransaction, CustomerPayment
from app.models.sales import Sale
from app.models.purchases import Purchase
from app.models.user import User
from app.routers.accounting import _LEDGER_STATUSES
from app.services.settings_service import get_setting
from app.utils.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


async def _base_currency(db: AsyncSession) -> str:
    return (await get_setting(db, "base_currency", default="SAR")).strip()


async def _posted_lines_breakdown(
    db: AsyncSession, start: datetime, end: datetime
) -> tuple[float, float, float, float]:
    """Return (revenue, expenses, operating_in, operating_out) within a window."""
    rows = (await db.execute(
        select(
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
        .where(JournalEntry.entry_date >= start)
        .where(JournalEntry.entry_date <= end)
        .group_by(Account.account_type)
    )).all()

    revenue = expenses = _in = _out = 0.0
    for acc_type, debit, credit in rows:
        debit, credit = float(debit), float(credit)
        if acc_type == "revenue":
            revenue += credit - debit
            _in += credit - debit
        elif acc_type == "expense":
            expenses += debit - credit
            _out += debit - credit
    return revenue, expenses, _in, _out


@router.get("/summary")
async def analytics_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Key financial KPIs from real data."""
    currency = await _base_currency(db)
    now = datetime.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    year_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    rev_m, exp_m, _, _ = await _posted_lines_breakdown(db, month_start, now)
    rev_y, exp_y, _, _ = await _posted_lines_breakdown(db, year_start, now)

    bank_rows = (await db.execute(
        select(func.coalesce(func.sum(Bank.current_balance), 0))
    )).scalar()
    bank_balance = float(bank_rows or 0)

    ar_row = (await db.execute(
        select(
            func.coalesce(func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0)
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
        .where(Account.account_type == "asset")
        .where(or_(
            func.lower(Account.account_name).like("%receivable%"),
            func.lower(Account.account_name_en).like("%receivable%"),
            func.lower(Account.account_name_ar).like("%receivable%"),
        ))
    )).scalar()
    receivables = abs(float(ar_row or 0))

    ap_row = (await db.execute(
        select(
            func.coalesce(func.sum(JournalEntryLine.credit - JournalEntryLine.debit), 0)
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
        .where(Account.account_type == "liability")
        .where(or_(
            func.lower(Account.account_name).like("%payable%"),
            func.lower(Account.account_name_en).like("%payable%"),
            func.lower(Account.account_name_ar).like("%payable%"),
        ))
    )).scalar()
    payables = abs(float(ap_row or 0))

    # Pending documents (workflow not approved yet)
    pending_sales = (await db.execute(
        select(func.count()).select_from(Sale).where(Sale.workflow_state == "submitted")
    )).scalar() or 0
    pending_purchases = (await db.execute(
        select(func.count()).select_from(Purchase).where(Purchase.workflow_state == "submitted")
    )).scalar() or 0

    return {
        "currency": currency,
        "revenue_month": round(rev_m, 2),
        "expenses_month": round(exp_m, 2),
        "net_profit_month": round(rev_m - exp_m, 2),
        "revenue_year": round(rev_y, 2),
        "expenses_year": round(exp_y, 2),
        "net_profit_year": round(rev_y - exp_y, 2),
        "bank_balance": round(bank_balance, 2),
        "receivables": round(receivables, 2),
        "payables": round(payables, 2),
        "pending_sales": pending_sales,
        "pending_purchases": pending_purchases,
        "as_of": now.isoformat(),
    }


@router.get("/cash-flow-forecast")
async def cash_flow_forecast(
    months: int = Query(6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Simple cash flow projection.

    Base: average monthly operating inflow/outflow of the last 3 full months.
    Then projected months include the base drift plus any known due collections
    (submitted sales) and due obligations (submitted purchases) per month.
    """
    currency = await _base_currency(db)
    now = datetime.now()

    # Average operating in/out from the last 3 calendar months
    start_m = (now.replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(days=31 * 2))
    start_d = start_m.replace(day=1)
    month_col = func.date_trunc("month", JournalEntry.entry_date).label("m")
    avg_rows = (await db.execute(
        select(
            month_col,
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
        .where(JournalEntry.entry_date >= start_d)
        .where(JournalEntry.entry_date < now.replace(day=1))
        .group_by(month_col, Account.account_type)
    )).all()

    in_total = out_total = 0.0
    months_seen = set()
    for ts, acc_type, debit, credit in avg_rows:
        months_seen.add(ts)
        debit, credit = float(debit), float(credit)
        if acc_type == "revenue":
            in_total += credit - debit
        elif acc_type == "expense":
            out_total += debit - credit
    count = max(len(months_seen), 1)
    avg_in = in_total / count
    avg_out = out_total / count

    # Known upcoming payable / receivable amounts per month
    pending_sales = (await db.execute(select(Sale).where(Sale.workflow_state == "submitted"))).scalars().all()
    pending_purchases = (await db.execute(
        select(Purchase).where(Purchase.workflow_state == "submitted")
    )).scalars().all()

    bank_balance = float((await db.execute(
        select(func.coalesce(func.sum(Bank.current_balance), 0))
    )).scalar() or 0)
    cash_balance = bank_balance

    projections = []
    for i in range(months):
        m = now.replace(day=1) + timedelta(days=32 * i)
        due_in = sum(
            float(s.final_amount or 0)
            for s in pending_sales
            if s.created_at and s.created_at.month == m.month and s.created_at.year == m.year
        )
        due_out = sum(
            float(p.final_amount or 0)
            for p in pending_purchases
            if p.created_at and p.created_at.month == m.month and p.created_at.year == m.year
        )
        forecast_in = avg_in + due_in
        forecast_out = avg_out + due_out
        cash_balance += forecast_in - forecast_out
        projections.append({
            "month": m.strftime("%Y-%m"),
            "forecast_in": round(forecast_in, 2),
            "forecast_out": round(forecast_out, 2),
            "net": round(forecast_in - forecast_out, 2),
            "closing_balance": round(cash_balance, 2),
            "known_receivables": round(due_in, 2),
            "known_payables": round(due_out, 2),
        })

    return {
        "currency": currency,
        "starting_balance": round(bank_balance, 2),
        "average_monthly_in": round(avg_in, 2),
        "average_monthly_out": round(avg_out, 2),
        "projections": projections,
    }


@router.get("/anomalies")
async def anomaly_detection(
    days: int = Query(90, ge=1, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Flag posted journal entries that are unusually large or odd."""
    now = datetime.now()
    cutoff = now - timedelta(days=days)

    entries = (await db.execute(
        select(JournalEntry, func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total"))
        .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntry.status == "Posted")
        .where(JournalEntry.entry_date >= cutoff)
        .group_by(JournalEntry.id)
        .order_by(func.coalesce(func.sum(JournalEntryLine.debit), 0).desc())
        .limit(50)
    )).all()

    if not entries:
        return {"notes": "No posted journal entries in the window", "anomalies": []}

    values = sorted(float(total) for _, total in entries)
    median = statistics.median(values)
    mean = statistics.mean(values)
    threshold = max(mean + 2.0 * (statistics.pstdev(values) if len(values) > 1 else 0), median * 5)

    anomalies = []
    for entry, total in entries:
        total_f = float(total)
        row = {
            "type": None,
            "severity": "low",
            "entry_id": entry.id,
            "entry_number": entry.entry_number,
            "entry_date": str(entry.entry_date.date()),
            "description": entry.description,
            "amount": round(total_f, 2),
            "reason": None,
        }
        if total_f > threshold:
            row["type"] = "unusual_value"
            row["severity"] = "high"
            row["reason"] = (
                f"amount {round(total_f, 2)} exceeds statistical threshold {round(threshold, 2)}"
            )
        elif entry.created_at and entry.created_at.hour >= 22 or (entry.created_at and entry.created_at.hour < 5):
            row["type"] = "odd_hour"
            row["severity"] = "medium"
            row["reason"] = f"created at {entry.created_at.strftime('%H:%M')}"
        if row["type"]:
            anomalies.append(row)

    return {
        "notes": f"Based on {len(entries)} posted entries, median {round(median, 2)}, mean {round(mean, 2)}",
        "anomalies": anomalies,
    }


@router.get("/duplicates")
async def duplicate_detection(
    days: int = Query(120, ge=1, le=730),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Find likely duplicate documents:
      * journal entries sharing exact amount + date
      * customer payments sharing amount + date + method
    """
    cutoff = datetime.now() - timedelta(days=days)

    # Journal entries: group by (date, rounded total) in Python
    je_totals = (await db.execute(
        select(
            JournalEntry.id, JournalEntry.entry_date,
            func.coalesce(func.sum(JournalEntryLine.debit), 0)
        )
        .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntry.entry_date >= cutoff)
        .group_by(JournalEntry.id)
    )).all()

    buckets: dict[tuple, list[int]] = {}
    for je_id, je_date, total in je_totals:
        key = ((je_date.date() if je_date else None), round(float(total), 2))
        buckets.setdefault(key, []).append(je_id)

    je_dupes = [
        {"entity": "JournalEntry", "date": str(k[0]), "amount": k[1],
         "count": len(v), "ids": v}
        for k, v in sorted(buckets.items(), key=lambda kv: -len(kv[1]))
        if len(v) > 1
    ][:20]

    # Customer payments: group by (date, rounded amount, method) in Python
    cp_rows = (await db.execute(
        select(CustomerPayment.id, CustomerPayment.payment_date,
               CustomerPayment.amount, CustomerPayment.payment_method)
        .where(CustomerPayment.payment_date >= cutoff)
    )).all()

    cp_buckets: dict[tuple, list[int]] = {}
    for cid, cdate, camount, cmethod in cp_rows:
        key = ((cdate.date() if cdate else None), round(float(camount), 2), cmethod)
        cp_buckets.setdefault(key, []).append(cid)

    cp_dupes = [
        {"entity": "CustomerPayment", "date": str(k[0]), "amount": k[1],
         "method": k[2], "count": len(v), "ids": v}
        for k, v in sorted(cp_buckets.items(), key=lambda kv: -len(kv[1]))
        if len(v) > 1
    ][:20]

    return {"journal_entries": je_dupes, "customer_payments": cp_dupes}


@router.get("/account-suggestions")
async def account_suggestions(
    text: str = Query(..., min_length=2),
    type: Optional[str] = Query(None),
    limit: int = Query(8, ge=1, le=25),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Suggest chart-of-accounts entries matching free-text description keywords.
    Use: pass the description of a transaction; get likely accounts back.
    """
    tokens = [t for t in text.lower().split() if len(t) >= 2]
    if not tokens:
        raise HTTPException(status_code=400, detail="Provide a description with at least 2 keywords")

    q = select(Account).where(Account.is_active.is_(True))
    if type:
        q = q.where(Account.account_type == type)

    accounts = (await db.execute(q)).scalars().all()

    scored = []
    for acc in accounts:
        haystacks = [acc.account_name, acc.account_name_en or "", acc.account_name_ar or "", acc.account_code]
        hay = " ".join(haystacks).lower()
        hits = 0
        for t in tokens:
            if re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", hay):
                hits += 1
        if hits:
            scored.append({
                "id": acc.id,
                "code": acc.account_code,
                "name": acc.account_name,
                "name_en": acc.account_name_en,
                "name_ar": acc.account_name_ar,
                "type": acc.account_type,
                "score": hits,
            })

    scored.sort(key=lambda a: (-a["score"], a["code"]))
    return {"query": text, "suggestions": scored[:limit]}


@router.get("/reconciliation-suggestions")
async def reconciliation_suggestions(
    days: int = Query(60, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Assisted bank reconciliation: propose matching bank transactions to posted
    journal entries by reversed amount and close dates (within 7 days).
    Human must confirm before matching is applied by the reconciliation module.
    """
    cutoff = datetime.now() - timedelta(days=days)

    txns = (await db.execute(
        select(BankTransaction).where(BankTransaction.transaction_date >= cutoff)
        .order_by(BankTransaction.transaction_date)
        .limit(300)
    )).scalars().all()

    suggestions = []
    for txn in txns:
        amount = abs(float(txn.amount or 0))
        if amount <= 0:
            continue
        candidates = (await db.execute(
            select(
                JournalEntry, JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("d"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("c")
            )
            .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.status == "Posted")
            .where(JournalEntry.entry_date >= (txn.transaction_date - timedelta(days=7)))
            .where(JournalEntry.entry_date <= (txn.transaction_date + timedelta(days=7)))
            .group_by(JournalEntry.id, JournalEntryLine.account_id)
        )).all()

        best = None
        for je, account_id, d, c in candidates:
            line_amount = max(float(d), float(c))
            if abs(line_amount - amount) < 1e-6:
                best = {"journal_entry_id": je.id, "entry_number": je.entry_number,
                        "entry_date": str(je.entry_date.date()), "account_id": account_id}
                break
        if best:
            suggestions.append({
                "bank_transaction_id": txn.id,
                "bank": txn.bank_id,
                "amount": amount,
                "type": txn.transaction_type,
                "transaction_date": str(txn.transaction_date.date()) if txn.transaction_date else None,
                "description": txn.description,
                "reference": txn.reference,
                "suggested": best,
            })

    return {"suggestion_count": len(suggestions), "suggestions": suggestions}