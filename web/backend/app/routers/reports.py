from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.models.sales import Sale, SaleItem
from app.models.purchases import Purchase, PurchaseItem
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/sales-summary")
async def sales_summary(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(
        func.count(Sale.id),
        func.coalesce(func.sum(Sale.total_amount), 0),
        func.coalesce(func.sum(Sale.discount), 0),
        func.coalesce(func.sum(Sale.final_amount), 0),
        func.coalesce(func.sum(Sale.tax_amount), 0),
    )
    if from_date:
        query = query.where(Sale.created_at >= from_date)
    if to_date:
        query = query.where(Sale.created_at <= to_date)
    result = await db.execute(query)
    row = result.one()

    paid = (await db.execute(select(func.count(Sale.id)).where(Sale.payment_status == "paid"))).scalar() or 0
    unpaid = (await db.execute(select(func.count(Sale.id)).where(Sale.payment_status != "paid"))).scalar() or 0

    return {
        "total_sales": row[0], "total_amount": float(row[1]),
        "total_discount": float(row[2]), "total_final": float(row[3]),
        "total_tax": float(row[4]), "paid_count": paid, "unpaid_count": unpaid,
    }


@router.get("/sales-by-product")
async def sales_by_product(
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(SaleItem.product_id, func.sum(SaleItem.quantity).label("total_qty"),
               func.sum(SaleItem.total_price).label("total_revenue"))
        .group_by(SaleItem.product_id)
        .order_by(func.sum(SaleItem.total_price).desc())
        .limit(limit)
    )
    return [{"product_id": r[0], "total_quantity": r[1], "total_revenue": float(r[2])}
            for r in result.all()]


@router.get("/purchases-summary")
async def purchases_summary(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(
        func.count(Purchase.id),
        func.coalesce(func.sum(Purchase.total_amount), 0),
        func.coalesce(func.sum(Purchase.discount), 0),
        func.coalesce(func.sum(Purchase.final_amount), 0),
        func.coalesce(func.sum(Purchase.tax_amount), 0),
    )
    if from_date:
        query = query.where(Purchase.created_at >= from_date)
    if to_date:
        query = query.where(Purchase.created_at <= to_date)
    result = await db.execute(query)
    row = result.one()

    pending = (await db.execute(select(func.count(Purchase.id)).where(Purchase.payment_status == "pending"))).scalar() or 0
    paid = (await db.execute(select(func.count(Purchase.id)).where(Purchase.payment_status == "paid"))).scalar() or 0

    return {
        "total_purchases": row[0], "total_amount": float(row[1]),
        "total_discount": float(row[2]), "total_final": float(row[3]),
        "total_tax": float(row[4]), "pending_count": pending, "paid_count": paid,
    }


@router.get("/inventory-summary")
async def inventory_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_products = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar() or 0
    low_stock = (await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True, Product.current_stock <= Product.min_stock)
    )).scalar() or 0
    total_value = (await db.execute(
        select(func.coalesce(func.sum(Product.current_stock * Product.purchase_price), 0))
        .where(Product.is_active == True)
    )).scalar() or 0
    total_movements = (await db.execute(select(func.count(StockMovement.id)))).scalar() or 0

    return {
        "total_products": total_products, "low_stock_count": low_stock,
        "total_inventory_value": float(total_value), "total_movements": total_movements,
    }


@router.get("/financial-summary")
async def financial_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_accounts = (await db.execute(select(func.count(Account.id)).where(Account.is_active == True))).scalar() or 0
    posted_entries = (await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.status == "posted")
    )).scalar() or 0
    draft_entries = (await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.status == "draft")
    )).scalar() or 0
    total_debit = (await db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.debit), 0))
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntry.status == "posted")
    )).scalar() or 0
    total_credit = (await db.execute(
        select(func.coalesce(func.sum(JournalEntryLine.credit), 0))
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntry.status == "posted")
    )).scalar() or 0

    return {
        "total_accounts": total_accounts, "posted_entries": posted_entries,
        "draft_entries": draft_entries, "total_debit": float(total_debit),
        "total_credit": float(total_credit),
        "is_balanced": abs(float(total_debit) - float(total_credit)) < 0.01,
    }


@router.get("/dashboard")
async def dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total_sales = (await db.execute(select(func.count(Sale.id)))).scalar() or 0
    total_purchases = (await db.execute(select(func.count(Purchase.id)))).scalar() or 0
    total_products = (await db.execute(select(func.count(Product.id)).where(Product.is_active == True))).scalar() or 0
    total_revenue = (await db.execute(select(func.coalesce(func.sum(Sale.final_amount), 0)))).scalar() or 0
    total_cost = (await db.execute(select(func.coalesce(func.sum(Purchase.final_amount), 0)))).scalar() or 0
    low_stock = (await db.execute(
        select(func.count(Product.id)).where(Product.is_active == True, Product.current_stock <= Product.min_stock)
    )).scalar() or 0

    recent_sales_result = await db.execute(select(Sale).order_by(Sale.id.desc()).limit(5))
    recent_sales = [{"id": s.id, "final_amount": s.final_amount, "payment_status": s.payment_status,
                     "created_at": s.created_at.isoformat() if s.created_at else None}
                    for s in recent_sales_result.scalars().all()]

    return {
        "total_sales": total_sales, "total_purchases": total_purchases,
        "total_products": total_products, "total_revenue": float(total_revenue),
        "total_cost": float(total_cost), "profit": float(total_revenue) - float(total_cost),
        "low_stock_alerts": low_stock, "recent_sales": recent_sales,
    }
