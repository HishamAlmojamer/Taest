import math
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.sales import Sale, SaleItem, Customer
from app.models.user import User
from app.models.inventory import Product, StockMovement
from app.schemas.sales import SaleCreate, SaleResponse
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user
from app.utils.event_emitter import emit_sale_approved, emit_goods_received
from app.models.payments import CustomerPayment

logger = logging.getLogger(__name__)

router = APIRouter()


async def _build_sale_response(sale: Sale, items: list, db: AsyncSession = None) -> dict:
    customer_name = ""
    if sale.customer_id and db:
        cust_result = await db.execute(select(Customer).where(Customer.id == sale.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    paid_amount = 0
    if db:
        pay_result = await db.execute(
            select(func.coalesce(func.sum(CustomerPayment.amount), 0))
            .where(CustomerPayment.customer_id == sale.customer_id)
        )
        paid_amount = float(pay_result.scalar() or 0)

    product_names = {}
    if db and items:
        product_ids = list(set(i.product_id for i in items if i.product_id))
        if product_ids:
            prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            for p in prod_result.scalars().all():
                product_names[p.id] = p.name

    return {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_name": customer_name,
        "customerName": customer_name,
        "total_amount": float(sale.total_amount),
        "total": float(sale.final_amount),
        "subtotal": float(sale.total_amount),
        "discount": float(sale.discount or 0),
        "final_amount": float(sale.final_amount),
        "payment_method": sale.payment_method,
        "payment_status": sale.payment_status,
        "workflow_state": sale.workflow_state,
        "status": sale.workflow_state.upper() if sale.workflow_state else None,
        "company_id": sale.company_id,
        "branch_id": sale.branch_id,
        "invoice_number": sale.invoice_number,
        "tax_amount": float(sale.tax_amount or 0),
        "tax_id": sale.tax_id,
        "notes": sale.notes,
        "created_by": sale.created_by,
        "date": sale.created_at.strftime("%Y-%m-%d") if sale.created_at else None,
        "created_at": sale.created_at.isoformat() if sale.created_at else None,
        "paid_amount": paid_amount,
        "items": [
            {
                "id": i.id, "sale_id": i.sale_id, "product_id": i.product_id,
                "product_name": product_names.get(i.product_id, ""),
                "productName": product_names.get(i.product_id, ""),
                "quantity": i.quantity,
                "unit_price": float(i.unit_price),
                "unitPrice": float(i.unit_price),
                "total_price": float(i.total_price),
                "total": float(i.total_price),
                "discount": 0,
            }
            for i in items
        ],
    }


@router.get("", response_model=PaginationResponse)
async def list_sales(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    payment_status: Optional[str] = None,
    workflow_state: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Sale)
    count_query = select(func.count(Sale.id))

    if search:
        query = query.where(Sale.invoice_number.ilike(f"%{search}%"))
        count_query = count_query.where(Sale.invoice_number.ilike(f"%{search}%"))
    if payment_status:
        query = query.where(Sale.payment_status == payment_status)
        count_query = count_query.where(Sale.payment_status == payment_status)
    if workflow_state:
        query = query.where(Sale.workflow_state == workflow_state)
        count_query = count_query.where(Sale.workflow_state == workflow_state)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Sale.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    sales = result.scalars().all()

    items = []
    if sales:
        sale_ids = [s.id for s in sales]
        items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id.in_(sale_ids)))
        all_items = items_result.scalars().all()
        items_by_sale = {}
        for it in all_items:
            items_by_sale.setdefault(it.sale_id, []).append(it)
        for s in sales:
            items.append(await _build_sale_response(s, items_by_sale.get(s.id, []), db))

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/{sale_id}")
async def get_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale.id))
    return await _build_sale_response(sale, items_result.scalars().all(), db)


@router.post("", response_model=SaleResponse)
async def create_sale(
    data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = Sale(
        customer_id=data.customer_id,
        total_amount=data.total_amount,
        discount=data.discount,
        final_amount=data.final_amount,
        payment_method=data.payment_method,
        payment_status=data.payment_status,
        workflow_state="draft",
        company_id=data.company_id,
        branch_id=data.branch_id,
        invoice_number=data.invoice_number,
        tax_amount=data.tax_amount,
        tax_id=data.tax_id,
        notes=data.notes,
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(sale)
    await db.flush()

    for item in data.items:
        sale_item = SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            total_price=item.total_price,
        )
        db.add(sale_item)

    await db.flush()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale.id))
    return await _build_sale_response(sale, items_result.scalars().all(), db)


@router.put("/{sale_id}", response_model=SaleResponse)
async def update_sale(
    sale_id: int,
    data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot edit a submitted/approved sale")

    await db.execute(update(Sale).where(Sale.id == sale_id).values(
        customer_id=data.customer_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_method=data.payment_method, payment_status=data.payment_status,
        company_id=data.company_id, branch_id=data.branch_id,
        invoice_number=data.invoice_number, tax_amount=data.tax_amount,
        tax_id=data.tax_id, notes=data.notes,
    ))
    await db.execute(delete(SaleItem).where(SaleItem.sale_id == sale_id))
    for item in data.items:
        db.add(SaleItem(
            sale_id=sale_id, product_id=item.product_id,
            quantity=item.quantity, unit_price=item.unit_price, total_price=item.total_price,
        ))
    await db.flush()

    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    return await _build_sale_response(refreshed, items_result.scalars().all(), db)


@router.delete("/{sale_id}", response_model=MessageResponse)
async def delete_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot delete a submitted/approved sale")

    await db.execute(delete(SaleItem).where(SaleItem.sale_id == sale_id))
    await db.execute(delete(Sale).where(Sale.id == sale_id))
    return MessageResponse(message="Sale deleted")


@router.post("/{sale_id}/submit", response_model=SaleResponse)
async def submit_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state != "draft":
        raise HTTPException(status_code=400, detail="Only draft sales can be submitted")

    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="submitted"))
    await db.flush()
    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    return await _build_sale_response(refreshed, items_result.scalars().all(), db)


@router.post("/{sale_id}/approve", response_model=SaleResponse)
async def approve_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Approve a sales invoice.

    Accounting Logic (per ERP_INSTRUCTIONS.md):
      1. Updates workflow_state to 'approved'
      2. Decrements product stock and creates stock movements
      3. Emits 'sales.invoice.approved' event to the Ledger Engine
      4. Ledger Engine creates a balanced journal entry:
         Dr. Accounts Receivable (1130)  finalAmount
         Cr. Sales Revenue (4100)        totalAmount
         Cr. VAT Output (2120)           taxAmount
    """
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted sales can be approved")

    # Step 1: Update workflow state
    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="approved"))

    # Step 2: Decrement stock and create stock movements
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    items = items_result.scalars().all()

    event_items = []
    for item in items:
        if item.product_id:
            prod_result = await db.execute(select(Product).where(Product.id == item.product_id))
            product = prod_result.scalar_one_or_none()
            if product:
                current_stock = float(product.current_stock or 0)
                if current_stock < item.quantity:
                    raise HTTPException(
                        status_code=400,
                        detail=f"المخزون غير كافٍ للمنتج '{product.name}': المتوفر {current_stock}، المطلوب {item.quantity}"
                    )
                product.current_stock = current_stock - item.quantity
                db.add(StockMovement(
                    product_id=item.product_id,
                    movement_type="out",
                    quantity=item.quantity,
                    reference_type="sale",
                    reference_id=sale_id,
                    created_by=current_user.id,
                    created_at=datetime.utcnow(),
                ))
                event_items.append({
                    "productId": item.product_id,
                    "quantity": item.quantity,
                    "unitPrice": float(item.unit_price),
                    "totalPrice": float(item.total_price),
                })

    await db.flush()

    # Step 3: Emit event to Ledger Engine (within the same transaction context)
    customer_name = "Unknown Customer"
    if sale.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == sale.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    await emit_sale_approved(
        invoice_id=sale.id,
        invoice_number=sale.invoice_number or f"INV-{sale.id}",
        customer_id=sale.customer_id or 0,
        customer_name=customer_name,
        total_amount=sale.total_amount,
        tax_amount=sale.tax_amount or 0,
        discount=sale.discount or 0,
        final_amount=sale.final_amount,
        items=event_items,
        user_id=current_user.id,
        company_id=sale.company_id,
    )
    logger.info(f"Sales: emitted invoice.approved event for sale {sale_id}")

    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    return await _build_sale_response(refreshed, items, db)


@router.post("/{sale_id}/reject", response_model=SaleResponse)
async def reject_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted sales can be rejected")

    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="rejected"))
    await db.flush()
    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    return await _build_sale_response(refreshed, items_result.scalars().all(), db)
