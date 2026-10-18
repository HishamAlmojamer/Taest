import math
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.inventory import (
    Product, Category, Warehouse, StockMovement,
    StockTransfer, StockTransferItem, ProductWarehouse,
)
from app.models.user import User
from app.schemas.inventory import ProductCreate, ProductResponse, CategoryCreate, CategoryResponse
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user
from app.utils.event_emitter import emit_goods_received

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Categories ────────────────────────────────────────────────

@router.get("/categories")
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Category).where(Category.is_active == True).order_by(Category.name))
    items = [{"id": c.id, "code": c.code, "name": c.name, "name_en": c.name_en,
             "parent_id": c.parent_id, "description": c.description, "is_active": c.is_active,
             "productCount": 0}
            for c in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/categories", response_model=dict)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cat = Category(code=data.code, name=data.name, name_en=data.name_en,
                   parent_id=data.parent_id, description=data.description, created_at=datetime.utcnow())
    db.add(cat)
    await db.flush()
    return {"id": cat.id, "name": cat.name, "message": "Category created"}


@router.put("/categories/{cat_id}", response_model=dict)
async def update_category(cat_id: int, data: CategoryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Category).where(Category.id == cat_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await db.execute(update(Category).where(Category.id == cat_id).values(
        code=data.code, name=data.name, name_en=data.name_en,
        parent_id=data.parent_id, description=data.description,
    ))
    return {"message": "Category updated"}


@router.delete("/categories/{cat_id}", response_model=MessageResponse)
async def delete_category(cat_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(update(Category).where(Category.id == cat_id).values(is_active=False))
    return MessageResponse(message="Category deleted")


# ── Warehouses ────────────────────────────────────────────────

@router.get("/warehouses")
async def list_warehouses(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Warehouse).where(Warehouse.is_active == 1).order_by(Warehouse.name))
    items = [{"id": w.id, "code": w.code, "name": w.name, "name_en": w.name_en,
             "warehouse_type": w.warehouse_type, "company_id": w.company_id,
             "address": w.address, "city": w.city, "phone": w.phone,
             "manager": w.manager_name, "manager_name": w.manager_name,
             "productCount": 0, "is_active": w.is_active}
            for w in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/warehouses", response_model=dict)
async def create_warehouse(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    wh = Warehouse(
        code=data.get("code", ""), name=data.get("name", ""),
        name_en=data.get("name_en"), warehouse_type=data.get("warehouse_type", "main"),
        company_id=data.get("company_id", 1), address=data.get("address"),
        city=data.get("city"), phone=data.get("phone"),
        manager_name=data.get("manager_name"), manager_phone=data.get("manager_phone"),
        created_at=datetime.utcnow(),
    )
    db.add(wh)
    await db.flush()
    return {"id": wh.id, "message": "Warehouse created"}


@router.put("/warehouses/{warehouse_id}", response_model=dict)
async def update_warehouse(warehouse_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Warehouse).where(Warehouse.id == warehouse_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Warehouse not found")
    allowed = ['code', 'name', 'name_en', 'warehouse_type', 'company_id', 'address', 'city', 'phone', 'manager_name', 'manager_phone']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Warehouse).where(Warehouse.id == warehouse_id).values(**values))
    return {"message": "Warehouse updated"}


@router.delete("/warehouses/{warehouse_id}", response_model=MessageResponse)
async def delete_warehouse(warehouse_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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


@router.post("/products", response_model=dict)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    product = Product(
        code=data.code, name=data.name, name_en=data.name_en, barcode=data.barcode,
        category_id=data.category_id, unit_id=data.unit_id, unit=data.unit,
        purchase_price=data.purchase_price, selling_price=data.selling_price,
        current_stock=data.current_stock, min_stock=data.min_stock,
        max_stock=data.max_stock, reorder_point=data.reorder_point,
        location=data.location, valuation_method=data.valuation_method,
        weight=data.weight, tax_percent=data.tax_percent, brand=data.brand,
        description=data.description,
        company_id=data.company_id, created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(product)
    await db.flush()
    return {"id": product.id, "message": "Product created"}


@router.put("/products/{product_id}", response_model=dict)
async def update_product(product_id: int, data: ProductCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Product).where(Product.id == product_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Product not found")
    await db.execute(update(Product).where(Product.id == product_id).values(
        code=data.code, name=data.name, name_en=data.name_en, barcode=data.barcode,
        category_id=data.category_id, unit_id=data.unit_id, unit=data.unit,
        purchase_price=data.purchase_price, selling_price=data.selling_price,
        min_stock=data.min_stock, max_stock=data.max_stock, reorder_point=data.reorder_point,
        location=data.location, valuation_method=data.valuation_method,
        weight=data.weight, tax_percent=data.tax_percent, brand=data.brand,
        description=data.description,
        company_id=data.company_id, updated_at=datetime.utcnow(),
    ))
    return {"message": "Product updated"}


@router.delete("/products/{product_id}", response_model=MessageResponse)
async def delete_product(product_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))
    return MessageResponse(message="Product deleted")


# ── Stock Movements ───────────────────────────────────────────

@router.get("/stock-movements")
async def list_stock_movements(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    product_id: Optional[int] = None,
    warehouse_id: Optional[int] = None,
    movement_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(StockMovement)
    count_query = select(func.count(StockMovement.id))
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
    result = await db.execute(query)
    movements = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": m.id, "movement_number": m.movement_number, "product_id": m.product_id,
                "warehouse_id": m.warehouse_id, "movement_type": m.movement_type,
                "quantity": m.quantity, "unit_cost": m.unit_cost,
                "reference_type": m.reference_type, "reference_id": m.reference_id,
                "notes": m.notes, "created_by": m.created_by,
                "created_at": m.created_at.isoformat() if m.created_at else None}
               for m in movements],
    )


@router.post("/stock-movements", response_model=dict)
async def create_stock_movement(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Create a stock movement.

    Accounting Logic (per ERP_INSTRUCTIONS.md):
      When stock is received (movement_type='in'):
        1. Updates product stock level
        2. Emits 'inventory.goods.received' event to the Ledger Engine
        3. Ledger Engine creates a balanced journal entry:
           Dr. Inventory Asset (1210)    totalCost
           Cr. GRNI Accrual (1230)       totalCost
    """
    movement = StockMovement(
        movement_number=data.get("movement_number"),
        product_id=data.get("product_id"),
        warehouse_id=data.get("warehouse_id"),
        batch_id=data.get("batch_id"),
        movement_type=data.get("movement_type", "in"),
        quantity=data.get("quantity", 0),
        unit_cost=data.get("unit_cost"),
        reference_type=data.get("reference_type"),
        reference_id=data.get("reference_id"),
        notes=data.get("notes"),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(movement)
    await db.flush()

    if movement.product_id:
        prod_result = await db.execute(select(Product).where(Product.id == movement.product_id))
        product = prod_result.scalar_one_or_none()
        if product:
            if movement.movement_type == "in":
                product.current_stock = (product.current_stock or 0) + movement.quantity

                # Emit goods.received event for accounting
                product_name = product.name
                warehouse_name = "Default Warehouse"
                if movement.warehouse_id:
                    wh_result = await db.execute(select(Warehouse).where(Warehouse.id == movement.warehouse_id))
                    warehouse = wh_result.scalar_one_or_none()
                    if warehouse:
                        warehouse_name = warehouse.name

                unit_cost = float(movement.unit_cost or product.purchase_price or 0)
                total_cost = unit_cost * movement.quantity

                await emit_goods_received(
                    transaction_id=movement.id,
                    product_id=movement.product_id,
                    product_name=product_name,
                    warehouse_id=movement.warehouse_id or 0,
                    warehouse_name=warehouse_name,
                    quantity=movement.quantity,
                    unit_cost=unit_cost,
                    total_cost=total_cost,
                    user_id=current_user.id,
                    company_id=product.company_id,
                )
                logger.info(f"Inventory: emitted goods.received event for movement {movement.id}")

            elif movement.movement_type == "out":
                product.current_stock = (product.current_stock or 0) - movement.quantity
            await db.flush()

    return {"id": movement.id, "message": "Stock movement created"}


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
async def create_transfer(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    transfer = StockTransfer(
        transfer_number=data.get("transfer_number", ""),
        from_warehouse_id=data.get("from_warehouse_id"),
        to_warehouse_id=data.get("to_warehouse_id"),
        transfer_date=data.get("transfer_date", ""),
        status=data.get("status", "draft"),
        notes=data.get("notes"),
        created_by=current_user.id,
        created_at=datetime.utcnow(),
    )
    db.add(transfer)
    await db.flush()
    for item_data in data.get("items", []):
        db.add(StockTransferItem(
            transfer_id=transfer.id, product_id=item_data.get("product_id"),
            quantity=item_data.get("quantity", 0), unit_cost=item_data.get("unit_cost"),
            batch_id=item_data.get("batch_id"), notes=item_data.get("notes"),
        ))
    await db.flush()
    return {"id": transfer.id, "message": "Transfer created"}
