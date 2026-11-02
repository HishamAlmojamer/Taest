"""
Accounts Receivable and Accounts Payable Aging Reports.
All queries are batched to avoid N+1 performance issues.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.sales import Customer, Sale
from app.models.purchases import Supplier, Purchase
from app.models.payments import CustomerPayment, SupplierPayment
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.routers.accounting import _LEDGER_STATUSES
from app.utils.deps import get_current_user

router = APIRouter()


def _bucket_for_days(days: int) -> str:
    if days <= 0:
        return "current"
    elif days <= 30:
        return "1_30"
    elif days <= 60:
        return "31_60"
    elif days <= 90:
        return "61_90"
    else:
        return "over_90"


def _add_bucket(acc: dict, key: str, amount: float):
    acc[key] = acc.get(key, 0.0) + amount


@router.get("/ar-aging")
async def get_ar_aging(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate Accounts Receivable Aging Report.
    Shows customer balances by aging buckets (0-30, 31-60, 61-90, 90+ days).
    Uses batched queries instead of N+1.
    """
    if not as_of_date:
        as_of_date = date.today()

    cutoff = datetime.combine(as_of_date, datetime.min.time())

    # 1) Fetch all customers with outstanding balance — 1 query
    conditions = [Customer.current_balance > 0]
    if company_id:
        conditions.append(Customer.company_id == company_id)
    customers_result = await db.execute(
        select(Customer).where(and_(*conditions)).order_by(Customer.name)
    )
    customers = customers_result.scalars().all()
    if not customers:
        return {"as_of_date": str(as_of_date), "summary": _empty_summary(), "customers": []}

    customer_ids = [c.id for c in customers]

    # 2) Fetch ALL unpaid sales for these customers in one query
    sales_result = await db.execute(
        select(Sale).where(
            Sale.customer_id.in_(customer_ids),
            Sale.payment_status != "PAID",
            Sale.created_at <= cutoff,
        )
    )
    all_sales = sales_result.scalars().all()

    # 3) Fetch ALL payments for these customers in one query
    payments_result = await db.execute(
        select(CustomerPayment).where(CustomerPayment.customer_id.in_(customer_ids))
    )
    all_payments = payments_result.scalars().all()

    # 4) Build lookup maps in Python — no more DB calls
    payments_by_customer = {}
    for p in all_payments:
        payments_by_customer.setdefault(p.customer_id, []).append(float(p.amount or 0))

    sales_by_customer = {}
    for s in all_sales:
        sales_by_customer.setdefault(s.customer_id, []).append(s)

    customer_map = {c.id: c for c in customers}

    aging_data = []
    totals = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0, "outstanding": 0.0}

    for cid in customer_ids:
        customer = customer_map[cid]
        cust_sales = sales_by_customer.get(cid, [])
        total_payments = sum(payments_by_customer.get(cid, []))

        bucket_totals = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0}

        for sale in cust_sales:
            amount = float(sale.final_amount or 0) - total_payments
            if amount <= 0:
                continue
            invoice_date = sale.created_at.date() if sale.created_at else as_of_date
            days = (as_of_date - invoice_date).days
            bucket = _bucket_for_days(days)
            _add_bucket(bucket_totals, bucket, amount)
            total_payments = 0  # only subtract once across all invoices

        customer_total = sum(bucket_totals.values())
        if customer_total > 0:
            aging_data.append({
                "customer_id": customer.id,
                "customer_code": customer.code,
                "customer_name": customer.name,
                "outstanding_amount": round(customer_total, 4),
                "current": round(bucket_totals["current"], 4),
                "1_30_days": round(bucket_totals["1_30"], 4),
                "31_60_days": round(bucket_totals["31_60"], 4),
                "61_90_days": round(bucket_totals["61_90"], 4),
                "over_90_days": round(bucket_totals["over_90"], 4),
            })
            for k in ("current", "1_30", "31_60", "61_90", "over_90"):
                totals[k] += bucket_totals[k]
            totals["outstanding"] += customer_total

    return {
        "as_of_date": str(as_of_date),
        "summary": {
            "total_outstanding": round(totals["outstanding"], 4),
            "current": round(totals["current"], 4),
            "1_30_days": round(totals["1_30"], 4),
            "31_60_days": round(totals["31_60"], 4),
            "61_90_days": round(totals["61_90"], 4),
            "over_90_days": round(totals["over_90"], 4),
        },
        "customers": aging_data,
    }


@router.get("/ap-aging")
async def get_ap_aging(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Generate Accounts Payable Aging Report.
    Shows supplier balances by aging buckets (0-30, 31-60, 61-90, 90+ days).
    Uses batched queries instead of N+1.
    """
    if not as_of_date:
        as_of_date = date.today()

    cutoff = datetime.combine(as_of_date, datetime.min.time())

    # 1) Fetch all suppliers with outstanding balance — 1 query
    conditions = [Supplier.current_balance > 0]
    if company_id:
        conditions.append(Supplier.company_id == company_id)
    suppliers_result = await db.execute(
        select(Supplier).where(and_(*conditions)).order_by(Supplier.name)
    )
    suppliers = suppliers_result.scalars().all()
    if not suppliers:
        return {"as_of_date": str(as_of_date), "summary": _empty_summary(), "suppliers": []}

    supplier_ids = [s.id for s in suppliers]

    # 2) Fetch ALL unpaid purchases in one query
    purchases_result = await db.execute(
        select(Purchase).where(
            Purchase.supplier_id.in_(supplier_ids),
            Purchase.payment_status != "PAID",
            Purchase.created_at <= cutoff,
        )
    )
    all_purchases = purchases_result.scalars().all()

    # 3) Fetch ALL supplier payments in one query
    payments_result = await db.execute(
        select(SupplierPayment).where(SupplierPayment.supplier_id.in_(supplier_ids))
    )
    all_payments = payments_result.scalars().all()

    # 4) Build lookup maps in Python
    payments_by_supplier = {}
    for p in all_payments:
        payments_by_supplier.setdefault(p.supplier_id, []).append(float(p.amount or 0))

    purchases_by_supplier = {}
    for pur in all_purchases:
        purchases_by_supplier.setdefault(pur.supplier_id, []).append(pur)

    supplier_map = {s.id: s for s in suppliers}

    aging_data = []
    totals = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0, "outstanding": 0.0}

    for sid in supplier_ids:
        supplier = supplier_map[sid]
        sup_purchases = purchases_by_supplier.get(sid, [])
        total_payments = sum(payments_by_supplier.get(sid, []))

        bucket_totals = {"current": 0.0, "1_30": 0.0, "31_60": 0.0, "61_90": 0.0, "over_90": 0.0}

        for purchase in sup_purchases:
            amount = float(purchase.final_amount or 0) - total_payments
            if amount <= 0:
                continue
            invoice_date = purchase.created_at.date() if purchase.created_at else as_of_date
            days = (as_of_date - invoice_date).days
            bucket = _bucket_for_days(days)
            _add_bucket(bucket_totals, bucket, amount)
            total_payments = 0

        supplier_total = sum(bucket_totals.values())
        if supplier_total > 0:
            aging_data.append({
                "supplier_id": supplier.id,
                "supplier_code": supplier.code,
                "supplier_name": supplier.name,
                "outstanding_amount": round(supplier_total, 4),
                "current": round(bucket_totals["current"], 4),
                "1_30_days": round(bucket_totals["1_30"], 4),
                "31_60_days": round(bucket_totals["31_60"], 4),
                "61_90_days": round(bucket_totals["61_90"], 4),
                "over_90_days": round(bucket_totals["over_90"], 4),
            })
            for k in ("current", "1_30", "31_60", "61_90", "over_90"):
                totals[k] += bucket_totals[k]
            totals["outstanding"] += supplier_total

    return {
        "as_of_date": str(as_of_date),
        "summary": {
            "total_outstanding": round(totals["outstanding"], 4),
            "current": round(totals["current"], 4),
            "1_30_days": round(totals["1_30"], 4),
            "31_60_days": round(totals["31_60"], 4),
            "61_90_days": round(totals["61_90"], 4),
            "over_90_days": round(totals["over_90"], 4),
        },
        "suppliers": aging_data,
    }


def _empty_summary():
    return {
        "total_outstanding": 0, "current": 0,
        "1_30_days": 0, "31_60_days": 0, "61_90_days": 0, "over_90_days": 0,
    }


@router.get("/customer-statement/{customer_id}")
async def get_customer_statement(
    customer_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate customer statement showing all transactions"""
    # Get customer
    customer_result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = customer_result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    if not start_date:
        start_date = date(date.today().year, 1, 1)
    if not end_date:
        end_date = date.today()

    # Get sales
    sales_result = await db.execute(
        select(Sale)
        .where(Sale.customer_id == customer_id)
        .where(Sale.created_at >= datetime.combine(start_date, datetime.min.time()))
        .where(Sale.created_at <= datetime.combine(end_date, datetime.max.time()))
        .order_by(Sale.created_at)
    )
    sales = sales_result.scalars().all()

    # Get payments
    payments_result = await db.execute(
        select(CustomerPayment)
        .where(CustomerPayment.customer_id == customer_id)
        .where(CustomerPayment.payment_date >= datetime.combine(start_date, datetime.min.time()))
        .where(CustomerPayment.payment_date <= datetime.combine(end_date, datetime.max.time()))
        .order_by(CustomerPayment.payment_date)
    )
    payments = payments_result.scalars().all()

    # Build statement
    transactions = []
    balance = Decimal("0")

    for sale in sales:
        balance += sale.final_amount
        transactions.append({
            "date": str(sale.created_at.date()) if sale.created_at else None,
            "type": "SALE",
            "reference": sale.invoice_number or f"SALE-{sale.id}",
            "description": f"Sale Invoice",
            "debit": sale.final_amount,
            "credit": 0,
            "balance": round(float(balance), 4),
        })

    for payment in payments:
        balance -= payment.amount
        transactions.append({
            "date": str(payment.payment_date.date()) if payment.payment_date else None,
            "type": "PAYMENT",
            "reference": f"PAY-{payment.id}",
            "description": f"Payment ({payment.payment_method})",
            "debit": 0,
            "credit": payment.amount,
            "balance": round(float(balance), 4),
        })

    # Sort by date
    transactions.sort(key=lambda x: x["date"] or "")

    return {
        "customer": {
            "id": customer.id,
            "code": customer.code,
            "name": customer.name,
            "current_balance": customer.current_balance,
        },
        "period": {"start": str(start_date), "end": str(end_date)},
        "transactions": transactions,
        "closing_balance": round(float(balance), 4),
    }


@router.get("/supplier-statement/{supplier_id}")
async def get_supplier_statement(
    supplier_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate supplier statement showing all transactions"""
    # Get supplier
    supplier_result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = supplier_result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    if not start_date:
        start_date = date(date.today().year, 1, 1)
    if not end_date:
        end_date = date.today()

    # Get purchases
    purchases_result = await db.execute(
        select(Purchase)
        .where(Purchase.supplier_id == supplier_id)
        .where(Purchase.created_at >= datetime.combine(start_date, datetime.min.time()))
        .where(Purchase.created_at <= datetime.combine(end_date, datetime.max.time()))
        .order_by(Purchase.created_at)
    )
    purchases = purchases_result.scalars().all()

    # Get payments
    payments_result = await db.execute(
        select(SupplierPayment)
        .where(SupplierPayment.supplier_id == supplier_id)
        .where(SupplierPayment.payment_date >= datetime.combine(start_date, datetime.min.time()))
        .where(SupplierPayment.payment_date <= datetime.combine(end_date, datetime.max.time()))
        .order_by(SupplierPayment.payment_date)
    )
    payments = payments_result.scalars().all()

    # Build statement
    transactions = []
    balance = Decimal("0")

    for purchase in purchases:
        balance += purchase.final_amount
        transactions.append({
            "date": str(purchase.created_at.date()) if purchase.created_at else None,
            "type": "PURCHASE",
            "reference": purchase.invoice_number or f"PUR-{purchase.id}",
            "description": f"Purchase Invoice",
            "debit": 0,
            "credit": purchase.final_amount,
            "balance": round(float(balance), 4),
        })

    for payment in payments:
        balance -= payment.amount
        transactions.append({
            "date": str(payment.payment_date.date()) if payment.payment_date else None,
            "type": "PAYMENT",
            "reference": f"PAY-{payment.id}",
            "description": f"Payment ({payment.payment_method})",
            "debit": payment.amount,
            "credit": 0,
            "balance": round(float(balance), 4),
        })

    # Sort by date
    transactions.sort(key=lambda x: x["date"] or "")

    return {
        "supplier": {
            "id": supplier.id,
            "code": supplier.code,
            "name": supplier.name,
            "current_balance": supplier.current_balance,
        },
        "period": {"start": str(start_date), "end": str(end_date)},
        "transactions": transactions,
        "closing_balance": round(float(balance), 4),
    }


@router.get("/debtors-creditors")
async def get_debtors_creditors(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """المدينون والدائنون — combined debtors & creditors position report.

    Lists customers (debtors) that owe the company and suppliers (creditors)
    the company owes money to, plus the ledger-backed AR/AP totals so the
    report can be reconciled against the books (accounts 1201/2111).
    """
    if not as_of_date:
        as_of_date = date.today()

    cust_cond = [Customer.current_balance > 0]
    supp_cond = [Supplier.current_balance > 0]
    if company_id:
        cust_cond.append(Customer.company_id == company_id)
        supp_cond.append(Supplier.company_id == company_id)

    customers = (await db.execute(
        select(Customer).where(and_(*cust_cond)).order_by(Customer.name)
    )).scalars().all()
    suppliers = (await db.execute(
        select(Supplier).where(and_(*supp_cond)).order_by(Supplier.name)
    )).scalars().all()

    debtors = [{
        "id": c.id,
        "code": c.code,
        "name": c.name or c.name_ar,
        "outstanding": round(float(c.current_balance or 0), 4),
    } for c in customers]
    creditors = [{
        "id": s.id,
        "code": s.code,
        "name": s.name or s.name_ar,
        "outstanding": round(float(s.current_balance or 0), 4),
    } for s in suppliers]

    # Ledger-backed totals for reconciliation (accounts 1201 / 2111).
    ledger_result = await db.execute(
        select(
            Account.account_code,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("db"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("cr"),
        )
        .join(Account, Account.id == JournalEntryLine.account_id)
        .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
        .where(
            JournalEntry.status.in_(_LEDGER_STATUSES),
            Account.account_code.in_(["1201", "2111"]),
        )
        .group_by(Account.account_code)
    )
    ar_balance = 0.0
    ap_balance = 0.0
    for row in ledger_result.all():
        net = float(row.db or 0) - float(row.cr or 0)
        if row.account_code == "1201":
            ar_balance = net
        elif row.account_code == "2111":
            ap_balance = -net  # AP is a liability: credit balance = payable

    total_debtors = round(sum(d["outstanding"] for d in debtors), 4)
    total_creditors = round(sum(c["outstanding"] for c in creditors), 4)

    return {
        "as_of_date": str(as_of_date),
        "debtors": {
            "total": total_debtors,
            "count": len(debtors),
            "items": debtors,
        },
        "creditors": {
            "total": total_creditors,
            "count": len(creditors),
            "items": creditors,
        },
        "ledger": {
            "ar_balance": round(ar_balance, 4),
            "ap_balance": round(ap_balance, 4),
            "net_position": round(ar_balance - ap_balance, 4),
        },
        "summary": {
            "total_debtors": total_debtors,
            "total_creditors": total_creditors,
        },
    }
