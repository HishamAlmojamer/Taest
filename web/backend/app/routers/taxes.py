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
from app.models.accounting import JournalEntry, JournalEntryLine, Account
from app.routers.accounting import _LEDGER_STATUSES
from app.schemas.taxes import TaxRateCreate
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log
from app.services.settings_service import get_setting

router = APIRouter()


@router.get("/tax-rates")
async def list_tax_rates(
    tax_type: Optional[str] = Query(None),
    applies_to: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
    current_user=Depends(get_current_user),
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
    data: TaxRateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """Create a new tax rate"""
    # Check if code already exists
    existing = await db.execute(select(TaxRate).where(TaxRate.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Tax rate code already exists")

    rate = TaxRate(
        code=data.code,
        name=data.name,
        name_ar=data.name_ar,
        rate=data.rate,
        tax_type=data.tax_type,
        applies_to=data.applies_to,
        is_recovery_allowed=data.is_recovery_allowed,
        gl_account_code=data.gl_account_code,
        is_active=data.is_active,
        description=data.description,
        created_at=datetime.now(),
    )
    db.add(rate)
    await db.commit()
    await db.refresh(rate)
    await add_audit_log(db, "TaxRate", rate.id, "CREATE", current_user,
                        {"code": rate.code, "name": rate.name, "rate": rate.rate})
    await db.commit()
    return {"id": rate.id, "code": rate.code, "name": rate.name, "message": "Tax rate created"}


@router.put("/tax-rates/{tax_rate_id}")
async def update_tax_rate(
    tax_rate_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
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
    await db.refresh(rate)
    await add_audit_log(db, "TaxRate", rate.id, "UPDATE", current_user,
                        {"changes": list(data.keys())})
    await db.commit()
    return {"success": True, "message": "Tax rate updated"}


@router.delete("/tax-rates/{tax_rate_id}")
async def delete_tax_rate(
    tax_rate_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_SETTINGS")),
):
    """Delete a tax rate (soft delete)"""
    result = await db.execute(select(TaxRate).where(TaxRate.id == tax_rate_id))
    rate = result.scalar_one_or_none()
    if not rate:
        raise HTTPException(status_code=404, detail="Tax rate not found")

    rate.is_active = False
    await db.commit()
    await add_audit_log(db, "TaxRate", rate.id, "DELETE", current_user,
                        {"code": rate.code, "deactivated": True})
    await db.commit()
    return {"success": True, "message": "Tax rate deactivated"}


@router.get("/vat-return")
async def get_vat_return(
    from_date: str = Query(...),
    to_date: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    VAT return report for a period.
    Computes output VAT (from the configurable VAT output account, default 2121)
    and input VAT (VAT input account, default 1400).
    """
    from datetime import datetime as dt

    def _parse(value: Optional[str], field: str) -> dt:
        """Accept ISO-8601 and common date formats; 422 on anything else."""
        text = (value or "").strip()
        if not text:
            raise HTTPException(status_code=422, detail=f"Missing required field(s): {field}")
        normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
        try:
            return dt.fromisoformat(normalized)
        except ValueError:
            pass
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"):
            try:
                return dt.strptime(text, fmt)
            except ValueError:
                continue
        raise HTTPException(status_code=422, detail=f"Invalid {field}: {value!r}")

    fd = _parse(from_date, "from_date")
    td = _parse(to_date, "to_date")

    async def _account_balance(code: str):
        result = await db.execute(
            select(Account).where(Account.account_code == code).limit(1)
        )
        account = result.scalar_one_or_none()
        if not account:
            return 0.0
        bal = await db.execute(
            select(
                func.coalesce(func.sum(JournalEntryLine.debit), 0) - func.coalesce(func.sum(JournalEntryLine.credit), 0)
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id == account.id)
            .where(JournalEntry.status.in_(_LEDGER_STATUSES))
            .where(JournalEntry.entry_date >= fd, JournalEntry.entry_date <= td)
        )
        return float(bal.scalar() or 0)

    output_code = (await get_setting(db, "vat_output_account_code", default="2121")).strip() or "2121"
    input_code = (await get_setting(db, "vat_input_account_code", default="1400")).strip() or "1400"
    output_vat = await _account_balance(output_code)
    input_vat = await _account_balance(input_code)
    net_vat_due = abs(output_vat) - abs(input_vat)

    return {
        "period": {"from": from_date, "to": to_date},
        "output_vat": round(abs(output_vat), 4),
        "input_vat": round(abs(input_vat), 4),
        "net_vat_due": round(abs(net_vat_due), 4),
        "is_refund": net_vat_due < 0,
    }


@router.post("/calculate-tax")
async def calculate_tax(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
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
