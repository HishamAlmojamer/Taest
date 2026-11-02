import math
import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.inventory import (
    Product, Category, Warehouse, StockMovement,
    StockTransfer, StockTransferItem, ProductWarehouse, InventoryBatch,
)
from app.models.user import User
from app.schemas.inventory import ProductCreate, ProductResponse, CategoryCreate, CategoryResponse
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.validation import require_fields, parse_date_value
from app.utils.event_emitter import emit_goods_received
from app.services.cache import cache_get, cache_set, cache_invalidate

logger = logging.getLogger(__name__)

router = APIRouter()


def _extract_entry_id_from_event(event_result) -> Optional[int]:
    """Extract the first journal entry id from a gateway emit response."""
    try:
        results = (event_result.get("data") or {}).get("results") or []
        for r in results:
            if isinstance(r, dict) and r.get("entryId"):
                return int(r["entryId"])
    except Exception:
        pass
    return None


# ── Categories ────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cached = await cache_get("list_categories", all="active")
    if cached is not None:
        return cached

    result = await db.execute(select(Category).where(Category.is_active == True).order_by(Category.name))
    items = [{"id": c.id, "code": c.code, "name": c.name, "name_en": c.name_en,
             "parent_id": c.parent_id, "description": c.description, "is_active": c.is_active,
             "productCount": 0}
            for c in result.scalars().all()]
    resp = {"items": items, "total": len(items)}
    await cache_set("list_categories", resp, ttl=600, all="active")
    return resp


@router.post("/categories", response_model=dict)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    cat = Category(code=data.code, name=data.name, name_en=data.name_en,
                   parent_id=data.parent_id, description=data.description, created_at=datetime.now(UTC).replace(tzinfo=None))
    db.add(cat)
    await db.flush()
    await cache_invalidate("list_categories")
    return {"id": cat.id, "name": cat.name, "message": "Category created"}


@router.put("/categories/{cat_id}", response_model=dict)
async def update_category(cat_id: int, data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.execute(update(Category).where(Category.id == cat_id).values(
        code=data.code, name=data.name, name_en=data.name_en,
        parent_id=data.parent_id, description=data.description,
    ))
    await cache_invalidate("list_categories")
    return {"message": "Category updated"}


@router.delete("/categories/{cat_id}", response_model=MessageResponse)
async def delete_category(cat_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Category not found")
    await db.execute(update(Category).where(Category.id == cat_id).values(is_active=False))
    await cache_invalidate("list_categories")
    return MessageResponse(message="Category deleted")


# ── Warehouses ────────────────────────────────────────────────

@router.get("/warehouses")
async def list_warehouses(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Warehouse).where(Warehouse.is_active.is_(True)).order_by(Warehouse.name))
    items = [{"id": w.id, "code": w.code, "name": w.name, "name_en": w.name_en,
             "warehouse_type": w.warehouse_type, "company_id": w.company_id,
             "address": w.address, "city": w.city, "phone": w.phone,
             "manager": w.manager_name, "manager_name": w.manager_name,
             "productCount": 0, "is_active": w.is_active}
            for w in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/warehouses", response_model=dict)
async def create_warehouse(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    wh = Warehouse(
        code=data.get("code", ""), name=data.get("name", ""),
        name_en=data.get("name_en"), warehouse_type=data.get("warehouse_type", "main"),
        company_id=data.get("company_id", 1), address=data.get("address"),
        city=data.get("city"), phone=data.get("phone"),
        manager_name=data.get("manager_name"), manager_phone=data.get("manager_phone"),
    )
    db.add(wh)
    await db.flush()
    return {"id": wh.id, "message": "Warehouse created"}


@router.put("/warehouses/{warehouse_id}", response_model=dict)
async def update_warehouse(warehouse_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Warehouse not found")
    allowed = ['code', 'name', 'name_en', 'warehouse_type', 'company_id', 'address', 'city', 'phone', 'manager_name', 'manager_phone']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Warehouse).where(Warehouse.id == warehouse_id).values(**values))
    return {"message": "Warehouse updated"}


@router.delete("/warehouses/{warehouse_id}", response_model=MessageResponse)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Warehouse not found")
    await db.execute(update(Warehouse).where(Warehouse.id == warehouse_id).values(is_active=False))
    return MessageResponse(message="Warehouse deleted")


# ── Products ──────────────────────────────────────────────────

@router.get("/products", response_model=PaginationResponse)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Product)
    count_query = select(func.count(Product.id))

    if search:
        q = Product.name.ilike(f"%{search}%") | Product.code.ilike(f"%{search}%") | Product.barcode.ilike(f"%{search}%")
        query = query.where(q)
        count_query = count_query.where(q)
    if category_id:
        query = query.where(Product.category_id == category_id)
        count_query = count_query.where(Product.category_id == category_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Product.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[ProductResponse.model_validate(p).model_dump() for p in products],
    )


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse.model_validate(product)


def _blank_to_none(value):
    """Optional text columns must stay NULL, never ''. Empty strings collide
    with UNIQUE constraints (e.g. products.barcode) and silently break inserts."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return value


def _product_integrity_message(exc: IntegrityError) -> str:
    detail = str(getattr(exc, "orig", exc)).lower()
    if "barcode" in detail:
        return "الباركود مستخدم من قبل منتج آخر"
    if "category" in detail:
        return "التصنيف المحدد غير موجود"
    if "company" in detail:
        return "الشركة المحددة غير موجودة"
    if "unit" in detail:
        return "وحدة القياس المحددة غير موجودة"
    return "تعارض في البيانات: تعذّر حفظ المنتج بالبيانات الحالية"


def _validate_product_payload(data: ProductCreate) -> tuple[str, Optional[str], Optional[str]]:
    name = (data.name or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="اسم المنتج مطلوب")
    if not (data.unit or "").strip():
        raise HTTPException(status_code=422, detail="وحدة القياس مطلوبة")
    if float(data.purchase_price or 0) < 0 or float(data.selling_price or 0) < 0:
        raise HTTPException(status_code=422, detail="أسعار المنتج لا يمكن أن تكون سالبة")
    return name, _blank_to_none(data.code), _blank_to_none(data.barcode)


@router.post("/products", response_model=dict)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    name, code, barcode = _validate_product_payload(data)
    if barcode:
        duplicate = await db.execute(select(Product.id).where(Product.barcode == barcode))
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="الباركود مستخدم من قبل منتج آخر")
    product = Product(
        code=code, name=name, name_en=_blank_to_none(data.name_en), barcode=barcode,
        category_id=data.category_id, unit_id=data.unit_id, currency_id=data.currency_id, unit=(data.unit or "").strip(),
        purchase_price=data.purchase_price, selling_price=data.selling_price,
        current_stock=data.current_stock, min_stock=data.min_stock,
        max_stock=data.max_stock, reorder_point=data.reorder_point,
        location=_blank_to_none(data.location), valuation_method=data.valuation_method,
        weight=data.weight, tax_percent=data.tax_percent, brand=_blank_to_none(data.brand),
        description=_blank_to_none(data.description),
        company_id=data.company_id, is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None), updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(product)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=_product_integrity_message(exc)) from exc
    return {"id": product.id, "message": "Product created"}


@router.put("/products/{product_id}", response_model=dict)
async def update_product(product_id: int, data: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")
    name, code, barcode = _validate_product_payload(data)
    if barcode:
        duplicate = await db.execute(select(Product.id).where(Product.barcode == barcode, Product.id != product_id))
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="الباركود مستخدم من قبل منتج آخر")
    try:
        await db.execute(update(Product).where(Product.id == product_id).values(
            code=code, name=name, name_en=_blank_to_none(data.name_en), barcode=barcode,
            category_id=data.category_id, unit_id=data.unit_id, currency_id=data.currency_id, unit=(data.unit or "").strip(),
            purchase_price=data.purchase_price, selling_price=data.selling_price,
            min_stock=data.min_stock, max_stock=data.max_stock, reorder_point=data.reorder_point,
            location=_blank_to_none(data.location), valuation_method=data.valuation_method,
            weight=data.weight, tax_percent=data.tax_percent, brand=_blank_to_none(data.brand),
            description=_blank_to_none(data.description),
            company_id=data.company_id, updated_at=datetime.now(UTC).replace(tzinfo=None),
        ))
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail=_product_integrity_message(exc)) from exc
    return {"message": "Product updated"}


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")
    await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))
    return MessageResponse(message="Product deleted")


# ── Stock Movements ───────────────────────────────────────────

@router.get("/stock-movements")
async def list_stock_movements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            StockMovement,
            Product.name.label("product_name"),
            Warehouse.name.label("warehouse_name"),
        )
        .outerjoin(Product, Product.id == StockMovement.product_id)
        .outerjoin(Warehouse, Warehouse.id == StockMovement.warehouse_id)
    )
    count_query = (
        select(func.count(StockMovement.id))
        .select_from(StockMovement)
        .outerjoin(Product, Product.id == StockMovement.product_id)
    )
    if search:
        q = Product.name.ilike(f"%{search}%")
        query = query.where(q)
        count_query = count_query.where(q)
    if product_id:
        query = query.where(StockMovement.product_id == product_id)
        count_query = count_query.where(StockMovement.product_id == product_id)
    if warehouse_id:
        query = query.where(StockMovement.warehouse_id == warehouse_id)
        count_query = count_query.where(StockMovement.warehouse_id == warehouse_id)
    if movement_type:
        query = query.where(StockMovement.movement_type == movement_type)
        count_query = count_query.where(StockMovement.movement_type == movement_type)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(StockMovement.id.desc()).offset(offset).limit(per_page)
    rows = (await db.execute(query)).all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": m.id, "movement_number": m.movement_number,
                "product_id": m.product_id, "product_name": product_name,
                "warehouse_id": m.warehouse_id, "warehouse_name": warehouse_name,
                "movement_type": m.movement_type,
                "quantity": m.quantity, "unit_cost": m.unit_cost,
                "reference_type": m.reference_type, "reference_id": m.reference_id,
                "notes": m.notes, "created_by": m.created_by,
                "created_at": m.created_at.isoformat() if m.created_at else None}
               for m, product_name, warehouse_name in rows],
    )


_MOVEMENT_ALIASES = {
    "in": "in", "stock_in": "in", "receipt": "in", "received": "in",
    "out": "out", "stock_out": "out", "issue": "out", "issued": "out",
    "adjustment": "adjustment", "adjust": "adjustment",
    "correction": "adjustment", "count": "adjustment",
}


@router.post("/stock-movements", response_model=dict)
async def create_stock_movement(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    """
    Record a stock movement and update the product's on-hand quantity.

      in         -> add `quantity` units (cost = unit_cost or product.purchase_price).
                    Emits inventory.goods.received so the Ledger Engine books
                    Dr Inventory (1210) / Cr GRNI (1230).
      out        -> remove `quantity` units (rejected when stock is insufficient).
      adjustment -> `quantity` is the real counted quantity; the difference
                    against the current balance is recorded.
    """
    raw_type = str(data.get("movement_type") or data.get("type") or "in").strip().lower()
    movement_type = _MOVEMENT_ALIASES.get(raw_type)
    if not movement_type:
        raise HTTPException(status_code=422, detail="نوع الحركة غير صالح")

    product_id = data.get("product_id")
    if not product_id:
        raise HTTPException(status_code=422, detail="product_id مطلوب")

    product = (await db.execute(select(Product).where(Product.id == product_id))).scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        quantity = int(round(float(data.get("quantity"))))
    except (TypeError, ValueError):
        raise HTTPException(status_code=422, detail="الكمية غير صالحة")
    if movement_type == "adjustment":
        if quantity < 0:
            raise HTTPException(status_code=422, detail="الكمية الفعلية لا يمكن أن تكون سالبة")
    elif quantity <= 0:
        raise HTTPException(status_code=422, detail="الكمية يجب أن تكون أكبر من صفر")

    current_stock = int(product.current_stock or 0)
    if movement_type == "out" and quantity > current_stock:
        raise HTTPException(status_code=400, detail=f"الكمية المتاحة غير كافية (المتاح: {current_stock})")

    if movement_type == "adjustment":
        delta = quantity - current_stock
        if delta == 0:
            raise HTTPException(status_code=400, detail="الكمية الفعلية تساوي الرصيد الحالي، لا يوجد فرق للتسوية")
        stored_quantity = abs(delta)
    else:
        delta = quantity if movement_type == "in" else -quantity
        stored_quantity = quantity

    if data.get("unit_cost") not in (None, ""):
        try:
            unit_cost = float(data["unit_cost"])
        except (TypeError, ValueError):
            raise HTTPException(status_code=422, detail="تكلفة الوحدة غير صالحة")
    else:
        unit_cost = float(product.purchase_price or product.last_purchase_price or 0)

    movement = StockMovement(
        movement_number=data.get("movement_number") or f"MOV-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:-3]}",
        product_id=product_id,
        warehouse_id=data.get("warehouse_id"),
        batch_id=data.get("batch_id"),
        movement_type=movement_type,
        quantity=stored_quantity,
        unit_cost=unit_cost,
        quantity_received=stored_quantity if delta > 0 else None,
        quantity_issued=stored_quantity if delta < 0 else None,
        reference_type=data.get("reference_type"),
        reference_id=data.get("reference_id"),
        notes=data.get("notes"),
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(movement)
    await db.flush()

    new_stock = current_stock + delta
    await db.execute(
        update(Product).where(Product.id == product_id).values(current_stock=new_stock)
    )

    if movement_type == "in":
        warehouse_name = "Default Warehouse"
        if movement.warehouse_id:
            warehouse = (await db.execute(
                select(Warehouse).where(Warehouse.id == movement.warehouse_id)
            )).scalar_one_or_none()
            if warehouse:
                warehouse_name = warehouse.name

        event_result = await emit_goods_received(
            transaction_id=movement.id,
            product_id=product_id,
            product_name=product.name,
            warehouse_id=movement.warehouse_id or 0,
            warehouse_name=warehouse_name,
            quantity=stored_quantity,
            unit_cost=unit_cost,
            total_cost=unit_cost * stored_quantity,
            user_id=current_user.id,
            company_id=product.company_id,
        )
        entry_id = _extract_entry_id_from_event(event_result)
        if entry_id:
            logger.info(f"Inventory: emitted goods.received for movement {movement.id} (entry {entry_id})")

    await db.flush()
    return {"id": movement.id, "message": "Stock movement created", "current_stock": new_stock}


# ── Stock Transfers ───────────────────────────────────────────

@router.get("/transfers")
async def list_transfers(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count_query = select(func.count(StockTransfer.id))
    total = (await db.execute(count_query)).scalar() or 0
    query = select(StockTransfer).order_by(StockTransfer.id.desc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    transfers = result.scalars().all()
    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": t.id, "transfer_number": t.transfer_number,
                "from_warehouse_id": t.from_warehouse_id, "to_warehouse_id": t.to_warehouse_id,
                "transfer_date": t.transfer_date, "status": t.status, "notes": t.notes}
               for t in transfers],
    )


@router.post("/transfers", response_model=dict)
async def create_transfer(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    """Create a stock transfer, validating dates/ids up front so a malformed
    body returns 422 instead of a DataError/IntegrityError 500."""
    require_fields(data, ["from_warehouse_id", "to_warehouse_id", "transfer_date"])
    items = data.get("items") or []
    require_fields(data, ["items"])
    if not isinstance(items, list) or not items:
        raise HTTPException(status_code=422, detail="items must be a non-empty list")
    for idx, item in enumerate(items):
        if not isinstance(item, dict) or not item:
            raise HTTPException(status_code=422, detail=f"items[{idx}] must be a non-empty object")
        require_fields(item, ["product_id", "quantity"])
        if (await db.execute(select(Product.id).where(Product.id == item["product_id"]))).scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Product not found")
        if item.get("batch_id") is not None and (await db.execute(
            select(InventoryBatch.id).where(InventoryBatch.id == item["batch_id"])
        )).scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Inventory batch not found")
    for field in ("from_warehouse_id", "to_warehouse_id"):
        if (await db.execute(select(Warehouse.id).where(Warehouse.id == data[field]))).scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="Warehouse not found")
    transfer = StockTransfer(
        transfer_number=data.get("transfer_number") or f"TRF-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        from_warehouse_id=data["from_warehouse_id"],
        to_warehouse_id=data["to_warehouse_id"],
        transfer_date=parse_date_value(data.get("transfer_date"), "transfer_date"),
        status=data.get("status", "draft"),
        notes=data.get("notes"),
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(transfer)
    await db.flush()
    for item_data in items:
        db.add(StockTransferItem(
            transfer_id=transfer.id, product_id=item_data.get("product_id"),
            quantity=item_data.get("quantity", 0), unit_cost=item_data.get("unit_cost"),
            batch_id=item_data.get("batch_id"), notes=item_data.get("notes"),
        ))
    await db.flush()
    return {"id": transfer.id, "message": "Transfer created"}


@router.post("/transfers/{transfer_id}/complete", response_model=dict)
async def complete_transfer(transfer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    result = await db.execute(select(StockTransfer).where(StockTransfer.id == transfer_id))
    transfer = result.scalar_one_or_none()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer not found")
    if transfer.status != "draft":
        raise HTTPException(status_code=400, detail="Transfer is not in draft status")

    items_result = await db.execute(select(StockTransferItem).where(StockTransferItem.transfer_id == transfer_id))
    items = items_result.scalars().all()

    for item in items:
        if item.product_id:
            await db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(current_stock=Product.current_stock - item.quantity)
            )
            await db.execute(
                update(Product)
                .where(Product.id == item.product_id)
                .values(current_stock=Product.current_stock + item.quantity)
            )

    transfer.status = "completed"
    await db.flush()
    return {"message": "Transfer completed"}


# ── Product Warehouse Stock ───────────────────────────────────

@router.get("/product-warehouse")
async def list_product_warehouse_stock(
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(ProductWarehouse)
    if product_id:
        query = query.where(ProductWarehouse.product_id == product_id)
    if warehouse_id:
        query = query.where(ProductWarehouse.warehouse_id == warehouse_id)
    result = await db.execute(query.limit(500))
    items = [{
        "id": pw.id,
        "product_id": pw.product_id,
        "warehouse_id": pw.warehouse_id,
        "quantity": pw.quantity or 0,
        "reserved_quantity": 0,
        "available_quantity": pw.quantity or 0,
        "location": pw.location,
        "bin_number": None,
    } for pw in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/product-warehouse", response_model=dict)
async def update_product_warehouse_stock(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_INVENTORY"))):
    require_fields(data, ["product_id", "warehouse_id"])
    product_id = data["product_id"]
    warehouse_id = data["warehouse_id"]
    quantity = data.get("quantity", 0)

    if (await db.execute(select(Product.id).where(Product.id == product_id))).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if (await db.execute(select(Warehouse.id).where(Warehouse.id == warehouse_id))).scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Warehouse not found")

    result = await db.execute(
        select(ProductWarehouse).where(
            ProductWarehouse.product_id == product_id,
            ProductWarehouse.warehouse_id == warehouse_id,
        )
    )
    pw = result.scalar_one_or_none()

    if pw:
        pw.quantity = quantity
        pw.location = data.get("location", pw.location)
    else:
        pw = ProductWarehouse(
            product_id=product_id,
            warehouse_id=warehouse_id,
            quantity=quantity,
            location=data.get("location"),
        )
        db.add(pw)

    await db.flush()
    return {"message": "Product warehouse stock updated"}
