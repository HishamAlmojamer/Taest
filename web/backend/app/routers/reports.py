from typing import Optional
from datetime import datetime, date, time, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.database import get_db
from app.models.sales import Sale, SaleItem, Customer
from app.models.purchases import Purchase, PurchaseItem, Supplier
from app.models.returns import SalesReturn, PurchaseReturn
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.routers.accounting import _LEDGER_STATUSES
from app.utils.deps import get_current_user

router = APIRouter()


def _parse_date(value: Optional[str], name: str) -> Optional[date]:
    if not value:
        return None
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {name} format, expected YYYY-MM-DD")


def _resolve_range(
    *,
    to_date: Optional[str] = None,
    from_date: Optional[str] = None,
    endDate: Optional[str] = None,
    startDate: Optional[str] = None,
    specific_date: Optional[str] = None,
) -> tuple[date, date]:
    """Normalize the various date filter styles into a (start, end) day range."""
    start_src = from_date or startDate or specific_date
    end_src = to_date or endDate or specific_date
    start_d = _parse_date(start_src, "from_date")
    end_d = _parse_date(end_src, "to_date")
    if start_d is None and end_d is None:
        start_d = end_d = date.today()
    if start_d is None:
        start_d = end_d
    if end_d is None:
        end_d = start_d
    if end_d < start_d:
        start_d, end_d = end_d, start_d
    return start_d, end_d


def _pct(cur: float, prev: float) -> float:
    if prev and prev > 0:
        return round((cur - prev) / prev * 100, 1)
    return 100.0 if cur > 0 else 0.0


@router.get("/sales-summary")
async def sales_summary(
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Real-time sales summary. Serves the dashboard (single `date`) and the
    sales report page (startDate/endDate range). No fake data."""
    start_d, end_d = _resolve_range(
        specific_date=date, from_date=from_date, to_date=to_date,
        startDate=startDate, endDate=endDate,
    )
    start_dt = datetime.combine(start_d, time.min)
    end_dt = datetime.combine(end_d, time.max)
    where = [Sale.created_at >= start_dt, Sale.created_at <= end_dt]

    agg = (await db.execute(
        select(
            func.count(Sale.id),
            func.coalesce(func.sum(Sale.final_amount), 0),
            func.coalesce(func.sum(Sale.tax_amount), 0),
            func.coalesce(func.sum(Sale.discount), 0),
            func.count(func.distinct(Sale.customer_id)),
        ).where(*where)
    )).one()
    total_invoices = int(agg[0])
    total_sales = float(agg[1])
    total_tax = float(agg[2])
    total_discount = float(agg[3])
    total_customers = int(agg[4])

    paid = (await db.execute(
        select(func.count(Sale.id)).where(Sale.payment_status == "paid", *where)
    )).scalar() or 0
    unpaid = (await db.execute(
        select(func.count(Sale.id)).where(Sale.payment_status != "paid", *where)
    )).scalar() or 0
    approval_pending = (await db.execute(
        select(func.count(Sale.id)).where(Sale.workflow_state.in_(["draft", "submitted"]))
    )).scalar() or 0

    hourly = (await db.execute(
        select(
            func.extract("hour", Sale.created_at).label("hour"),
            func.coalesce(func.sum(Sale.final_amount), 0),
        ).where(*where).group_by("hour").order_by("hour")
    )).all()
    hour_map = {int(h): float(amt) for h, amt in hourly}
    if start_d == end_d:
        sales_by_hour = [{"hour": h, "amount": hour_map.get(h, 0.0)} for h in range(24)]
    else:
        sales_by_hour = [{"hour": h, "amount": a} for h, a in sorted(hour_map.items())]

    sales_by_month = [
        {"month": m, "amount": float(amt)}
        for m, amt in (await db.execute(
            select(
                func.to_char(Sale.created_at, "YYYY-MM").label("month"),
                func.coalesce(func.sum(Sale.final_amount), 0),
            ).where(*where).group_by("month").order_by("month")
        )).all()
    ]

    payment_methods = [
        {"name": m or "other", "value": float(v)}
        for m, v in (await db.execute(
            select(
                func.coalesce(Sale.payment_method, "other").label("method"),
                func.coalesce(func.sum(Sale.final_amount), 0),
            ).where(*where).group_by("method").order_by("method")
        )).all()
    ]

    recent = (await db.execute(
        select(Sale).where(*where).order_by(Sale.created_at.desc(), Sale.id.desc()).limit(5)
    )).scalars().all()
    cust_ids = {s.customer_id for s in recent if s.customer_id}
    names = {}
    if cust_ids:
        names = dict((await db.execute(
            select(Customer.id, Customer.name).where(Customer.id.in_(cust_ids))
        )).all())
    recent_sales = [{
        "id": s.id,
        "invoiceNumber": s.invoice_number or f"INV-{s.id}",
        "customerName": names.get(s.customer_id, "-"),
        "total": float(s.final_amount),
        "status": s.workflow_state or s.payment_status or "approved",
    } for s in recent]

    top_products = [
        {"name": nm, "quantity": int(qty), "amount": float(rev)}
        for nm, qty, rev in (await db.execute(
            select(Product.name, func.sum(SaleItem.quantity), func.sum(SaleItem.total_price))
            .join(Sale, SaleItem.sale_id == Sale.id)
            .join(Product, SaleItem.product_id == Product.id)
            .where(*where)
            .group_by(Product.name)
            .order_by(func.sum(SaleItem.total_price).desc())
            .limit(5)
        )).all()
    ]

    top_customers = [
        {"name": nm, "amount": float(rev)}
        for nm, rev in (await db.execute(
            select(Customer.name, func.sum(Sale.final_amount))
            .join(Sale, Sale.customer_id == Customer.id)
            .where(*where, Sale.customer_id.isnot(None))
            .group_by(Customer.name)
            .order_by(func.sum(Sale.final_amount).desc())
            .limit(5)
        )).all()
    ]

    total_returns = float((await db.execute(
        select(func.coalesce(func.sum(SalesReturn.final_amount), 0)).where(
            SalesReturn.created_at >= start_dt,
            SalesReturn.created_at <= end_dt,
            SalesReturn.status == "approved",
        )
    )).scalar() or 0)

    vs_yesterday = None
    if start_d == end_d:
        y = start_d - timedelta(days=1)
        prev = (await db.execute(
            select(
                func.count(Sale.id),
                func.coalesce(func.sum(Sale.final_amount), 0),
                func.count(func.distinct(Sale.customer_id)),
            ).where(Sale.created_at >= datetime.combine(y, time.min),
                    Sale.created_at <= datetime.combine(y, time.max))
        )).one()
        prev_invoices, prev_sales, prev_customers = int(prev[0]), float(prev[1]), int(prev[2])
        vs_yesterday = {
            "sales": _pct(total_sales, prev_sales),
            "invoices": _pct(float(total_invoices), float(prev_invoices)),
            "customers": _pct(float(total_customers), float(prev_customers)),
        }

    return {
        "date": str(start_d),
        "totalSales": round(total_sales, 4),
        "totalReturns": round(total_returns, 4),
        "netSales": round(total_sales - total_returns, 4),
        "totalInvoices": total_invoices,
        "totalCustomers": total_customers,
        "salesByHour": sales_by_hour,
        "salesByMonth": sales_by_month,
        "recentSales": recent_sales,
        "paymentMethods": payment_methods,
        "topProducts": top_products,
        "topCustomers": top_customers,
        "approvalPending": approval_pending,
        "paidCount": paid,
        "unpaidCount": unpaid,
        "vsYesterday": vs_yesterday,
        # backwards-compatible legacy keys
        "total_sales": total_invoices,
        "total_amount": round(total_sales, 4),
        "total_discount": round(total_discount, 4),
        "total_final": round(total_sales, 4),
        "total_tax": round(total_tax, 4),
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
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Real-time purchases summary with monthly trend and top suppliers."""
    start_d, end_d = _resolve_range(
        from_date=from_date, to_date=to_date, startDate=startDate, endDate=endDate,
    )
    start_dt = datetime.combine(start_d, time.min)
    end_dt = datetime.combine(end_d, time.max)
    where = [Purchase.created_at >= start_dt, Purchase.created_at <= end_dt]

    row = (await db.execute(
        select(
            func.count(Purchase.id),
            func.coalesce(func.sum(Purchase.total_amount), 0),
            func.coalesce(func.sum(Purchase.discount), 0),
            func.coalesce(func.sum(Purchase.final_amount), 0),
            func.coalesce(func.sum(Purchase.tax_amount), 0),
        ).where(*where)
    )).one()
    total_purchases = float(row[3])

    pending = (await db.execute(
        select(func.count(Purchase.id)).where(Purchase.payment_status == "pending", *where)
    )).scalar() or 0
    paid = (await db.execute(
        select(func.count(Purchase.id)).where(Purchase.payment_status == "paid", *where)
    )).scalar() or 0

    purchases_by_month = [
        {"month": m, "amount": float(amt)}
        for m, amt in (await db.execute(
            select(
                func.to_char(Purchase.created_at, "YYYY-MM").label("month"),
                func.coalesce(func.sum(Purchase.final_amount), 0),
            ).where(*where).group_by("month").order_by("month")
        )).all()
    ]

    top_suppliers = [
        {"name": nm, "amount": float(rev)}
        for nm, rev in (await db.execute(
            select(Supplier.name, func.sum(Purchase.final_amount))
            .join(Purchase, Purchase.supplier_id == Supplier.id)
            .where(*where, Purchase.supplier_id.isnot(None))
            .group_by(Supplier.name)
            .order_by(func.sum(Purchase.final_amount).desc())
            .limit(5)
        )).all()
    ]

    total_returns = float((await db.execute(
        select(func.coalesce(func.sum(PurchaseReturn.final_amount), 0)).where(
            PurchaseReturn.created_at >= start_dt,
            PurchaseReturn.created_at <= end_dt,
            PurchaseReturn.status == "approved",
        )
    )).scalar() or 0)

    return {
        "totalPurchases": round(total_purchases, 4),
        "totalReturns": round(total_returns, 4),
        "netPurchases": round(total_purchases - total_returns, 4),
        "purchasesByMonth": purchases_by_month,
        "topSuppliers": top_suppliers,
        "pendingCount": pending,
        "paidCount": paid,
        # backwards-compatible legacy keys
        "total_purchases": int(row[0]),
        "total_amount": round(float(row[1]), 4),
        "total_discount": round(float(row[2]), 4),
        "total_final": round(total_purchases, 4),
        "total_tax": round(float(row[4]), 4),
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
    """Financial snapshot computed from the actual posted ledger."""
    total_accounts = (await db.execute(select(func.count(Account.id)).where(Account.is_active == True))).scalar() or 0
    posted_entries = (await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.status == "Posted")
    )).scalar() or 0
    draft_entries = (await db.execute(
        select(func.count(JournalEntry.id)).where(JournalEntry.status == "Draft")
    )).scalar() or 0

    ledger = select(
        func.coalesce(func.sum(JournalEntryLine.debit), 0),
        func.coalesce(func.sum(JournalEntryLine.credit), 0),
    ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntry.status.in_(_LEDGER_STATUSES))
    totals = (await db.execute(ledger)).one()
    total_debit = float(totals[0])
    total_credit = float(totals[1])

    type_rows = (await db.execute(
        select(
            Account.account_type.label("atype"),
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .join(JournalEntryLine, JournalEntryLine.account_id == Account.id)
        .join(JournalEntry, and_(
            JournalEntryLine.journal_entry_id == JournalEntry.id,
            JournalEntry.status.in_(_LEDGER_STATUSES),
        ))
        .group_by("atype")
    )).all()
    by_type: dict = {}
    for atype, d, c in type_rows:
        by_type[atype] = (float(d), float(c))

    rev_d, rev_c = by_type.get("revenue", (0.0, 0.0))
    exp_d, exp_c = by_type.get("expense", (0.0, 0.0))
    asset_d, asset_c = by_type.get("asset", (0.0, 0.0))
    liab_d, liab_c = by_type.get("liability", (0.0, 0.0))
    eq_d, eq_c = by_type.get("equity", (0.0, 0.0))

    revenue = rev_c - rev_d
    expenses = exp_d - exp_c
    net_income = revenue - expenses
    assets = asset_d - asset_c
    liabilities = liab_c - liab_d
    equity = (eq_c - eq_d) + net_income

    month_rows = (await db.execute(
        select(
            func.to_char(JournalEntry.entry_date, "YYYY-MM").label("month"),
            Account.account_type.label("atype"),
            func.coalesce(func.sum(JournalEntryLine.debit), 0),
            func.coalesce(func.sum(JournalEntryLine.credit), 0),
        )
        .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES), Account.account_type.in_(["revenue", "expense"]))
        .group_by("month", "atype")
        .order_by("month")
    )).all()
    month_rev: dict = {}
    month_exp: dict = {}
    for m, atype, d, c in month_rows:
        d, c = float(d), float(c)
        if atype == "revenue":
            month_rev[m] = month_rev.get(m, 0.0) + (c - d)
        else:
            month_exp[m] = month_exp.get(m, 0.0) + (d - c)
    income_by_month = [
        {"month": m, "revenue": round(month_rev.get(m, 0.0), 4), "expenses": round(month_exp.get(m, 0.0), 4)}
        for m in sorted(set(month_rev) | set(month_exp))
    ]

    return {
        "revenue": round(revenue, 4),
        "expenses": round(expenses, 4),
        "netIncome": round(net_income, 4),
        "incomeByMonth": income_by_month,
        "assets": round(assets, 4),
        "liabilities": round(liabilities, 4),
        "equity": round(equity, 4),
        "totalAccounts": total_accounts,
        "postedEntries": posted_entries,
        "draftEntries": draft_entries,
        "totalDebit": round(total_debit, 4),
        "totalCredit": round(total_credit, 4),
        "isBalanced": abs(total_debit - total_credit) < 0.01,
        # backwards-compatible legacy keys
        "total_accounts": total_accounts,
        "posted_entries": posted_entries,
        "draft_entries": draft_entries,
        "total_debit": round(total_debit, 4),
        "total_credit": round(total_credit, 4),
        "is_balanced": abs(total_debit - total_credit) < 0.01,
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
