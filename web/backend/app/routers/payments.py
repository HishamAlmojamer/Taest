import math
import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.payments import CustomerPayment, SupplierPayment, Bank, BankTransaction
from app.models.sales import Customer
from app.models.purchases import Supplier
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.validation import require_fields
from app.utils.event_emitter import emit_payment_received, emit_payment_made
from app.services.settings_service import get_setting

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_entry_id_from_event(event_result) -> Optional[int]:
    """Extract the created journal entry id from the Ledger Engine emit response."""
    try:
        results = (event_result.get("data") or {}).get("results") or []
        for r in results:
            if isinstance(r, dict) and r.get("entryId"):
                return int(r["entryId"])
    except Exception:
        logger.exception("Failed to extract entry id from ledger event response")
    return None


# ── Customer Payments ─────────────────────────────────────────

@router.get("/customers", response_model=PaginationResponse)
async def list_customer_payments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(CustomerPayment)
    count_query = select(func.count(CustomerPayment.id))
    if customer_id:
        query = query.where(CustomerPayment.customer_id == customer_id)
        count_query = count_query.where(CustomerPayment.customer_id == customer_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(CustomerPayment.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    payments = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": p.id, "paymentNumber": f"PAY-{p.id:05d}",
                "customerId": p.customer_id, "customerName": f"عميل #{p.customer_id}",
                "amount": p.amount, "method": p.payment_method,
                "date": str(p.payment_date) if p.payment_date else None,
                "paymentDate": str(p.payment_date) if p.payment_date else None,
                "referenceNumber": p.reference_number, "notes": p.notes,
                "createdBy": p.created_by}
               for p in payments],
    )


@router.post("/customers", response_model=dict)
async def create_customer_payment(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_SALE"))):
    amount = data.get("amount", 0)
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")

    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), None)

    payment = CustomerPayment(
        customer_id=data.get("customer_id"), amount=amount,
        payment_date=data.get("payment_date") or datetime.now(UTC).replace(tzinfo=None),
        payment_method=data.get("payment_method", "cash"),
        reference_number=data.get("reference_number"),
        bank_id=data.get("bank_id"),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(payment)
    await db.flush()

    # Create BankTransaction if bank_id is provided
    bank_id = data.get("bank_id")
    if bank_id:
        txn_type = "DEPOSIT" if data.get("payment_method", "cash") != "CASH" else "DEPOSIT"
        bank_txn = BankTransaction(
            bank_id=bank_id,
            transaction_type=txn_type,
            amount=amount,
            transaction_date=payment.payment_date or datetime.now(UTC).replace(tzinfo=None),
            description=f"دفعة من عميل #{payment.customer_id}",
            reference_number=data.reference_number if hasattr(data, 'reference_number') else data.get("reference_number"),
            reconciled=False,
            journal_entry_id=None,
            created_by=current_user.id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(bank_txn)

    # Emit ledger event within the same transaction (Dr Bank / Cr AR).
    customer_name = f"عميل #{payment.customer_id}"
    if payment.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == payment.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    event_result = await emit_payment_received(
        payment_id=payment.id,
        customer_id=payment.customer_id or 0,
        customer_name=customer_name,
        amount=amount,
        payment_method=payment.payment_method or "cash",
        reference_number=payment.reference_number,
        user_id=current_user.id,
    )
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(CustomerPayment).where(CustomerPayment.id == payment.id).values(journal_entry_id=entry_id))

    await db.commit()
    return {"id": payment.id, "message": "Payment recorded",
            "journal_entry_id": entry_id}


# ── Supplier Payments ─────────────────────────────────────────

@router.get("/suppliers", response_model=PaginationResponse)
async def list_supplier_payments(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    supplier_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SupplierPayment)
    count_query = select(func.count(SupplierPayment.id))
    if supplier_id:
        query = query.where(SupplierPayment.supplier_id == supplier_id)
        count_query = count_query.where(SupplierPayment.supplier_id == supplier_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(SupplierPayment.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    payments = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": p.id, "paymentNumber": f"PAY-{p.id:05d}",
                "supplierId": p.supplier_id, "supplierName": f"مورد #{p.supplier_id}",
                "amount": p.amount, "method": p.payment_method,
                "date": str(p.payment_date) if p.payment_date else None,
                "paymentDate": str(p.payment_date) if p.payment_date else None,
                "referenceNumber": p.reference_number, "notes": p.notes,
                "createdBy": p.created_by}
               for p in payments],
    )


@router.post("/suppliers", response_model=dict)
async def create_supplier_payment(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_PURCHASE"))):
    amount = data.get("amount", 0)
    if amount is None or amount <= 0:
        raise HTTPException(status_code=400, detail="المبلغ يجب أن يكون أكبر من صفر")

    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), None)

    payment = SupplierPayment(
        supplier_id=data.get("supplier_id"), amount=amount,
        payment_date=data.get("payment_date") or datetime.now(UTC).replace(tzinfo=None),
        payment_method=data.get("payment_method", "cash"),
        reference_number=data.get("reference_number"),
        bank_id=data.get("bank_id"),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(payment)
    await db.flush()

    # Create BankTransaction if bank_id is provided
    bank_id = data.get("bank_id")
    if bank_id:
        txn_type = "WITHDRAWAL"
        bank_txn = BankTransaction(
            bank_id=bank_id,
            transaction_type=txn_type,
            amount=amount,
            transaction_date=payment.payment_date or datetime.now(UTC).replace(tzinfo=None),
            description=f"دفعة إلى مورد #{payment.supplier_id}",
            reference_number=data.reference_number if hasattr(data, 'reference_number') else data.get("reference_number"),
            reconciled=False,
            journal_entry_id=None,
            created_by=current_user.id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(bank_txn)

    # Emit ledger event within the same transaction (Dr AP / Cr Bank).
    supplier_name = f"مورد #{payment.supplier_id}"
    if payment.supplier_id:
        sup_result = await db.execute(select(Supplier).where(Supplier.id == payment.supplier_id))
        supplier = sup_result.scalar_one_or_none()
        if supplier:
            supplier_name = supplier.name

    event_result = await emit_payment_made(
        payment_id=payment.id,
        supplier_id=payment.supplier_id or 0,
        supplier_name=supplier_name,
        amount=amount,
        payment_method=payment.payment_method or "cash",
        reference_number=payment.reference_number,
        user_id=current_user.id,
    )
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(SupplierPayment).where(SupplierPayment.id == payment.id).values(journal_entry_id=entry_id))

    await db.commit()
    return {"id": payment.id, "message": "Payment recorded",
            "journal_entry_id": entry_id}


# ── Banks ─────────────────────────────────────────────────────

@router.get("/banks")
async def list_banks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Bank).where(Bank.is_active == True).order_by(Bank.bank_name))
    base_cur = (await get_setting(db, "base_currency", default="SAR")).strip()
    items = [{"id": b.id, "name": b.bank_name, "bank_name": b.bank_name,
             "accountName": b.account_name, "account_name": b.account_name,
             "accountNumber": b.account_number, "account_number": b.account_number,
             "iban": b.iban, "accountType": b.account_type,
             "balance": b.current_balance or 0,
             "current_balance": b.current_balance, "opening_balance": b.opening_balance,
             "currency": base_cur, "isActive": b.is_active, "is_active": b.is_active}
            for b in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/banks", response_model=dict)
async def create_bank(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    require_fields(data, ["bank_name", "account_number"])
    account_number = str(data["account_number"]).strip()
    if not account_number:
        raise HTTPException(status_code=422, detail="account_number is required")
    existing = (await db.execute(select(Bank.id).where(Bank.account_number == account_number))).scalar_one_or_none()
    if existing is not None:
        raise HTTPException(status_code=409, detail="Bank account number already exists")
    bank = Bank(
        bank_name=data.get("bank_name", ""), account_name=data.get("account_name"),
        account_number=account_number,
        iban=data.get("iban"), account_type=data.get("account_type", "checking"),
        currency_id=data.get("currency_id"),
        opening_balance=data.get("opening_balance", 0),
        current_balance=data.get("current_balance", data.get("opening_balance", 0)),
        account_id=data.get("account_id"), notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(bank)
    await db.flush()
    return {"id": bank.id, "message": "Bank account created"}


@router.put("/banks/{bank_id}", response_model=dict)
async def update_bank(bank_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Bank).where(Bank.id == bank_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bank not found")
    allowed = ['bank_name', 'account_name', 'account_number', 'iban', 'account_type',
               'currency_id', 'opening_balance', 'current_balance', 'account_id', 'notes']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Bank).where(Bank.id == bank_id).values(**values))
    return {"message": "Bank updated"}


# ── Bank Transactions ─────────────────────────────────────────

@router.get("/banks/{bank_id}/transactions")
async def list_bank_transactions(
    bank_id: int,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_query = select(func.count(BankTransaction.id)).where(BankTransaction.bank_id == bank_id)
    total = (await db.execute(count_query)).scalar() or 0
    query = select(BankTransaction).where(BankTransaction.bank_id == bank_id)\
        .order_by(BankTransaction.id.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    txns = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": t.id, "bank_id": t.bank_id, "transaction_type": t.transaction_type,
                "amount": t.amount, "transaction_date": t.transaction_date,
                "description": t.description, "reference_number": t.reference_number,
                "reconciled": t.reconciled, "created_by": t.created_by,
                "created_at": t.created_at.isoformat() if t.created_at else None}
               for t in txns],
    )


@router.post("/banks/{bank_id}/transactions", response_model=dict)
async def create_bank_transaction(bank_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_PURCHASE"))):
    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), None)

    from decimal import Decimal as _D, InvalidOperation
    require_fields(data, ["amount"])
    try:
        amount = _D(str(data["amount"]))
    except (InvalidOperation, TypeError):
        raise HTTPException(status_code=422, detail=f"Invalid amount: {data['amount']!r}")

    bank_result = await db.execute(select(Bank).where(Bank.id == bank_id))
    bank = bank_result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    txn = BankTransaction(
        bank_id=bank_id, transaction_type=data.get("transaction_type", "deposit"),
        amount=amount, transaction_date=data.get("transaction_date") or datetime.now(UTC).replace(tzinfo=None),
        description=data.get("description"), reference_number=data.get("reference_number"),
        created_by=current_user.id, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(txn)

    balance = _D(str(bank.current_balance)) if bank.current_balance is not None else _D("0")
    if txn.transaction_type == "deposit":
        bank.current_balance = balance + amount
    elif txn.transaction_type == "withdrawal":
        bank.current_balance = balance - amount

    await db.flush()
    return {"id": txn.id, "message": "Transaction recorded"}
