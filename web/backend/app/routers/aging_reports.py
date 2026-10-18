"""
Accounts Receivable and Accounts Payable Aging Reports.
"""

from datetime import datetime, date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.sales import Customer, Sale, SaleItem
from app.models.purchases import Supplier, Purchase, PurchaseItem
from app.models.payments import CustomerPayment, SupplierPayment
from app.utils.deps import get_current_active_user

router = APIRouter()


def calculate_aging_buckets(invoice_date: date, amount: float, today: date) -> dict:
    """Calculate aging buckets for an invoice"""
    days_overdue = (today - invoice_date).days
    if days_overdue <= 0:
        return {"current": amount, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": 0}
    elif days_overdue <= 30:
        return {"current": 0, "1_30": amount, "31_60": 0, "61_90": 0, "over_90": 0}
    elif days_overdue <= 60:
        return {"current": 0, "1_30": 0, "31_60": amount, "61_90": 0, "over_90": 0}
    elif days_overdue <= 90:
        return {"current": 0, "1_30": 0, "31_60": 0, "61_90": amount, "over_90": 0}
    else:
        return {"current": 0, "1_30": 0, "31_60": 0, "61_90": 0, "over_90": amount}


@router.get("/ar-aging")
async def get_ar_aging(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate Accounts Receivable Aging Report.
    Shows customer balances by aging buckets (0-30, 31-60, 61-90, 90+ days).
    """
    if not as_of_date:
        as_of_date = date.today()

    # Get customers with outstanding balances
    conditions = [Customer.current_balance > 0]
    if company_id:
        conditions.append(Customer.company_id == company_id)

    customers_result = await db.execute(
        select(Customer).where(and_(*conditions)).order_by(Customer.name)
    )
    customers = customers_result.scalars().all()

    aging_data = []
    total_current = 0.0
    total_1_30 = 0.0
    total_31_60 = 0.0
    total_61_90 = 0.0
    total_over_90 = 0.0
    total_outstanding = 0.0

    for customer in customers:
        # Get unpaid sales for this customer
        sales_result = await db.execute(
            select(Sale)
            .where(Sale.customer_id == customer.id)
            .where(Sale.payment_status != "PAID")
            .where(Sale.created_at <= datetime.combine(as_of_date, datetime.min.time()))
        )
        sales = sales_result.scalars().all()

        customer_aging = {
            "current": 0.0,
            "1_30": 0.0,
            "31_60": 0.0,
            "61_90": 0.0,
            "over_90": 0.0,
        }

        for sale in sales:
            invoice_date = sale.created_at.date() if sale.created_at else as_of_date
            amount = sale.final_amount - sum(
                p.amount for p in (await db.execute(
                    select(CustomerPayment)
                    .where(CustomerPayment.customer_id == customer.id)
                )).scalars().all()
            ) if sale.payment_status != "PAID" else 0

            if amount > 0:
                buckets = calculate_aging_buckets(invoice_date, amount, as_of_date)
                for key in customer_aging:
                    customer_aging[key] += buckets[key]

        customer_total = sum(customer_aging.values())
        if customer_total > 0:
            aging_data.append({
                "customer_id": customer.id,
                "customer_code": customer.code,
                "customer_name": customer.name,
                "outstanding_amount": round(customer_total, 4),
                "current": round(customer_aging["current"], 4),
                "1_30_days": round(customer_aging["1_30"], 4),
                "31_60_days": round(customer_aging["31_60"], 4),
                "61_90_days": round(customer_aging["61_90"], 4),
                "over_90_days": round(customer_aging["over_90"], 4),
            })

            total_current += customer_aging["current"]
            total_1_30 += customer_aging["1_30"]
            total_31_60 += customer_aging["31_60"]
            total_61_90 += customer_aging["61_90"]
            total_over_90 += customer_aging["over_90"]
            total_outstanding += customer_total

    return {
        "as_of_date": str(as_of_date),
        "summary": {
            "total_outstanding": round(total_outstanding, 4),
            "current": round(total_current, 4),
            "1_30_days": round(total_1_30, 4),
            "31_60_days": round(total_31_60, 4),
            "61_90_days": round(total_61_90, 4),
            "over_90_days": round(total_over_90, 4),
        },
        "customers": aging_data,
    }


@router.get("/ap-aging")
async def get_ap_aging(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate Accounts Payable Aging Report.
    Shows supplier balances by aging buckets (0-30, 31-60, 61-90, 90+ days).
    """
    if not as_of_date:
        as_of_date = date.today()

    # Get suppliers with outstanding balances
    conditions = [Supplier.current_balance > 0]
    if company_id:
        conditions.append(Supplier.company_id == company_id)

    suppliers_result = await db.execute(
        select(Supplier).where(and_(*conditions)).order_by(Supplier.name)
    )
    suppliers = suppliers_result.scalars().all()

    aging_data = []
    total_current = 0.0
    total_1_30 = 0.0
    total_31_60 = 0.0
    total_61_90 = 0.0
    total_over_90 = 0.0
    total_outstanding = 0.0

    for supplier in suppliers:
        # Get unpaid purchases for this supplier
        purchases_result = await db.execute(
            select(Purchase)
            .where(Purchase.supplier_id == supplier.id)
            .where(Purchase.payment_status != "PAID")
            .where(Purchase.created_at <= datetime.combine(as_of_date, datetime.min.time()))
        )
        purchases = purchases_result.scalars().all()

        supplier_aging = {
            "current": 0.0,
            "1_30": 0.0,
            "31_60": 0.0,
            "61_90": 0.0,
            "over_90": 0.0,
        }

        for purchase in purchases:
            invoice_date = purchase.created_at.date() if purchase.created_at else as_of_date
            amount = purchase.final_amount  # Simplified - should subtract payments
            if amount > 0:
                buckets = calculate_aging_buckets(invoice_date, amount, as_of_date)
                for key in supplier_aging:
                    supplier_aging[key] += buckets[key]

        supplier_total = sum(supplier_aging.values())
        if supplier_total > 0:
            aging_data.append({
                "supplier_id": supplier.id,
                "supplier_code": supplier.code,
                "supplier_name": supplier.name,
                "outstanding_amount": round(supplier_total, 4),
                "current": round(supplier_aging["current"], 4),
                "1_30_days": round(supplier_aging["1_30"], 4),
                "31_60_days": round(supplier_aging["31_60"], 4),
                "61_90_days": round(supplier_aging["61_90"], 4),
                "over_90_days": round(supplier_aging["over_90"], 4),
            })

            total_current += supplier_aging["current"]
            total_1_30 += supplier_aging["1_30"]
            total_31_60 += supplier_aging["31_60"]
            total_61_90 += supplier_aging["61_90"]
            total_over_90 += supplier_aging["over_90"]
            total_outstanding += supplier_total

    return {
        "as_of_date": str(as_of_date),
        "summary": {
            "total_outstanding": round(total_outstanding, 4),
            "current": round(total_current, 4),
            "1_30_days": round(total_1_30, 4),
            "31_60_days": round(total_31_60, 4),
            "61_90_days": round(total_61_90, 4),
            "over_90_days": round(total_over_90, 4),
        },
        "suppliers": aging_data,
    }


@router.get("/customer-statement/{customer_id}")
async def get_customer_statement(
    customer_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
    balance = 0.0

    for sale in sales:
        balance += sale.final_amount
        transactions.append({
            "date": str(sale.created_at.date()) if sale.created_at else None,
            "type": "SALE",
            "reference": sale.invoice_number or f"SALE-{sale.id}",
            "description": f"Sale Invoice",
            "debit": sale.final_amount,
            "credit": 0,
            "balance": round(balance, 4),
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
            "balance": round(balance, 4),
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
        "closing_balance": round(balance, 4),
    }


@router.get("/supplier-statement/{supplier_id}")
async def get_supplier_statement(
    supplier_id: int,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
    balance = 0.0

    for purchase in purchases:
        balance += purchase.final_amount
        transactions.append({
            "date": str(purchase.created_at.date()) if purchase.created_at else None,
            "type": "PURCHASE",
            "reference": purchase.invoice_number or f"PUR-{purchase.id}",
            "description": f"Purchase Invoice",
            "debit": 0,
            "credit": purchase.final_amount,
            "balance": round(balance, 4),
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
            "balance": round(balance, 4),
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
        "closing_balance": round(balance, 4),
    }
