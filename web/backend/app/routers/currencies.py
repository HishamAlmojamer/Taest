"""
Currency and Exchange Rate management endpoints.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.currency import Currency, ExchangeRate
from app.utils.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# Currency Endpoints
# =============================================================================

@router.get("/currencies")
async def list_currencies(
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
):
    """Create a new exchange rate"""
    rate = ExchangeRate(
        from_currency_code=data["from_currency_code"],
        to_currency_code=data["to_currency_code"],
        rate=data["rate"],
        effective_date=datetime.fromisoformat(data["effective_date"]) if isinstance(data.get("effective_date"), str) else data.get("effective_date", datetime.now()),
        expiry_date=datetime.fromisoformat(data["expiry_date"]) if isinstance(data.get("expiry_date"), str) else data.get("expiry_date"),
        is_active=data.get("is_active", True),
        created_by=current_user.id if hasattr(current_user, "id") else None,
        created_at=datetime.now(),
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return {"id": rate.id, "message": "Exchange rate created"}
