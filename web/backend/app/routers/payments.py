import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.payments import CustomerPayment, SupplierPayment, Bank, BankTransaction
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user

router = APIRouter()


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
async def create_customer_payment(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment = CustomerPayment(
        customer_id=data.get("customer_id"), amount=data.get("amount", 0),
        payment_date=data.get("payment_date") or datetime.utcnow(),
        payment_method=data.get("payment_method", "cash"),
        reference_number=data.get("reference_number"),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    await db.flush()
    return {"id": payment.id, "message": "Payment recorded"}


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
async def create_supplier_payment(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    payment = SupplierPayment(
        supplier_id=data.get("supplier_id"), amount=data.get("amount", 0),
        payment_date=data.get("payment_date") or datetime.utcnow(),
        payment_method=data.get("payment_method", "cash"),
        reference_number=data.get("reference_number"),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(payment)
    await db.flush()
    return {"id": payment.id, "message": "Payment recorded"}


# ── Banks ─────────────────────────────────────────────────────

@router.get("/banks")
async def list_banks(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Bank).where(Bank.is_active == True).order_by(Bank.bank_name))
    items = [{"id": b.id, "name": b.bank_name, "bank_name": b.bank_name,
             "accountName": b.account_name, "account_name": b.account_name,
             "accountNumber": b.account_number, "account_number": b.account_number,
             "iban": b.iban, "accountType": b.account_type,
             "balance": b.current_balance or 0,
             "current_balance": b.current_balance, "opening_balance": b.opening_balance,
             "currency": "SAR", "isActive": b.is_active, "is_active": b.is_active}
            for b in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/banks", response_model=dict)
async def create_bank(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    bank = Bank(
        bank_name=data.get("bank_name", ""), account_name=data.get("account_name"),
        account_number=data.get("account_number", ""),
        iban=data.get("iban"), account_type=data.get("account_type", "checking"),
        currency_id=data.get("currency_id"),
        opening_balance=data.get("opening_balance", 0),
        current_balance=data.get("current_balance", data.get("opening_balance", 0)),
        account_id=data.get("account_id"), notes=data.get("notes"),
        created_at=datetime.utcnow(),
    )
    db.add(bank)
    await db.flush()
    return {"id": bank.id, "message": "Bank account created"}


@router.put("/banks/{bank_id}", response_model=dict)
async def update_bank(bank_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
async def create_bank_transaction(bank_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    txn = BankTransaction(
        bank_id=bank_id, transaction_type=data.get("transaction_type", "deposit"),
        amount=data.get("amount", 0), transaction_date=data.get("transaction_date") or datetime.utcnow(),
        description=data.get("description"), reference_number=data.get("reference_number"),
        created_by=current_user.id, created_at=datetime.utcnow(),
    )
    db.add(txn)

    bank_result = await db.execute(select(Bank).where(Bank.id == bank_id))
    bank = bank_result.scalar_one_or_none()
    if bank:
        if txn.transaction_type == "deposit":
            bank.current_balance = (bank.current_balance or 0) + txn.amount
        elif txn.transaction_type == "withdrawal":
            bank.current_balance = (bank.current_balance or 0) - txn.amount

    await db.flush()
    return {"id": txn.id, "message": "Transaction recorded"}
