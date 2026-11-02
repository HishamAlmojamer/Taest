"""
Accounting vouchers (سندات القبض والصرف).

A voucher is a treasury document:
  RECEIPT (سند قبض) — money received:      Dr  Cash/Bank   Cr  Customer (AR) / counter account
  PAYMENT (سند صرف)  — money paid out:     Dr  Supplier (AP) / counter account   Cr  Cash/Bank

Every voucher posts a balanced double-entry journal entry immediately upon
creation. Voiding a posted voucher creates an automatic reversal entry and
marks the voucher Voided, preserving the audit trail.
"""

from datetime import UTC, datetime
from decimal import Decimal as _D
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.models.sales import Customer
from app.models.purchases import Supplier
from app.models.voucher import AccountingVoucher
from app.models.user import User
from app.routers.accounting import _check_period_lock, _validate_journal_accounts, _generate_entry_number
from app.services.numbering_service import generate_next_number
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log

router = APIRouter()


class VoucherCreate(BaseModel):
    voucher_type: str = Field(..., description="RECEIPT or PAYMENT")
    voucher_date: str | None = None
    partner_type: Optional[str] = None
    partner_id: Optional[int] = None
    amount: float = Field(..., gt=0)
    payment_method: str = Field(..., description="cash or bank")
    bank_id: Optional[int] = None
    counter_account_id: Optional[int] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    fiscal_period_id: Optional[int] = None
    company_id: Optional[int] = None
    currency_code: Optional[str] = "SAR"
    exchange_rate: Optional[float] = 1.0


async def _resolve_account(db: AsyncSession, code: str, fallback_name: str = "") -> Account:
    result = await db.execute(select(Account).where(Account.account_code == code).limit(1))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(
            status_code=400,
            detail=f"Chart account '{code}' ({fallback_name}) is not configured. Please create it first.",
        )
    if account.is_control:
        raise HTTPException(
            status_code=400,
            detail=f"Chart account '{code}' is a control (group) account and cannot receive postings.",
        )
    if not account.is_active:
        raise HTTPException(status_code=400, detail=f"Chart account '{code}' is inactive.")
    return account


def _parse_date(raw: str | None, field: str = "voucher_date") -> datetime:
    """Parse a date/datetime, accepting ISO-8601 and a few common formats.

    Bad input raises 422 instead of letting ValueError escape as a 500.
    """
    if not raw:
        return datetime.now(UTC).replace(tzinfo=None)
    text = raw.strip()
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        return datetime.fromisoformat(normalized).replace(tzinfo=None)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise HTTPException(status_code=422, detail=f"Invalid {field}: {raw!r}")


def _voucher_to_dict(v: AccountingVoucher) -> dict:
    return {
        "id": v.id,
        "voucher_type": v.voucher_type,
        "voucher_number": v.voucher_number,
        "voucher_date": v.voucher_date.isoformat() if v.voucher_date else None,
        "partner_type": v.partner_type,
        "partner_id": v.partner_id,
        "amount": float(v.amount or 0),
        "payment_method": v.payment_method,
        "bank_id": v.bank_id,
        "reference_number": v.reference_number,
        "description": v.description,
        "status": v.status,
        "journal_entry_id": v.journal_entry_id,
        "reversal_entry_id": v.reversal_entry_id,
        "void_reason": v.void_reason,
        "currency_code": v.currency_code,
        "company_id": v.company_id,
        "created_by": v.created_by,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@router.post("/vouchers", response_model=dict)
async def create_voucher(
    data: VoucherCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_JOURNAL")),
):
    voucher_type = data.voucher_type.upper().strip()
    if voucher_type not in ("RECEIPT", "PAYMENT"):
        raise HTTPException(status_code=400, detail="voucher_type must be RECEIPT or PAYMENT")
    payment_method = (data.payment_method or "").lower().strip()
    if payment_method not in ("cash", "bank"):
        raise HTTPException(status_code=400, detail="payment_method must be 'cash' or 'bank'")

    voucher_date = _parse_date(data.voucher_date)

    partner_type = (data.partner_type or "").lower().strip()
    partner_id = data.partner_id
    partner = None
    amount = _D(str(data.amount))
    if partner_type == "customer":
        if not partner_id:
            raise HTTPException(status_code=400, detail="partner_id is required for customer vouchers")
        partner = (await db.execute(select(Customer).where(Customer.id == partner_id))).scalar_one_or_none()
        if not partner:
            raise HTTPException(status_code=404, detail="Customer not found")
    elif partner_type == "supplier":
        if not partner_id:
            raise HTTPException(status_code=400, detail="partner_id is required for supplier vouchers")
        partner = (await db.execute(select(Supplier).where(Supplier.id == partner_id))).scalar_one_or_none()
        if not partner:
            raise HTTPException(status_code=404, detail="Supplier not found")
    elif partner_type:
        raise HTTPException(status_code=400, detail="partner_type must be 'customer', 'supplier' or null")

    await _check_period_lock(db, data.fiscal_period_id, voucher_date)

    # Treasury (fund) account: cash drawer or bank.
    fund_code = "1111" if payment_method == "cash" else "1121"
    fund_account = await _resolve_account(db, fund_code, "الصندوق الرئيسي" if payment_method == "cash" else "بنك الأهلي السعودي")

    # Counter account: default AR (1201) for receipts, AP (2111) for payments.
    if data.counter_account_id:
        counter_account = (await db.execute(select(Account).where(Account.id == data.counter_account_id))).scalar_one_or_none()
        if not counter_account:
            raise HTTPException(status_code=404, detail="Counter account not found")
        await _validate_journal_accounts(db, [counter_account.id])
    else:
        default_code = "1201" if voucher_type == "RECEIPT" else "2111"
        counter_account = await _resolve_account(
            db, default_code,
            "الذمم المدينة" if voucher_type == "RECEIPT" else "الذمم الدائنة",
        )

    await _validate_journal_accounts(db, [fund_account.id, counter_account.id])

    doc_type = "RECEIPT_VOUCHER" if voucher_type == "RECEIPT" else "PAYMENT_VOUCHER"
    voucher_number = await generate_next_number(
        db, doc_type,
        prefix="RC" if voucher_type == "RECEIPT" else "PV",
        include_year=True, zero_padding=6, separator="-", period="YEAR",
    )

    voucher = AccountingVoucher(
        voucher_type=voucher_type,
        voucher_number=voucher_number,
        voucher_date=voucher_date,
        partner_type=partner_type or None,
        partner_id=partner_id,
        amount=amount,
        payment_method=payment_method,
        bank_id=data.bank_id,
        reference_number=data.reference_number,
        description=data.description,
        status="Posted",
        currency_code=data.currency_code,
        exchange_rate=data.exchange_rate,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        company_id=data.company_id,
    )
    db.add(voucher)
    await db.flush()

    entry_number = await _generate_entry_number(db)
    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=voucher_date,
        fiscal_period_id=data.fiscal_period_id,
        reference_type="ReceiptVoucher" if voucher_type == "RECEIPT" else "PaymentVoucher",
        reference_id=voucher.id,
        description=f"{'سند قبض' if voucher_type == 'RECEIPT' else 'سند صرف'} {voucher_number}"
                    + (f" — {data.description}" if data.description else ""),
        status="Posted",
        created_by=current_user.id,
        posted_by=current_user.id,
        posted_at=datetime.now(UTC).replace(tzinfo=None),
        created_at=datetime.now(UTC).replace(tzinfo=None),
        company_id=data.company_id,
    )
    db.add(entry)
    await db.flush()

    partner_line_description = ""
    if partner:
        partner_line_description = getattr(partner, "name", "") or getattr(partner, "name_ar", "") or ""
        fund_description = f"{partner_line_description} — {voucher_number}"
    else:
        fund_description = f"{voucher_number}{' — ' + data.description if data.description else ''}"

    if voucher_type == "RECEIPT":
        fund_debit, fund_credit = amount, None
        counter_debit, counter_credit = None, amount
    else:
        fund_debit, fund_credit = None, amount
        counter_debit, counter_credit = amount, None

    db.add_all([
        JournalEntryLine(
            journal_entry_id=entry.id, account_id=fund_account.id,
            description=fund_description,
            debit=fund_debit, credit=fund_credit,
            partner_id=partner_id if partner else None,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            company_id=data.company_id,
        ),
        JournalEntryLine(
            journal_entry_id=entry.id, account_id=counter_account.id,
            description=fund_description,
            debit=counter_debit, credit=counter_credit,
            partner_id=partner_id if partner else None,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            company_id=data.company_id,
        ),
    ])
    await db.flush()

    if partner_type == "customer":
        partner.current_balance = _D(str(partner.current_balance or 0)) - amount
    elif partner_type == "supplier":
        partner.current_balance = _D(str(partner.current_balance or 0)) - amount

    voucher.journal_entry_id = entry.id
    await db.flush()

    await add_audit_log(db, "AccountingVoucher", voucher.id, "CREATE", current_user,
                        {"voucher_number": voucher_number, "journal_entry_id": entry.id,
                         "entry_number": entry_number})
    await db.commit()

    result = _voucher_to_dict(voucher)
    result["entry_number"] = entry_number
    result["fund_account_id"] = fund_account.id
    result["counter_account_id"] = counter_account.id
    return {"message": "Voucher created and posted", "voucher": result, "journal_entry_id": entry.id}


@router.get("/vouchers", response_model=dict)
async def list_vouchers(
    voucher_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    partner_type: Optional[str] = Query(None),
    partner_id: Optional[int] = Query(None),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_JOURNAL")),
):
    conditions = []
    if voucher_type:
        conditions.append(AccountingVoucher.voucher_type == voucher_type.upper())
    if status:
        conditions.append(AccountingVoucher.status == status)
    if partner_type:
        conditions.append(AccountingVoucher.partner_type == partner_type)
    if partner_id:
        conditions.append(AccountingVoucher.partner_id == partner_id)
    if from_date:
        conditions.append(AccountingVoucher.voucher_date >= _parse_date(from_date, "from_date"))
    if to_date:
        conditions.append(AccountingVoucher.voucher_date <= _parse_date(to_date, "to_date"))

    base = select(AccountingVoucher)
    if conditions:
        base = base.where(*conditions)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar() or 0
    rows = (await db.execute(
        base.order_by(AccountingVoucher.voucher_date.desc(), AccountingVoucher.id.desc())
        .offset((page - 1) * per_page).limit(per_page)
    )).scalars().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": -(-total // per_page) if total else 0,
        "items": [_voucher_to_dict(v) for v in rows],
    }


@router.get("/vouchers/{voucher_id}", response_model=dict)
async def get_voucher(
    voucher_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("VIEW_JOURNAL")),
):
    voucher = (await db.execute(select(AccountingVoucher).where(AccountingVoucher.id == voucher_id))).scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    return _voucher_to_dict(voucher)


@router.post("/vouchers/{voucher_id}/void", response_model=dict)
async def void_voucher(
    voucher_id: int,
    reason: str = Query("", min_length=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("EDIT_JOURNAL")),
):
    voucher = (await db.execute(select(AccountingVoucher).where(AccountingVoucher.id == voucher_id))).scalar_one_or_none()
    if not voucher:
        raise HTTPException(status_code=404, detail="Voucher not found")
    if voucher.status != "Posted":
        raise HTTPException(status_code=400, detail="Only posted vouchers can be voided")
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="A void reason is required")
    if not voucher.journal_entry_id:
        raise HTTPException(status_code=400, detail="Voucher has no journal entry to reverse")

    await _check_period_lock(db, None, voucher.voucher_date)

    lines = (await db.execute(
        select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == voucher.journal_entry_id)
    )).scalars().all()
    if not lines:
        raise HTTPException(status_code=400, detail="Voucher journal entry has no lines")

    reversal_number = await _generate_entry_number(db)
    reversal = JournalEntry(
        entry_number=reversal_number,
        entry_date=datetime.now(UTC).replace(tzinfo=None),
        reference_type="VoucherReversal",
        reference_id=voucher.id,
        description=f"عكس {voucher.voucher_number} — {reason}",
        status="Posted",
        created_by=current_user.id,
        posted_by=current_user.id,
        posted_at=datetime.now(UTC).replace(tzinfo=None),
        created_at=datetime.now(UTC).replace(tzinfo=None),
        company_id=voucher.company_id,
    )
    db.add(reversal)
    await db.flush()

    for line in lines:
        db.add(JournalEntryLine(
            journal_entry_id=reversal.id, account_id=line.account_id,
            description=f"عكس {voucher.voucher_number} — {reason}",
            debit=line.credit, credit=line.debit,
            partner_id=line.partner_id, cost_center_id=line.cost_center_id,
            project_id=line.project_id, currency_id=line.currency_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
            company_id=voucher.company_id,
        ))
    await db.flush()

    if voucher.partner_type == "customer" and voucher.partner_id:
        partner = (await db.execute(select(Customer).where(Customer.id == voucher.partner_id))).scalar_one_or_none()
        if partner:
            partner.current_balance = (partner.current_balance or 0) + voucher.amount
    elif voucher.partner_type == "supplier" and voucher.partner_id:
        partner = (await db.execute(select(Supplier).where(Supplier.id == voucher.partner_id))).scalar_one_or_none()
        if partner:
            partner.current_balance = (partner.current_balance or 0) + voucher.amount

    voucher.status = "Voided"
    voucher.reversal_entry_id = reversal.id
    voucher.void_reason = reason
    voucher.updated_by = current_user.id
    voucher.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()

    await add_audit_log(db, "AccountingVoucher", voucher.id, "VOID", current_user,
                        {"voucher_number": voucher.voucher_number, "reversal_entry_id": reversal.id})
    await db.commit()

    result = _voucher_to_dict(voucher)
    result["reversal_entry_number"] = reversal_number
    return {"message": "Voucher voided with reversing entry", "voucher": result, "reversal_entry_id": reversal.id}