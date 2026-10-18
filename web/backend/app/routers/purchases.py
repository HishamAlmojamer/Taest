import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.purchases import Purchase, PurchaseItem
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user
from pydantic import BaseModel
from typing import List
from app.utils.event_emitter import emit_goods_received
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int
    unit_price: float
    total_price: float


class PurchaseCreate(BaseModel):
    supplier_id: Optional[int] = None
    total_amount: float
    discount: float = 0
    final_amount: float
    payment_status: str = "pending"
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1
    invoice_number: Optional[str] = None
    tax_amount: float = 0
    tax_id: Optional[int] = None
    notes: Optional[str] = None
    items: List[PurchaseItemCreate] = []


def _build_purchase_response(purchase: Purchase, items: list) -> dict:
    return {
        "id": purchase.id,
        "supplier_id": purchase.supplier_id,
        "total_amount": purchase.total_amount,
        "discount": purchase.discount,
        "final_amount": purchase.final_amount,
        "payment_status": purchase.payment_status,
        "workflow_state": purchase.workflow_state,
        "company_id": purchase.company_id,
        "branch_id": purchase.branch_id,
        "invoice_number": purchase.invoice_number,
        "tax_amount": purchase.tax_amount,
        "tax_id": purchase.tax_id,
        "notes": purchase.notes,
        "created_by": purchase.created_by,
        "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        "items": [
            {"id": i.id, "purchase_id": i.purchase_id, "product_id": i.product_id,
             "quantity": i.quantity, "unit_price": i.unit_price, "total_price": i.total_price}
            for i in items
        ],
    }


@router.get("", response_model=PaginationResponse)
async def list_purchases(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    payment_status: Optional[str] = None,
    workflow_state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Purchase)
    count_query = select(func.count(Purchase.id))

    if search:
        query = query.where(Purchase.invoice_number.ilike(f"%{search}%"))
        count_query = count_query.where(Purchase.invoice_number.ilike(f"%{search}%"))
    if payment_status:
        query = query.where(Purchase.payment_status == payment_status)
        count_query = count_query.where(Purchase.payment_status == payment_status)
    if workflow_state:
        query = query.where(Purchase.workflow_state == workflow_state)
        count_query = count_query.where(Purchase.workflow_state == workflow_state)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Purchase.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    purchases = result.scalars().all()

    items = []
    if purchases:
        purchase_ids = [p.id for p in purchases]
        items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id.in_(purchase_ids)))
        all_items = items_result.scalars().all()
        items_by_purchase = {}
        for it in all_items:
            items_by_purchase.setdefault(it.purchase_id, []).append(it)
        for p in purchases:
            items.append(_build_purchase_response(p, items_by_purchase.get(p.id, [])))

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/{purchase_id}")
async def get_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id))
    return _build_purchase_response(purchase, items_result.scalars().all())


@router.post("", response_model=dict)
async def create_purchase(data: PurchaseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    purchase = Purchase(
        supplier_id=data.supplier_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_status=data.payment_status, workflow_state="draft",
        company_id=data.company_id, branch_id=data.branch_id,
        invoice_number=data.invoice_number, tax_amount=data.tax_amount,
        tax_id=data.tax_id, notes=data.notes, created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(purchase)
    await db.flush()
    for item in data.items:
        db.add(PurchaseItem(
            purchase_id=purchase.id, product_id=item.product_id,
            quantity=item.quantity, unit_price=item.unit_price, total_price=item.total_price,
        ))
    await db.flush()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id))
    return _build_purchase_response(purchase, items_result.scalars().all())


@router.put("/{purchase_id}", response_model=dict)
async def update_purchase(purchase_id: int, data: PurchaseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot edit a submitted/approved purchase")

    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(
        supplier_id=data.supplier_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_status=data.payment_status, company_id=data.company_id,
        branch_id=data.branch_id, invoice_number=data.invoice_number,
        tax_amount=data.tax_amount, tax_id=data.tax_id, notes=data.notes,
    ))
    await db.execute(delete(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    for item in data.items:
        db.add(PurchaseItem(
            purchase_id=purchase_id, product_id=item.product_id,
            quantity=item.quantity, unit_price=item.unit_price, total_price=item.total_price,
        ))
    await db.flush()
    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return _build_purchase_response(refreshed, items_result.scalars().all())


@router.delete("/{purchase_id}", response_model=MessageResponse)
async def delete_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot delete a submitted/approved purchase")
    await db.execute(delete(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    await db.execute(delete(Purchase).where(Purchase.id == purchase_id))
    return MessageResponse(message="Purchase deleted")


@router.post("/{purchase_id}/submit", response_model=dict)
async def submit_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state != "draft":
        raise HTTPException(status_code=400, detail="Only draft purchases can be submitted")
    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(workflow_state="submitted"))
    await db.flush()
    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return _build_purchase_response(refreshed, items_result.scalars().all())


@router.post("/{purchase_id}/approve", response_model=dict)
async def approve_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted purchases can be approved")

    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(workflow_state="approved"))
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    items = items_result.scalars().all()
    for item in items:
        if item.product_id:
            prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = prod_result.scalar_one_or_none()
            if product:
                product.current_stock = (product.current_stock or 0) + item.quantity
                db.add(StockMovement(
                    product_id=item.product_id, movement_type="in",
                    quantity=item.quantity, reference_type="purchase",
                    reference_id=purchase_id, created_by=current_user.id,
                    created_at=datetime.utcnow(),
                ))
    await db.flush()

    for item in items:
        if item.product_id:
            prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = prod_result.scalar_one_or_none()
            if product:
                unit_cost = float(item.unit_price or 0)
                total_cost = unit_cost * item.quantity
                try:
                    await emit_goods_received(
                        transaction_id=item.id,
                        product_id=item.product_id,
                        product_name=product.name,
                        warehouse_id=1,
                        warehouse_name="Main Warehouse",
                        quantity=item.quantity,
                        unit_cost=unit_cost,
                        total_cost=total_cost,
                        user_id=current_user.id,
                        company_id=purchase.company_id,
                    )
                    logger.info(f"Purchases: emitted goods.received event for purchase item {item.id}")
                except Exception as e:
                    logger.warning(f"Purchases: failed to emit goods.received event: {e}")

    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    return _build_purchase_response(refreshed, items)
