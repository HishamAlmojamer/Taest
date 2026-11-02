import math
from datetime import UTC, datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.purchases import Purchase, PurchaseItem, Supplier
from app.models.inventory import Product, StockMovement
from app.models.user import User
from app.models.accounting import FiscalPeriod
from app.models.payments import SupplierPayment
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from pydantic import BaseModel
from typing import List
from app.utils.event_emitter import emit_purchase_approved, emit_purchase_voided
from app.services.settings_service import get_setting
from app.services.numbering_service import generate_next_number
from app.services import workflow_engine
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
    fiscal_period_id: Optional[int] = None
    invoice_number: Optional[str] = None
    due_date: Optional[date] = None
    tax_amount: float = 0
    tax_id: Optional[int] = None
    notes: Optional[str] = None
    items: List[PurchaseItemCreate] = []


def _validate_amounts(data: PurchaseCreate) -> None:
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
        raise HTTPException(status_code=400, detail="السنة المالية مغلقة أو مؤمنة - لا يمكن إضافة أمر شراء عليها")


def _next_purchase_number(db: AsyncSession, purchase_id: int, prefix: str = "PO-") -> str:
    prefix = (prefix or "PO-").strip() or "PO-"
    if not prefix.endswith("-"):
        prefix += "-"
    year = datetime.now(UTC).replace(tzinfo=None).year
    if not prefix.endswith(f"{year}-"):
        prefix = f"{prefix}{year}-"
    return f"{prefix}{purchase_id:06d}"


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


async def _build_purchase_response(purchase: Purchase, items: list, db: AsyncSession = None) -> dict:
    supplier_name = ""
    if purchase.supplier_id and db:
        sup_result = await db.execute(select(Supplier).where(Supplier.id == purchase.supplier_id))
        supplier = sup_result.scalar_one_or_none()
        if supplier:
            supplier_name = supplier.name

    paid_amount = 0.0
    if db and purchase.supplier_id:
        pay_result = await db.execute(
            select(func.coalesce(func.sum(SupplierPayment.amount), 0))
            .where(SupplierPayment.supplier_id == purchase.supplier_id)
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
        "id": purchase.id,
        "supplier_id": purchase.supplier_id,
        "supplier_name": supplier_name,
        "supplierName": supplier_name,
        "total_amount": float(purchase.total_amount),
        "total": float(purchase.final_amount),
        "subtotal": float(purchase.total_amount),
        "discount": float(purchase.discount or 0),
        "final_amount": float(purchase.final_amount),
        "payment_status": purchase.payment_status,
        "workflow_state": purchase.workflow_state,
        "status": purchase.workflow_state.upper() if purchase.workflow_state else None,
        "company_id": purchase.company_id,
        "branch_id": purchase.branch_id,
        "fiscal_period_id": purchase.fiscal_period_id,
        "invoice_number": purchase.invoice_number,
        "order_number": purchase.invoice_number,
        "journal_entry_id": purchase.journal_entry_id,
        "is_posted_to_ledger": purchase.journal_entry_id is not None,
        "isPostedToLedger": purchase.journal_entry_id is not None,
        "due_date": purchase.due_date.isoformat() if purchase.due_date else None,
        "tax_amount": float(purchase.tax_amount or 0),
        "tax_id": purchase.tax_id,
        "notes": purchase.notes,
        "created_by": purchase.created_by,
        "date": purchase.created_at.strftime("%Y-%m-%d") if purchase.created_at else None,
        "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        "paid_amount": paid_amount,
        "void_reason": purchase.void_reason,
        "items": [
            {
                "id": i.id, "purchase_id": i.purchase_id, "product_id": i.product_id,
                "product_name": product_names.get(i.product_id, ""),
                "productName": product_names.get(i.product_id, ""),
                "quantity": i.quantity,
                "unit_price": float(i.unit_price),
                "unitPrice": float(i.unit_price),
                "unit_cost": float(i.unit_price),
                "unitCost": float(i.unit_price),
                "total_price": float(i.total_price),
                "totalPrice": float(i.total_price),
                "total": float(i.total_price),
                "discount": 0,
            }
            for i in items
        ],
    }


def _build_purchase_response_sync(
    purchase: Purchase,
    items: list,
    supplier_map: dict,
    paid_map: dict,
    product_map: dict,
) -> dict:
    supplier_name = ""
    if purchase.supplier_id and purchase.supplier_id in supplier_map:
        supplier_name = supplier_map[purchase.supplier_id].name

    paid_amount = paid_map.get(purchase.supplier_id, 0.0) if purchase.supplier_id else 0.0

    return {
        "id": purchase.id,
        "supplier_id": purchase.supplier_id,
        "supplier_name": supplier_name,
        "supplierName": supplier_name,
        "total_amount": float(purchase.total_amount),
        "total": float(purchase.final_amount),
        "subtotal": float(purchase.total_amount),
        "discount": float(purchase.discount or 0),
        "final_amount": float(purchase.final_amount),
        "payment_status": purchase.payment_status,
        "workflow_state": purchase.workflow_state,
        "status": purchase.workflow_state.upper() if purchase.workflow_state else None,
        "company_id": purchase.company_id,
        "branch_id": purchase.branch_id,
        "fiscal_period_id": purchase.fiscal_period_id,
        "invoice_number": purchase.invoice_number,
        "order_number": purchase.invoice_number,
        "journal_entry_id": purchase.journal_entry_id,
        "is_posted_to_ledger": purchase.journal_entry_id is not None,
        "isPostedToLedger": purchase.journal_entry_id is not None,
        "due_date": purchase.due_date.isoformat() if purchase.due_date else None,
        "tax_amount": float(purchase.tax_amount or 0),
        "tax_id": purchase.tax_id,
        "notes": purchase.notes,
        "created_by": purchase.created_by,
        "date": purchase.created_at.strftime("%Y-%m-%d") if purchase.created_at else None,
        "created_at": purchase.created_at.isoformat() if purchase.created_at else None,
        "paid_amount": paid_amount,
        "void_reason": purchase.void_reason,
        "items": [
            {
                "id": i.id, "purchase_id": i.purchase_id, "product_id": i.product_id,
                "product_name": product_map.get(i.product_id, ""),
                "productName": product_map.get(i.product_id, ""),
                "quantity": i.quantity,
                "unit_price": float(i.unit_price),
                "unitPrice": float(i.unit_price),
                "unit_cost": float(i.unit_price),
                "unitCost": float(i.unit_price),
                "total_price": float(i.total_price),
                "totalPrice": float(i.total_price),
                "total": float(i.total_price),
                "discount": 0,
            }
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
        like = f"%{search}%"
        query = query.where(
            (Purchase.invoice_number.ilike(like))
            | (Purchase.id.cast(func.text("VARCHAR")).ilike(like))
        )
        count_query = count_query.where(
            (Purchase.invoice_number.ilike(like))
            | (Purchase.id.cast(func.text("VARCHAR")).ilike(like))
        )
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
        supplier_ids = list({p.supplier_id for p in purchases if p.supplier_id})

        items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id.in_(purchase_ids)))
        all_items = items_result.scalars().all()
        items_by_purchase = {}
        for it in all_items:
            items_by_purchase.setdefault(it.purchase_id, []).append(it)

        supplier_map = {}
        if supplier_ids:
            sup_result = await db.execute(select(Supplier).where(Supplier.id.in_(supplier_ids)))
            supplier_map = {s.id: s for s in sup_result.scalars().all()}

        product_ids = list({i.product_id for it in all_items for i in [it] if i.product_id})
        product_map = {}
        if product_ids:
            prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
            product_map = {p.id: p.name for p in prod_result.scalars().all()}

        paid_map = {}
        if supplier_ids:
            pay_result = await db.execute(
                select(SupplierPayment.supplier_id, func.coalesce(func.sum(SupplierPayment.amount), 0))
                .where(SupplierPayment.supplier_id.in_(supplier_ids))
                .group_by(SupplierPayment.supplier_id)
            )
            for sid, amt in pay_result.all():
                paid_map[sid] = float(amt)

        for p in purchases:
            items.append(_build_purchase_response_sync(
                p, items_by_purchase.get(p.id, []), supplier_map, paid_map, product_map,
            ))

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
    return await _build_purchase_response(purchase, items_result.scalars().all(), db)


@router.post("", response_model=dict)
async def create_purchase(data: PurchaseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_PURCHASE"))):
    await _validate_fiscal_period(db, data.fiscal_period_id)
    _validate_amounts(data)
    if data.supplier_id is None:
        raise HTTPException(status_code=400, detail="المورد مطلوب")
    if not data.items:
        raise HTTPException(status_code=400, detail="يجب إضافة بند واحد على الأقل")

    supplier = (await db.execute(select(Supplier).where(Supplier.id == data.supplier_id))).scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=400, detail="المورد غير موجود")

    purchase = Purchase(
        supplier_id=data.supplier_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_status=data.payment_status, workflow_state="draft",
        company_id=data.company_id, branch_id=data.branch_id,
        fiscal_period_id=data.fiscal_period_id,
        invoice_number=data.invoice_number, tax_amount=data.tax_amount,
        tax_id=data.tax_id, notes=data.notes, due_date=data.due_date,
        created_by=current_user.id, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(purchase)
    await db.flush()

    if not purchase.invoice_number:
        purchase.invoice_number = await generate_next_number(db, "PURCHASE")

    for item in data.items:
        db.add(PurchaseItem(
            purchase_id=purchase.id, product_id=item.product_id,
            quantity=item.quantity, unit_price=item.unit_price, total_price=item.total_price,
        ))
    await db.flush()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase.id))
    return await _build_purchase_response(purchase, items_result.scalars().all(), db)


@router.put("/{purchase_id}", response_model=dict)
async def update_purchase(purchase_id: int, data: PurchaseCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_PURCHASE"))):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot edit a submitted/approved purchase")

    await _validate_fiscal_period(db, data.fiscal_period_id)
    _validate_amounts(data)

    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(
        supplier_id=data.supplier_id, total_amount=data.total_amount,
        discount=data.discount, final_amount=data.final_amount,
        payment_status=data.payment_status, company_id=data.company_id,
        branch_id=data.branch_id, fiscal_period_id=data.fiscal_period_id,
        invoice_number=data.invoice_number, due_date=data.due_date,
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
    return await _build_purchase_response(refreshed, items_result.scalars().all(), db)


@router.delete("/{purchase_id}", response_model=MessageResponse)
async def delete_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("DELETE_PURCHASE"))):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    if purchase.workflow_state not in ("draft", "rejected", "voided"):
        raise HTTPException(status_code=400, detail="Cannot delete a submitted/approved purchase")
    await db.execute(delete(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    await db.execute(delete(Purchase).where(Purchase.id == purchase_id))
    return MessageResponse(message="Purchase deleted")


@router.post("/{purchase_id}/submit", response_model=dict)
async def submit_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_PURCHASE"))):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    await workflow_engine.validate_transition(
        db, "PURCHASE", purchase.workflow_state, "submitted", user=current_user
    )
    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(workflow_state="submitted"))
    await db.flush()
    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return await _build_purchase_response(refreshed, items_result.scalars().all(), db)


@router.post("/{purchase_id}/approve", response_model=dict)
async def approve_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("APPROVE_PURCHASE"))):
    """
    Approve a purchase order.

    Accounting Logic (per ERP_INSTRUCTIONS.md):
      1. Updates workflow_state to 'approved'
      2. Increases product stock and creates stock movements (goods received)
      3. Emits 'purchase.order.approved' event to the Ledger Engine
      4. Ledger Engine creates a balanced journal entry:
         Dr. Inventory (1301)     totalAmount
         Dr. VAT Input (1400)     taxAmount
         Cr. Accounts Payable (2111) finalAmount
      5. Links the created journal entry and increases the supplier balance
    """
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    await workflow_engine.validate_transition(
        db, "PURCHASE", purchase.workflow_state, "approved",
        amount=purchase.final_amount, user=current_user,
    )
    if purchase.journal_entry_id:
        raise HTTPException(status_code=400, detail="Purchase already has an accounting entry")

    # Ensure the fiscal period for the posting is open
    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), purchase.fiscal_period_id)

    # Step 1: Update workflow state
    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(workflow_state="approved"))

    # Step 2: Batch-load products, increase stock, create stock movements
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    items = items_result.scalars().all()

    product_ids = [i.product_id for i in items if i.product_id]
    product_map = {}
    if product_ids:
        prod_result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p for p in prod_result.scalars().all()}

    event_items = []
    for item in items:
        if item.product_id and item.product_id in product_map:
            await db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(current_stock=Product.current_stock + item.quantity)
            )
            db.add(StockMovement(
                product_id=item.product_id, movement_type="in",
                quantity=item.quantity, reference_type="purchase",
                reference_id=purchase_id, created_by=current_user.id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
            event_items.append({
                "productId": item.product_id,
                "quantity": item.quantity,
                "unitPrice": float(item.unit_price),
                "totalPrice": float(item.total_price),
            })

    await db.flush()

    # Step 3: Emit event to Ledger Engine (within the same transaction context)
    supplier_name = "Unknown Supplier"
    if purchase.supplier_id:
        sup_result = await db.execute(select(Supplier).where(Supplier.id == purchase.supplier_id))
        supplier = sup_result.scalar_one_or_none()
        if supplier:
            supplier_name = supplier.name

    event_result = await emit_purchase_approved(
        purchase_order_id=purchase.id,
        purchase_order_number=purchase.invoice_number or f"PO-{purchase.id}",
        supplier_id=purchase.supplier_id or 0,
        supplier_name=supplier_name,
        total_amount=purchase.total_amount,
        tax_amount=purchase.tax_amount or 0,
        discount=purchase.discount or 0,
        final_amount=purchase.final_amount,
        items=event_items,
        user_id=current_user.id,
        company_id=purchase.company_id,
    )
    logger.info(f"Purchases: emitted purchase.order.approved event for purchase {purchase_id}")

    # Step 4: Link the ledger entry created by the Ledger Engine back to the
    # purchase. The gateway returns the entry id synchronously; we record the
    # link in this same transaction (no direct gateway write to `purchases`).
    entry_id = _extract_entry_id_from_event(event_result)
    if entry_id:
        await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(journal_entry_id=entry_id))
        await db.flush()

    # Step 5: Increase supplier balance (we now owe the supplier)
    if purchase.supplier_id:
        sup_result = await db.execute(select(Supplier).where(Supplier.id == purchase.supplier_id))
        supplier = sup_result.scalar_one_or_none()
        if supplier:
            new_balance = (supplier.current_balance or 0) + purchase.final_amount
            await db.execute(
                update(Supplier).where(Supplier.id == purchase.supplier_id).values(current_balance=new_balance)
            )

    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return await _build_purchase_response(refreshed, items_result.scalars().all(), db)


@router.post("/{purchase_id}/reject", response_model=dict)
async def reject_purchase(purchase_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_PURCHASE"))):
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    await workflow_engine.validate_transition(
        db, "PURCHASE", purchase.workflow_state, "rejected",
        reason=None, user=current_user,
    )

    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(workflow_state="rejected"))
    await db.flush()
    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return await _build_purchase_response(refreshed, items_result.scalars().all(), db)


@router.post("/{purchase_id}/void", response_model=dict)
async def void_purchase(
    purchase_id: int,
    reason: str = "إلغاء أمر الشراء",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("APPROVE_PURCHASE")),
):
    """
    Void an approved purchase order.

    Reverses the accounting entry (purchase.order.voided -> reversing entry),
    returns received stock back out of inventory, and marks the order voided.
    """
    result = await db.execute(select(Purchase).where(Purchase.id == purchase_id))
    purchase = result.scalar_one_or_none()
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase not found")
    await workflow_engine.validate_transition(
        db, "PURCHASE", purchase.workflow_state, "voided",
        amount=purchase.final_amount, reason=reason, user=current_user,
    )

    # Step 1: Reverse stock (return received goods out of inventory)
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
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
                .where(Product.current_stock >= item.quantity)
                .values(current_stock=Product.current_stock - item.quantity)
            )
            db.add(StockMovement(
                product_id=item.product_id, movement_type="out",
                quantity=item.quantity, reference_type="purchase_void",
                reference_id=purchase_id, created_by=current_user.id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))

    # Step 2: Mark voided (within this transaction, so emit failure rolls back)
    await db.execute(update(Purchase).where(Purchase.id == purchase_id).values(
        workflow_state="voided",
        voided_by=current_user.id,
        voided_at=datetime.now(UTC).replace(tzinfo=None),
        void_reason=reason,
    ))
    await db.flush()

    # Step 3: Reverse the accounting entry via the Ledger Engine
    await emit_purchase_voided(
        purchase_order_id=purchase.id,
        purchase_order_number=purchase.invoice_number or f"PO-{purchase.id}",
        original_entry_id=purchase.journal_entry_id,
        reason=reason,
        user_id=current_user.id,
        company_id=purchase.company_id,
    )
    logger.info(f"Purchases: emitted purchase.order.voided event for purchase {purchase_id}")

    # Step 4: Reduce supplier balance (we no longer owe the supplier)
    if purchase.supplier_id:
        sup_result = await db.execute(select(Supplier).where(Supplier.id == purchase.supplier_id))
        supplier = sup_result.scalar_one_or_none()
        if supplier:
            new_balance = max((supplier.current_balance or 0) - purchase.final_amount, 0)
            await db.execute(
                update(Supplier).where(Supplier.id == purchase.supplier_id).values(current_balance=new_balance)
            )

    refreshed = (await db.execute(select(Purchase).where(Purchase.id == purchase_id))).scalar_one()
    items_result = await db.execute(select(PurchaseItem).where(PurchaseItem.purchase_id == purchase_id))
    return await _build_purchase_response(refreshed, items_result.scalars().all(), db)
