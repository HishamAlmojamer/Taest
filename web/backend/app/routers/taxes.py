"""
Tax Rate management endpoints for VAT/GST/tax configuration.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.tax import TaxRate, TaxTransaction
from app.utils.deps import get_current_active_user

router = APIRouter()


@router.get("/tax-rates")
async def list_tax_rates(
    tax_type: Optional[str] = Query(None),
    applies_to: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all tax rates"""
    query = select(TaxRate).order_by(TaxRate.code)
    if tax_type:
        query = query.where(TaxRate.tax_type == tax_type)
    if applies_to:
        query = query.where(TaxRate.applies_to == applies_to)
    if is_active is not None:
        query = query.where(TaxRate.is_active == is_active)
    result = await db.execute(query)
    rates = result.scalars().all()
    return [{"id": r.id, "code": r.code, "name": r.name, "name_ar": r.name_ar,
             "rate": r.rate, "tax_type": r.tax_type, "applies_to": r.applies_to,
             "is_recovery_allowed": r.is_recovery_allowed, "gl_account_code": r.gl_account_code,
             "is_active": r.is_active, "description": r.description} for r in rates]


@router.get("/tax-rates/{tax_rate_id}")
async def get_tax_rate(
    tax_rate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Get a specific tax rate"""
    result = await db.execute(select(TaxRate).where(TaxRate.id == tax_rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")
    return {"id": rate.id, "code": rate.code, "name": rate.name, "name_ar": rate.name_ar,
            "rate": rate.rate, "tax_type": rate.tax_type, "applies_to": rate.applies_to,
            "is_recovery_allowed": rate.is_recovery_allowed, "gl_account_code": rate.gl_account_code,
            "is_active": rate.is_active, "description": rate.description}


@router.post("/tax-rates")
async def create_tax_rate(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new tax rate"""
    # Check if code already exists
    existing = await db.execute(select(TaxRate).where(TaxRate.code == data.get("code")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tax rate code already exists")

    rate = TaxRate(
        code=data["code"],
        name=data["name"],
        name_ar=data.get("name_ar"),
        rate=data.get("rate", 0.0),
        tax_type=data.get("tax_type", "VAT"),
        applies_to=data.get("applies_to", "BOTH"),
        is_recovery_allowed=data.get("is_recovery_allowed", False),
        gl_account_code=data.get("gl_account_code"),
        is_active=data.get("is_active", True),
        description=data.get("description"),
        created_at=datetime.now(),
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    return {"id": rate.id, "code": rate.code, "name": rate.name, "message": "Tax rate created"}


@router.put("/tax-rates/{tax_rate_id}")
async def update_tax_rate(
    tax_rate_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Update a tax rate"""
    result = await db.execute(select(TaxRate).where(TaxRate.id == tax_rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    for key, value in data.items():
        if hasattr(rate, key):
            setattr(rate, key, value)
    rate.updated_at = datetime.now()
    await db.commit()
    return {"success": True, "message": "Tax rate updated"}


@router.delete("/tax-rates/{tax_rate_id}")
async def delete_tax_rate(
    tax_rate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Delete a tax rate (soft delete)"""
    result = await db.execute(select(TaxRate).where(TaxRate.id == tax_rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    rate.is_active = False
    await db.commit()
    return {"success": True, "message": "Tax rate deactivated"}


@router.post("/calculate-tax")
async def calculate_tax(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Calculate tax for an amount using a specific tax rate.
    Request body: { "tax_rate_id": int, "amount": float }
    """
    tax_rate_id = data.get("tax_rate_id")
    amount = data.get("amount", 0.0)

    if not tax_rate_id:
        raise HTTPException(status_code=400, detail="tax_rate_id is required")

    result = await db.execute(select(TaxRate).where(TaxRate.id == tax_rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    tax_amount = amount * (rate.rate / 100)
    total_with_tax = amount + tax_amount

    return {
        "amount": amount,
        "tax_rate_code": rate.code,
        "tax_rate_name": rate.name,
        "tax_rate": rate.rate,
        "tax_amount": round(tax_amount, 4),
        "total_with_tax": round(total_with_tax, 4),
    }
