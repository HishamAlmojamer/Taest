import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.returns import (
    SalesReturn, SalesReturnItem, PurchaseReturn, PurchaseReturnItem,
)
from app.models.sales import Customer
from app.models.purchases import Supplier
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.schemas.returns import (
    SalesReturnCreate, PurchaseReturnCreate,
)
from app.schemas.common import PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.event_emitter import (
    emit_sales_return_approved, emit_purchase_return_approved,
)

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


def math_ceil(n):
    return int(n) + (1 if n % 1 > 0 else 0)


# ── Helpers ───────────────────────────────────────

async def _build_sales_return(sales_return, items, db) -> dict:
    customer_name = ""
    if sales_return.customer_id:
        cust = (await db.execute(select(Customer).where(Customer.id == sales_return.customer_id))).scalar_one_or_none()
        if cust:
            customer_name = cust.name

    product_ids = list({i.product_id for i in items if i.product_id})
    product_map = {}
    if product_ids:
        pr = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p.name for p in pr.scalars().all()}

    return {
        "id": sales_return.id,
        "return_number": sales_return.return_number,
        "sale_id": sales_return.sale_id,
        "sale_invoice_number": sales_return.sale_invoice_number,
        "customer_id": sales_return.customer_id,
        "customer_name": customer_name,
        "return_date": sales_return.return_date,
        "total_amount": float(sales_return.total_amount or 0),
        "tax_amount": float(sales_return.tax_amount or 0),
        "final_amount": float(sales_return.final_amount or 0),
        "status": sales_return.status,
        "reason": sales_return.reason,
        "refund_method": sales_return.refund_method,
        "journal_entry_id": sales_return.journal_entry_id,
        "is_posted_to_ledger": sales_return.journal_entry_id is not None,
        "isPostedToLedger": sales_return.journal_entry_id is not None,
        "company_id": sales_return.company_id,
        "branch_id": sales_return.branch_id,
        "notes": sales_return.notes,
        "is_restocked": bool(sales_return.is_restocked),
        "created_at": sales_return.created_at.isoformat() if sales_return.created_at else None,
        "items": [
            {
                "id": i.id, "return_id": i.return_id, "product_id": i.product_id,
                "product_name": product_map.get(i.product_id, ""),
                "quantity": i.quantity, "unit_price": float(i.unit_price or 0),
                "total_price": float(i.total_price or 0),
                "tax_amount": float(i.tax_amount or 0), "reason": i.reason,
            }
            for i in items
        ],
    }


async def _build_sales_return_list(returns: list, db: AsyncSession) -> list:
    if not returns:
        return []
    result = []
    for sr in returns:
        items = (await db.execute(select(SalesReturnItem).where(SalesReturnItem.return_id == sr.id))).scalars().all()
        result.append(await _build_sales_return(sr, items, db))
    return result


# ── Sales Returns CRUD ────────────────────────────

@router.get("/sales")
async def list_sales_returns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(SalesReturn)
    count_query = select(func.count(SalesReturn.id))
    if search:
        query = query.where(SalesReturn.return_number.ilike(f"%{search}%"))
        count_query = count_query.where(SalesReturn.return_number.ilike(f"%{search}%"))
    if status:
        query = query.where(SalesReturn.status == status)
        count_query = count_query.where(SalesReturn.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(SalesReturn.id.desc()).offset(offset).limit(per_page))
    returns = list(result.scalars().all())
    items = await _build_sales_return_list(returns, db)

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math_ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/sales/{return_id}")
async def get_sales_return(return_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    sr = (await db.execute(select(SalesReturn).where(SalesReturn.id == return_id))).scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Sales return not found")
    items = (await db.execute(select(SalesReturnItem).where(SalesReturnItem.return_id == sr.id))).scalars().all()
    return await _build_sales_return(sr, items, db)


@router.post("/sales", response_model=dict)
async def create_sales_return(data: SalesReturnCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_SALE"))):
    count = (await db.execute(select(func.count(SalesReturn.id)))).scalar() or 0
    return_number = f"SR-{datetime.now().year}-{count + 1:05d}"

    sales_return = SalesReturn(
        return_number=return_number,
        sale_id=data.sale_id,
        sale_invoice_number=data.sale_invoice_number,
        customer_id=data.customer_id,
        return_date=data.return_date or datetime.now(UTC).replace(tzinfo=None),
        total_amount=data.total_amount,
        tax_amount=data.tax_amount,
        final_amount=data.final_amount,
        status="draft",
        reason=data.reason,
        refund_method=data.refund_method,
        company_id=data.company_id,
        branch_id=data.branch_id,
        notes=data.notes,
        is_restocked=data.is_restocked,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(sales_return)
    await db.flush()

    for item in data.items:
        db.add(SalesReturnItem(
            return_id=sales_return.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
            tax_amount=item.tax_amount,
            reason=item.reason,
        ))
    await db.flush()
    return {"id": sales_return.id, "return_number": return_number, "message": "Sales return created"}


@router.post("/sales/{return_id}/approve", response_model=dict)
async def approve_sales_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("APPROVE_SALE")),
):
    """
    Approve a sales return.

    Accounting Logic:
      1. Update status to 'approved'
      2. If is_restocked, increase product stock + create stock movements
    """
    sr = (await db.execute(select(SalesReturn).where(SalesReturn.id == return_id))).scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Sales return not found")
    if sr.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft returns can be approved")

    await db.execute(update(SalesReturn).where(SalesReturn.id == return_id).values(
        status="approved", approved_by=current_user.id, approved_at=datetime.now(UTC).replace(tzinfo=None),
    ))

    # Restock products
    items = (await db.execute(select(SalesReturnItem).where(SalesReturnItem.return_id == return_id))).scalars().all()
    if sr.is_restocked:
        for item in items:
            if item.product_id:
                await db.execute(update(Product).where(Product.id == item.product_id).values(
                    current_stock=Product.current_stock + (item.quantity or 0),
                ))
                db.add(StockMovement(
                    product_id=item.product_id,
                    movement_type="in",
                    quantity=item.quantity or 0,
                    reference_type="sales_return",
                    reference_id=return_id,
                    created_by=current_user.id,
                    created_at=datetime.now(UTC).replace(tzinfo=None),
                ))

    # Emit sales.return.approved ledger event within this transaction.
    customer_name = ""
    if sr.customer_id:
        cust = (await db.execute(select(Customer).where(Customer.id == sr.customer_id))).scalar_one_or_none()
        if cust:
            customer_name = cust.name

    event_result = await emit_sales_return_approved(
        return_id=return_id,
        return_number=sr.return_number,
        sale_id=sr.sale_id,
        sale_invoice_number=sr.sale_invoice_number,
        customer_id=sr.customer_id or 0,
        customer_name=customer_name,
        total_amount=float(sr.total_amount or 0),
        tax_amount=float(sr.tax_amount or 0),
        final_amount=float(sr.final_amount or 0),
        refund_method=sr.refund_method or "cash",
        is_restocked=bool(sr.is_restocked),
        items=[
            {
                "productId": i.product_id,
                "quantity": i.quantity or 0,
                "unitPrice": float(i.unit_price or 0),
                "totalPrice": float(i.total_price or 0),
            }
            for i in items
        ],
        user_id=current_user.id,
        company_id=sr.company_id,
    )
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(SalesReturn).where(SalesReturn.id == return_id).values(journal_entry_id=entry_id))

    await db.flush()
    return {"id": return_id, "message": "Sales return approved",
            "journal_entry_id": entry_id}


@router.post("/sales/{return_id}/void", response_model=dict)
async def void_sales_return(return_id: int, reason: str = "", data: Optional[dict] = Body(None), db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("APPROVE_SALE"))):
    reason = reason or (data or {}).get("reason", "")
    sr = (await db.execute(select(SalesReturn).where(SalesReturn.id == return_id))).scalar_one_or_none()
    if not sr:
        raise HTTPException(status_code=404, detail="Sales return not found")
    if sr.status not in ("draft", "submitted"):
        raise HTTPException(status_code=400, detail="Only non-approved returns can be voided")
    await db.execute(update(SalesReturn).where(SalesReturn.id == return_id).values(
        status="voided", reason=reason or sr.reason,
    ))
    await db.flush()
    return {"message": "Sales return voided"}


# ── Purchase Returns CRUD ─────────────────────────

async def _build_purchase_return(pr, items, db) -> dict:
    supplier_name = ""
    if pr.supplier_id:
        sup = (await db.execute(select(Supplier).where(Supplier.id == pr.supplier_id))).scalar_one_or_none()
        if sup:
            supplier_name = sup.name

    product_ids = list({i.product_id for i in items if i.product_id})
    product_map = {}
    if product_ids:
        prd = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p.name for p in prd.scalars().all()}

    return {
        "id": pr.id,
        "return_number": pr.return_number,
        "purchase_id": pr.purchase_id,
        "purchase_order_number": pr.purchase_order_number,
        "supplier_id": pr.supplier_id,
        "supplier_name": supplier_name,
        "return_date": pr.return_date,
        "total_amount": float(pr.total_amount or 0),
        "tax_amount": float(pr.tax_amount or 0),
        "final_amount": float(pr.final_amount or 0),
        "status": pr.status,
        "reason": pr.reason,
        "refund_method": pr.refund_method,
        "journal_entry_id": pr.journal_entry_id,
        "is_posted_to_ledger": pr.journal_entry_id is not None,
        "isPostedToLedger": pr.journal_entry_id is not None,
        "company_id": pr.company_id,
        "branch_id": pr.branch_id,
        "notes": pr.notes,
        "is_restocked": bool(pr.is_restocked),
        "created_at": pr.created_at.isoformat() if pr.created_at else None,
        "items": [
            {
                "id": i.id, "return_id": i.return_id, "product_id": i.product_id,
                "product_name": product_map.get(i.product_id, ""),
                "quantity": i.quantity, "unit_cost": float(i.unit_cost or 0),
                "total_cost": float(i.total_cost or 0),
                "tax_amount": float(i.tax_amount or 0), "reason": i.reason,
            }
            for i in items
        ],
    }


@router.get("/purchases")
async def list_purchase_returns(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(PurchaseReturn)
    count_query = select(func.count(PurchaseReturn.id))
    if search:
        query = query.where(PurchaseReturn.return_number.ilike(f"%{search}%"))
        count_query = count_query.where(PurchaseReturn.return_number.ilike(f"%{search}%"))
    if status:
        query = query.where(PurchaseReturn.status == status)
        count_query = count_query.where(PurchaseReturn.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(PurchaseReturn.id.desc()).offset(offset).limit(per_page))
    returns = list(result.scalars().all())
    items = []
    for pr in returns:
        pr_items = (await db.execute(select(PurchaseReturnItem).where(PurchaseReturnItem.return_id == pr.id))).scalars().all()
        items.append(await _build_purchase_return(pr, pr_items, db))

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math_ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/purchases/{return_id}")
async def get_purchase_return(return_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pr = (await db.execute(select(PurchaseReturn).where(PurchaseReturn.id == return_id))).scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    items = (await db.execute(select(PurchaseReturnItem).where(PurchaseReturnItem.return_id == pr.id))).scalars().all()
    return await _build_purchase_return(pr, items, db)


@router.post("/purchases", response_model=dict)
async def create_purchase_return(data: PurchaseReturnCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_PURCHASE"))):
    count = (await db.execute(select(func.count(PurchaseReturn.id)))).scalar() or 0
    return_number = f"PR-{datetime.now().year}-{count + 1:05d}"

    purchase_return = PurchaseReturn(
        return_number=return_number,
        purchase_id=data.purchase_id,
        purchase_order_number=data.purchase_order_number,
        supplier_id=data.supplier_id,
        return_date=data.return_date or datetime.now(UTC).replace(tzinfo=None),
        total_amount=data.total_amount,
        tax_amount=data.tax_amount,
        final_amount=data.final_amount,
        status="draft",
        reason=data.reason,
        refund_method=data.refund_method,
        company_id=data.company_id,
        branch_id=data.branch_id,
        notes=data.notes,
        is_restocked=data.is_restocked,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(purchase_return)
    await db.flush()

    for item in data.items:
        db.add(PurchaseReturnItem(
            return_id=purchase_return.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_cost=item.unit_cost,
            total_cost=item.total_cost,
            tax_amount=item.tax_amount,
            reason=item.reason,
        ))
    await db.flush()
    return {"id": purchase_return.id, "return_number": return_number, "message": "Purchase return created"}


@router.post("/purchases/{return_id}/approve", response_model=dict)
async def approve_purchase_return(
    return_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("APPROVE_PURCHASE")),
):
    """
    Approve a purchase return.

    Accounting Logic:
      1. Update status to 'approved'
      2. If is_restocked, decrease product stock + create stock movements
    """
    pr = (await db.execute(select(PurchaseReturn).where(PurchaseReturn.id == return_id))).scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    if pr.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft returns can be approved")

    await db.execute(update(PurchaseReturn).where(PurchaseReturn.id == return_id).values(
        status="approved", approved_by=current_user.id, approved_at=datetime.now(UTC).replace(tzinfo=None),
    ))

    items = (await db.execute(select(PurchaseReturnItem).where(PurchaseReturnItem.return_id == return_id))).scalars().all()
    if pr.is_restocked:
        for item in items:
            if item.product_id:
                await db.execute(update(Product).where(Product.id == item.product_id).values(
                    current_stock=Product.current_stock - (item.quantity or 0),
                ))
                db.add(StockMovement(
                    product_id=item.product_id,
                    movement_type="out",
                    quantity=item.quantity or 0,
                    reference_type="purchase_return",
                    reference_id=return_id,
                    created_by=current_user.id,
                    created_at=datetime.now(UTC).replace(tzinfo=None),
                ))

    # Emit purchase.return.approved ledger event within this transaction.
    supplier_name = ""
    if pr.supplier_id:
        sup = (await db.execute(select(Supplier).where(Supplier.id == pr.supplier_id))).scalar_one_or_none()
        if sup:
            supplier_name = sup.name

    event_result = await emit_purchase_return_approved(
        return_id=return_id,
        return_number=pr.return_number,
        purchase_id=pr.purchase_id,
        purchase_order_number=pr.purchase_order_number,
        supplier_id=pr.supplier_id or 0,
        supplier_name=supplier_name,
        total_amount=float(pr.total_amount or 0),
        tax_amount=float(pr.tax_amount or 0),
        final_amount=float(pr.final_amount or 0),
        refund_method=pr.refund_method or "cash",
        is_restocked=bool(pr.is_restocked),
        items=[
            {
                "productId": i.product_id,
                "quantity": i.quantity or 0,
                "unitCost": float(i.unit_cost or 0),
                "totalCost": float(i.total_cost or 0),
            }
            for i in items
        ],
        user_id=current_user.id,
        company_id=pr.company_id,
    )
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(PurchaseReturn).where(PurchaseReturn.id == return_id).values(journal_entry_id=entry_id))

    await db.flush()
    return {"id": return_id, "message": "Purchase return approved",
            "journal_entry_id": entry_id}


@router.post("/purchases/{return_id}/void", response_model=dict)
async def void_purchase_return(return_id: int, reason: str = "", data: Optional[dict] = Body(None), db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("APPROVE_PURCHASE"))):
    reason = reason or (data or {}).get("reason", "")
    pr = (await db.execute(select(PurchaseReturn).where(PurchaseReturn.id == return_id))).scalar_one_or_none()
    if not pr:
        raise HTTPException(status_code=404, detail="Purchase return not found")
    if pr.status not in ("draft", "submitted"):
        raise HTTPException(status_code=400, detail="Only non-approved returns can be voided")
    await db.execute(update(PurchaseReturn).where(PurchaseReturn.id == return_id).values(
        status="voided", reason=reason or pr.reason,
    ))
    await db.flush()
    return {"message": "Purchase return voided"}
