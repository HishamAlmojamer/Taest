"""
Currency and Exchange Rate management endpoints.
"""

from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.currency import Currency, ExchangeRate
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.routers.accounting import _LEDGER_STATUSES
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log
from app.utils.validation import require_fields, parse_date_value
from app.services.settings_service import get_setting

router = APIRouter()


def _coerce_ts(value, field: str):
    """Parse a user-supplied timestamp, rejecting bad input with 422.

    These endpoints accept a raw dict, so ``datetime.fromisoformat`` used to
    raise ValueError on bad input and surface as a 500.
    """
    if value is None or value == "":
        return None
    parsed = parse_date_value(value, field)
    if parsed is None:
        return None
    return datetime(parsed.year, parsed.month, parsed.day)


async def _base_currency_code(db: AsyncSession) -> str:
    base = (await get_setting(db, "base_currency", default="SAR")).strip()
    if base:
        return base
    result = await db.execute(select(Currency).where(Currency.is_base_currency == True).limit(1))
    cur = result.scalar_one_or_none()
    return cur.code if cur else "SAR"


async def _latest_rate(db: AsyncSession, from_code: str, to_code: str, as_of) -> Optional[float]:
    """Latest active rate from_code->to_code as of date (supports reversed rows)."""
    if from_code == to_code:
        return 1.0
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.from_currency_code == from_code)
        .where(ExchangeRate.to_currency_code == to_code)
        .where(ExchangeRate.is_active == True)
        .where(ExchangeRate.effective_date <= as_of)
        .order_by(desc(ExchangeRate.effective_date))
        .limit(1)
    )
    rate = result.scalar_one_or_none()
    if rate:
        return float(rate.rate)
    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.from_currency_code == to_code)
        .where(ExchangeRate.to_currency_code == from_code)
        .where(ExchangeRate.is_active == True)
        .where(ExchangeRate.effective_date <= as_of)
        .order_by(desc(ExchangeRate.effective_date))
        .limit(1)
    )
    rate = result.scalar_one_or_none()
    if rate:
        r = float(rate.rate)
        return 1.0 / r if r else None
    return None


async def _fx_differences(db: AsyncSession, as_of: datetime) -> list[dict]:
    """Compute unrealized FX differences on balance-sheet accounts
    denominated in non-base currencies up to `as_of`.

    Stored lines keep base-currency debit/credit plus the line rate; the
    foreign-currency amount is recovered as base/rate and re-measured at the
    revaluation-date rate."""
    base_code = await _base_currency_code(db)
    acc_result = await db.execute(
        select(Account.id, Account.account_code, Account.account_name, Account.account_type)
        .where(Account.is_active == True, Account.account_type.in_(["asset", "liability", "equity"]))
    )
    accounts = acc_result.all()
    acc_map = {a.id: a for a in accounts}
    if not acc_map:
        return []

    result = await db.execute(
        select(
            JournalEntryLine.account_id,
            JournalEntryLine.currency_id,
            func.coalesce(func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0).label("base_net"),
            func.coalesce(func.sum(
                (JournalEntryLine.debit - JournalEntryLine.credit) /
                func.nullif(func.coalesce(JournalEntryLine.currency_rate, 1), 0)
            ), 0).label("foreign_net"),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(
            JournalEntry.status.in_(_LEDGER_STATUSES),
            JournalEntryLine.currency_id.isnot(None),
            JournalEntry.entry_date <= as_of,
        )
        .group_by(JournalEntryLine.account_id, JournalEntryLine.currency_id)
    )
    rows = result.all()

    diffs = []
    for row in rows:
        acc = acc_map.get(row.account_id)
        if not acc:
            continue
        cur = await db.execute(select(Currency).where(Currency.id == row.currency_id))
        currency = cur.scalar_one_or_none()
        if not currency or currency.code == base_code:
            continue
        rate = await _latest_rate(db, currency.code, base_code, as_of)
        if not rate or rate <= 0:
            continue
        base_net = float(row.base_net or 0)
        foreign_net = float(row.foreign_net or 0)
        revalued = foreign_net * rate
        diff = revalued - base_net
        if abs(diff) < 0.01:
            continue
        diffs.append({
            "account_id": acc.id,
            "account_code": acc.account_code,
            "account_name": acc.account_name,
            "account_type": acc.account_type,
            "currency_code": currency.code,
            "foreign_balance": round(foreign_net, 4),
            "recorded_base": round(base_net, 4),
            "rate": round(rate, 6),
            "revaluated_base": round(revalued, 4),
            "difference": round(diff, 4),
        })
    return diffs


# =============================================================================
# Currency Endpoints
# =============================================================================

@router.get("/currencies")
async def list_currencies(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all currencies"""
    query = select(Currency).order_by(Currency.code)
    if is_active is not None:
        query = query.where(Currency.is_active == is_active)
    result = await db.execute(query)
    currencies = result.scalars().all()
    return [{"id": c.id, "code": c.code, "name": c.name, "name_ar": c.name_ar,
             "symbol": c.symbol, "decimal_places": c.decimal_places,
             "is_base_currency": c.is_base_currency, "is_active": c.is_active} for c in currencies]


@router.post("/currencies")
async def create_currency(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new currency"""
    # Check if code already exists
    existing = await db.execute(select(Currency).where(Currency.code == data.get("code")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Currency code already exists")

    # If this is set as base currency, unset others
    if data.get("is_base_currency"):
        await db.execute(
            Currency.__table__.update().where(Currency.is_base_currency == True).values(is_base_currency=False)
        )
    require_fields(data, ["code", "name"])
    currency = Currency(
        code=data["code"],
        name=data["name"],
        name_ar=data.get("name_ar"),
        symbol=data.get("symbol"),
        decimal_places=data.get("decimal_places", 2),
        is_base_currency=data.get("is_base_currency", False),
        is_active=data.get("is_active", True),
        created_at=datetime.now(),
    )
    db.add(currency)
    await db.commit()
    await db.refresh(currency)
    return {"id": currency.id, "code": currency.code, "name": currency.name}


@router.put("/currencies/{currency_id}")
async def update_currency(
    currency_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a currency"""
    result = await db.execute(select(Currency).where(Currency.id == currency_id))
    currency = result.scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")

    # If this is set as base currency, unset others
    if data.get("is_base_currency") and not currency.is_base_currency:
        await db.execute(
            Currency.__table__.update().where(Currency.is_base_currency == True).values(is_base_currency=False)
        )

    for key, value in data.items():
        if hasattr(currency, key):
            setattr(currency, key, value)
    await db.commit()
    return {"success": True, "message": "Currency updated"}


@router.delete("/currencies/{currency_id}")
async def delete_currency(
    currency_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a currency (soft delete)"""
    result = await db.execute(select(Currency).where(Currency.id == currency_id))
    currency = result.scalar_one_or_none()
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    if currency.is_base_currency:
        raise HTTPException(status_code=400, detail="Cannot delete base currency")

    currency.is_active = False
    await db.commit()
    return {"success": True, "message": "Currency deactivated"}


# =============================================================================
# Exchange Rate Endpoints
# =============================================================================

@router.get("/exchange-rates")
async def list_exchange_rates(
    from_currency: Optional[str] = Query(None),
    to_currency: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List exchange rates"""
    query = select(ExchangeRate).order_by(desc(ExchangeRate.effective_date))
    if from_currency:
        query = query.where(ExchangeRate.from_currency_code == from_currency)
    if to_currency:
        query = query.where(ExchangeRate.to_currency_code == to_currency)
    result = await db.execute(query)
    rates = result.scalars().all()
    return [{"id": r.id, "from_currency_code": r.from_currency_code,
             "to_currency_code": r.to_currency_code, "rate": r.rate,
             "effective_date": str(r.effective_date), "is_active": r.is_active} for r in rates]


@router.get("/exchange-rates/convert")
async def convert_currency(
    amount: float = Query(...),
    from_currency: str = Query(...),
    to_currency: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Convert amount from one currency to another using latest rate"""
    if from_currency == to_currency:
        return {"amount": amount, "from_currency": from_currency, "to_currency": to_currency, "rate": 1.0}

    result = await db.execute(
        select(ExchangeRate)
        .where(ExchangeRate.from_currency_code == from_currency)
        .where(ExchangeRate.to_currency_code == to_currency)
        .where(ExchangeRate.is_active == True)
        .order_by(desc(ExchangeRate.effective_date))
        .limit(1)
    )
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail=f"Exchange rate not found for {from_currency} to {to_currency}")

    converted_amount = amount * rate.rate
    return {
        "amount": amount,
        "from_currency": from_currency,
        "to_currency": to_currency,
        "rate": rate.rate,
        "converted_amount": round(converted_amount, 4),
    }


@router.post("/exchange-rates")
async def create_exchange_rate(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new exchange rate"""
    require_fields(data, ["from_currency_code", "to_currency_code", "rate"])
    rate = ExchangeRate(
        from_currency_code=data["from_currency_code"],
        to_currency_code=data["to_currency_code"],
        rate=data["rate"],
        effective_date=_coerce_ts(data.get("effective_date"), "effective_date") or datetime.now(),
        expiry_date=_coerce_ts(data.get("expiry_date"), "expiry_date"),
        is_active=data.get("is_active", True),
        created_by=current_user.id if hasattr(current_user, "id") else None,
        created_at=datetime.now(),
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return {"id": rate.id, "message": "Exchange rate created"}


# =============================================================================
# FX Revaluation (multi-currency period-end)
# =============================================================================

async def _parse_as_of(data: dict) -> datetime:
    as_of_str = data.get("as_of_date")
    if not as_of_str:
        return datetime.now(UTC).replace(tzinfo=None)
    try:
        return datetime.fromisoformat(as_of_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.strptime(as_of_str, "%Y-%m-%d")


async def _resolve_fx_account(db: AsyncSession) -> Optional[Account]:
    configured = (await get_setting(db, "fx_gain_loss_account_code", default="5530")).strip() or "5530"
    for code in [configured, "5530"]:
        result = await db.execute(select(Account).where(Account.account_code == code).limit(1))
        acc = result.scalar_one_or_none()
        if acc:
            return acc
    return None


@router.post("/revaluate/preview")
async def preview_revaluation(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Preview unrealized FX differences without posting (read-only)."""
    as_of = await _parse_as_of(data)
    diffs = await _fx_differences(db, as_of)
    total_gain = round(sum(d["difference"] for d in diffs if d["difference"] > 0), 4)
    total_loss = round(abs(sum(d["difference"] for d in diffs if d["difference"] < 0)), 4)
    return {
        "as_of_date": as_of.date().isoformat(),
        "differences": diffs,
        "total_gain": total_gain,
        "total_loss": total_loss,
        "net_difference": round(total_gain - total_loss, 4),
        "requires_posting": len(diffs) > 0,
    }


@router.post("/revaluate")
async def apply_revaluation(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("POST_JOURNAL")),
):
    """Post a revaluation journal entry for unrealized FX differences.

    Standard treatment: assets/liabilities are re-measured at the balance-sheet
    rate and the difference is recognized in the FX gain/loss account (5530,
    configurable via settings). The entry is posted immediately and balanced.
    """
    from app.routers.accounting import _generate_entry_number

    as_of = await _parse_as_of(data)
    diffs = await _fx_differences(db, as_of)
    if not diffs:
        return {"message": "لا توجد فروق عملة لإعادة تقييمها", "posted": 0,
                "entry_number": None, "differences": []}

    fx_account = await _resolve_fx_account(db)
    if not fx_account:
        raise HTTPException(
            status_code=400,
            detail="لا يوجد حساب فروق عملة (5530). يرجى إنشاؤه أو ضبط الكود من الإعدادات.",
        )

    lines = []
    net = 0.0
    for d in diffs:
        amount = d["difference"]
        if d["account_type"] == "asset":
            debit, credit = (abs(amount), 0.0) if amount > 0 else (0.0, abs(amount))
        else:
            debit, credit = (0.0, abs(amount)) if amount > 0 else (abs(amount), 0.0)
        lines.append({"account_id": d["account_id"], "debit": debit, "credit": credit,
                      "description": f"فروق عملة إعادة تقييم {d['currency_code']} - {d['account_code']}"})
        # net on the P&L side: +gain => extra credit, +loss => extra debit
        net += amount

    if abs(net) < 0.01:
        raise HTTPException(status_code=400, detail="مجموع الفروق صفر بعد التقريب")

    fx_debit = net if net < 0 else 0.0
    fx_credit = net if net > 0 else 0.0
    lines.append({"account_id": fx_account.id, "debit": round(fx_debit, 4),
                  "credit": round(fx_credit, 4),
                  "description": "فروق عملة (تسوية إعادة التقييم)"})

    entry_number = await _generate_entry_number(db)
    description = (data.get("description") or "").strip() or f"إعادة تقييم عملات بتاريخ {as_of.date()}"
    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=as_of,
        reference_type="CurrencyRevaluation",
        description=description,
        status="Posted",
        created_by=current_user.id if hasattr(current_user, "id") else None,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        posted_by=current_user.id if hasattr(current_user, "id") else None,
        posted_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(entry)
    await db.flush()
    for line in lines:
        db.add(JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=line["account_id"],
            description=line["description"],
            debit=line["debit"],
            credit=line["credit"],
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    await db.flush()
    await add_audit_log(db, "JournalEntry", entry.id, "POST", current_user,
                        {"entry_number": entry_number, "kind": "currency_revaluation"})
    total_debit = round(sum(l["debit"] for l in lines), 4)
    total_credit = round(sum(l["credit"] for l in lines), 4)
    return {
        "message": "تم ترحيل قيد إعادة تقييم العملات",
        "entry_number": entry_number,
        "entry_id": entry.id,
        "posted": len(diffs),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "differences": diffs,
    }
