import math
import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.sales import Sale, SaleItem, Customer
from app.models.user import User
from app.models.inventory import Product, StockMovement, Warehouse
from app.models.accounting import FiscalPeriod
from app.schemas.sales import SaleCreate, SaleResponse
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.event_emitter import (
    emit_sale_approved, emit_sale_voided, emit_goods_issued, emit_goods_received,
)
from app.models.payments import CustomerPayment
from app.services.settings_service import get_setting
from app.services.numbering_service import generate_next_number
from app.services import workflow_engine

logger = logging.getLogger(__name__)

router = APIRouter()


def _validate_amounts(data: SaleCreate) -> None:
    if data.total_amount < 0 or data.discount < 0 or data.tax_amount < 0 or data.final_amount < 0:
        raise HTTPException(status_code=400, detail="المبالغ لا يمكن أن تكون سالبة")
    if data.discount > data.total_amount + data.tax_amount:
        raise HTTPException(status_code=400, detail="الخصم أكبر من إجمالي المبلغ")
    for item in data.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="الكمية يجب أن تكون أكبر من صفر")
        if item.unit_price < 0:
            raise HTTPException(status_code=400, detail="سعر الوحدة لا يمكن أن يكون سالباً")
        if item.product_id is None:
            raise HTTPException(status_code=400, detail="المنتج مطلوب لكل بند")


async def _validate_fiscal_period(db: AsyncSession, fiscal_period_id) -> None:
    if not fiscal_period_id:
        return
    fp = (await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == fiscal_period_id))).scalar_one_or_none()
    if not fp:
        raise HTTPException(status_code=400, detail="السنة المالية غير موجودة")
    if fp.is_closed or fp.is_locked:
        raise HTTPException(status_code=400, detail="السنة المالية مغلقة أو مؤمنة - لا يمكن إضافة فاتورة عليها")


async def _resolve_fiscal_period_id(db: AsyncSession, when: datetime) -> Optional[int]:
    """Return the narrowest fiscal period covering ``when`` (inclusive of its day)."""
    if when is None:
        return None
    when_date = when.date()
    result = await db.execute(
        select(FiscalPeriod)
        .where(func.date(FiscalPeriod.start_date) <= when_date)
        .where(func.date(FiscalPeriod.end_date) >= when_date)
        .order_by(FiscalPeriod.end_date.asc())
        .limit(1)
    )
    period = result.scalar_one_or_none()
    return period.id if period else None


def _next_invoice_number(db: AsyncSession, sale_id: int, prefix: str = "INV-") -> str:
    prefix = (prefix or "INV-").strip() or "INV-"
    if not prefix.endswith("-"):
        prefix += "-"
    year = datetime.now(UTC).replace(tzinfo=None).year
    if not prefix.endswith(f"{year}-"):
        prefix = f"{prefix}{year}-"
    return f"{prefix}{sale_id:06d}"


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


async def _build_sale_response(sale: Sale, items: list, db: AsyncSession = None) -> dict:
    customer_name = ""
    if sale.customer_id and db:
        cust_result = await db.execute(select(Customer).where(Customer.id == sale.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    paid_amount = 0.0
    if db and sale.customer_id:
        pay_result = await db.execute(
            select(func.coalesce(func.sum(CustomerPayment.amount), 0))
            .where(CustomerPayment.customer_id == sale.customer_id)
        )
        paid_amount = float(pay_result.scalar() or 0)

    product_names = {}
    if db and items:
        product_ids = list({i.product_id for i in items if i.product_id})
        if product_ids:
            prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            for p in prod_result.scalars().all():
                product_names[p.id] = p.name

    return {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_name": customer_name,
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
        "fiscal_period_id": sale.fiscal_period_id,
        "invoice_number": sale.invoice_number,
        "journal_entry_id": sale.journal_entry_id,
        "is_posted_to_ledger": sale.journal_entry_id is not None,
        "isPostedToLedger": sale.journal_entry_id is not None,
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


def _build_sale_response_sync(
    sale: Sale,
    items: list,
    customer_map: dict,
    paid_map: dict,
    product_map: dict,
) -> dict:
    cn = ""
    if sale.customer_id and sale.customer_id in customer_map:
        cn = customer_map[sale.customer_id].name

    paid_amount = paid_map.get(sale.customer_id, 0.0) if sale.customer_id else 0.0

    return {
        "id": sale.id,
        "customer_id": sale.customer_id,
        "customer_name": cn,
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
        "fiscal_period_id": sale.fiscal_period_id,
        "invoice_number": sale.invoice_number,
        "journal_entry_id": sale.journal_entry_id,
        "is_posted_to_ledger": sale.journal_entry_id is not None,
        "isPostedToLedger": sale.journal_entry_id is not None,
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
                "product_name": product_map.get(i.product_id, ""),
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


async def _build_sale_list(sales: list, db: AsyncSession) -> list:
    if not sales:
        return []

    customer_ids = list({s.customer_id for s in sales if s.customer_id})
    sale_ids = [s.id for s in sales]

    # 1) Customers — 1 query
    customer_map = {}
    if customer_ids:
        cr = await db.execute(select(Customer).where(Customer.id.in_(customer_ids)))
        customer_map = {c.id: c for c in cr.scalars().all()}

    # 2) Payments — 1 query
    paid_map = {}
    if customer_ids:
        pr = await db.execute(
            select(CustomerPayment.customer_id, func.coalesce(func.sum(CustomerPayment.amount), 0).label("paid"))
            .where(CustomerPayment.customer_id.in_(customer_ids))
            .group_by(CustomerPayment.customer_id)
        )
        for row in pr:
            paid_map[row[0]] = float(row[1])

    # 3) Items — 1 query
    ir = await db.execute(select(SaleItem).where(SaleItem.sale_id.in_(sale_ids)))
    all_items = ir.scalars().all()
    items_by_sale = {}
    for it in all_items:
        items_by_sale.setdefault(it.sale_id, []).append(it)

    # 4) Products — 1 query
    product_ids = list({i.product_id for i in all_items if i.product_id})
    product_map = {}
    if product_ids:
        pr2 = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p.name for p in pr2.scalars().all()}

    # 5) Build responses — 0 queries
    return [
        _build_sale_response_sync(s, items_by_sale.get(s.id, []), customer_map, paid_map, product_map)
        for s in sales
    ]


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
    sales = list(result.scalars().all())

    items = await _build_sale_list(sales, db)

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
    current_user: User = Depends(require_permission("CREATE_SALE")),
):
    fiscal_period_id = data.fiscal_period_id or await _resolve_fiscal_period_id(
        db, datetime.now(UTC).replace(tzinfo=None)
    )
    await _validate_fiscal_period(db, fiscal_period_id)
    _validate_amounts(data)

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
        fiscal_period_id=fiscal_period_id,
        invoice_number=data.invoice_number,
        tax_amount=data.tax_amount,
        tax_id=data.tax_id,
        notes=data.notes,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(sale)
    await db.flush()

    if not sale.invoice_number:
        sale.invoice_number = await generate_next_number(db, "SALE")

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
    current_user: User = Depends(require_permission("EDIT_SALE")),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    if sale.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot edit a submitted/approved sale")

    fiscal_period_id = data.fiscal_period_id or await _resolve_fiscal_period_id(
        db, sale.created_at or datetime.now(UTC).replace(tzinfo=None)
    )
    await _validate_fiscal_period(db, fiscal_period_id)
    _validate_amounts(data)

    await db.execute(update(Sale).where(Sale.id == sale_id).values(
        customer_id=data.customer_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_method=data.payment_method, payment_status=data.payment_status,
        company_id=data.company_id, branch_id=data.branch_id,
        fiscal_period_id=fiscal_period_id,
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
    current_user: User = Depends(require_permission("DELETE_SALE")),
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
    current_user: User = Depends(require_permission("EDIT_SALE")),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    await workflow_engine.validate_transition(
        db, "SALE", sale.workflow_state, "submitted", user=current_user
    )

    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="submitted"))
    await db.flush()
    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    return await _build_sale_response(refreshed, items_result.scalars().all(), db)


@router.post("/{sale_id}/approve", response_model=SaleResponse)
async def approve_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("APPROVE_SALE")),
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
    await workflow_engine.validate_transition(
        db, "SALE", sale.workflow_state, "approved",
        amount=sale.final_amount, user=current_user,
    )

    # Ensure the fiscal period for the posting is open
    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), sale.fiscal_period_id)

    # Step 1: Update workflow state
    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="approved"))

    # Step 2: Batch-load products, decrement stock, create stock movements
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    items = items_result.scalars().all()

    product_ids = [i.product_id for i in items if i.product_id]
    product_map = {}
    if product_ids:
        prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p for p in prod_result.scalars().all()}

    event_items = []
    issued_movements = []
    for item in items:
        if item.product_id and item.product_id in product_map:
            product = product_map[item.product_id]
            result = await db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .where(Product.current_stock >= item.quantity)
                .values(current_stock=Product.current_stock - item.quantity)
            )
            if result.rowcount == 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"المخزون غير كافٍ للمنتج '{product.name}': المتوفر {product.current_stock}، المطلوب {item.quantity}"
                )
            # COGS is valued at the product's latest landed cost. store it on
            # the stock movement (unit_cost) to keep a per-movement audit trail
            # and post matching COGS journal entries below.
            unit_cost = product.last_purchase_price or product.purchase_price or 0.0
            mv = StockMovement(
                product_id=item.product_id,
                movement_type="out",
                quantity=item.quantity,
                reference_type="sale",
                reference_id=sale_id,
                unit_cost=unit_cost,
                created_by=current_user.id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            db.add(mv)
            issued_movements.append((mv, item, unit_cost))
            event_items.append({
                "productId": item.product_id,
                "quantity": item.quantity,
                "unitPrice": float(item.unit_price),
                "totalPrice": float(item.total_price),
            })

    await db.flush()

    # Step 3a: Emit inventory.goods.issued (COGS) for each movement within
    # this same transaction. The gateway posts Dr. COGS / Cr. Inventory per
    # movement, keyed by stock movement id (referenceId), so both the revenue
    # and the COGS legs of the sale land in the ledger. On void, the same
    # movement ids are used to reverse the COGS entries.
    if issued_movements:
        warehouse_rows = (await db.execute(select(Warehouse))).scalars().all()
        warehouse_map = {w.id: w for w in warehouse_rows}
        for mv, item, unit_cost in issued_movements:
            warehouse = warehouse_map.get(mv.warehouse_id)
            if warehouse is None and warehouse_map:
                warehouse = next(iter(warehouse_map.values()))
            warehouse_id = mv.warehouse_id or (warehouse.id if warehouse else 0)
            warehouse_name = warehouse.name if warehouse else "Main Warehouse"
            await emit_goods_issued(
                transaction_id=mv.id,
                product_id=mv.product_id,
                product_name=product_map[mv.product_id].name,
                warehouse_id=warehouse_id,
                warehouse_name=warehouse_name,
                quantity=item.quantity,
                unit_cost=unit_cost,
                total_cost=float(unit_cost) * (item.quantity or 0),
                customer_id=sale.customer_id,
                sales_order_id=sale.id,
                sales_order_number=sale.invoice_number or f"INV-{sale.id}",
                user_id=current_user.id,
                company_id=sale.company_id,
            )
        logger.info(
            f"Sales: emitted {len(issued_movements)} goods.issued (COGS) events for sale {sale_id}"
        )

    # Step 3: Emit event to Ledger Engine (within the same transaction context)
    customer_name = "Unknown Customer"
    if sale.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == sale.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    event_result = await emit_sale_approved(
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

    # Link the ledger entry created by the Ledger Engine back to the sale.
    # The event emission returns the entry id synchronously; we record the
    # link in this same transaction (the gateway no longer updates `sales`
    # directly to avoid a cross-transaction deadlock).
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(Sale).where(Sale.id == sale_id).values(journal_entry_id=entry_id))
        await db.flush()

    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    return await _build_sale_response(refreshed, items, db)


@router.post("/{sale_id}/reject", response_model=SaleResponse)
async def reject_sale(
    sale_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("EDIT_SALE")),
):
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    await workflow_engine.validate_transition(
        db, "SALE", sale.workflow_state, "rejected",
        reason=None, user=current_user,
    )

    await db.execute(update(Sale).where(Sale.id == sale_id).values(workflow_state="rejected"))
    await db.flush()
    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    return await _build_sale_response(refreshed, items_result.scalars().all(), db)


@router.post("/{sale_id}/void", response_model=dict)
async def void_sale(
    sale_id: int,
    reason: str = "إلغاء فاتورة بيع",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("APPROVE_SALE")),
):
    """
    Void an approved sales invoice.

    Reverses the accounting (sales.invoice.voided -> reversing entry for the
    revenue entry plus every COGS entry posted for this sale's goods issue),
    returns sold goods back into inventory, and marks the invoice voided.
    """
    result = await db.execute(select(Sale).where(Sale.id == sale_id))
    sale = result.scalar_one_or_none()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    await workflow_engine.validate_transition(
        db, "SALE", sale.workflow_state, "voided",
        amount=sale.final_amount, reason=reason, user=current_user,
    )

    # Step 1: Reverse stock (return sold goods back into inventory)
    items_result = await db.execute(select(SaleItem).where(SaleItem.sale_id == sale_id))
    items = items_result.scalars().all()

    product_ids = [i.product_id for i in items if i.product_id]
    product_map = {}
    if product_ids:
        prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p for p in prod_result.scalars().all()}

    for item in items:
        if item.product_id and item.product_id in product_map:
            await db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(current_stock=Product.current_stock + (item.quantity or 0))
            )
            db.add(StockMovement(
                product_id=item.product_id, movement_type="in",
                quantity=item.quantity, reference_type="sale_void",
                reference_id=sale_id, created_by=current_user.id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    await db.flush()

    # The COGS journal entries were keyed by the ORIGINAL goods-issued stock
    # movements (reference_type='sale'). Hand those ids to the gateway so it
    # reverses exactly those posted COGS entries.
    stock_movement_ids = list(
        (await db.execute(
            select(StockMovement.id)
            .where(StockMovement.reference_type == "sale", StockMovement.reference_id == sale_id)
        )).scalars().all()
    )

    # Step 2: Mark voided (within this transaction, so emit failure rolls back)
    await db.execute(update(Sale).where(Sale.id == sale_id).values(
        workflow_state="voided",
        voided_by=current_user.id,
        voided_at=datetime.now(UTC).replace(tzinfo=None),
        void_reason=reason,
    ))
    await db.flush()

    # Step 3: Reverse the accounting entries via the Ledger Engine.
    # The gateway voids the revenue entry (sales.journal_entry_id) and every
    # posted InventoryTransaction/CostOfGoodsSold entry keyed by this sale's
    # original stock-movement ids.
    customer_name = ""
    if sale.customer_id:
        cust_result = await db.execute(select(Customer).where(Customer.id == sale.customer_id))
        customer = cust_result.scalar_one_or_none()
        if customer:
            customer_name = customer.name

    await emit_sale_voided(
        invoice_id=sale.id,
        invoice_number=sale.invoice_number or f"INV-{sale.id}",
        customer_id=sale.customer_id,
        customer_name=customer_name,
        original_entry_id=sale.journal_entry_id,
        stock_movement_ids=stock_movement_ids,
        reason=reason,
        user_id=current_user.id,
        company_id=sale.company_id,
    )
    logger.info(f"Sales: emitted invoice.voided event for sale {sale_id}")

    refreshed = (await db.execute(select(Sale).where(Sale.id == sale_id))).scalar_one()
    return {"id": sale_id, "message": "الفاتورة تم إلغاؤها", "workflow_state": refreshed.workflow_state}
