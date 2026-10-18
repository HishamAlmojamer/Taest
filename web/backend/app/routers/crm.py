from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.sales import Customer
from app.models.purchases import Supplier
from app.models.user import User
from app.schemas.common import MessageResponse
from app.utils.deps import get_current_user

router = APIRouter()


# ── Customers ─────────────────────────────────────────────────

@router.get("/customers")
async def list_customers(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Customer)
    if search:
        query = query.where(Customer.name.ilike(f"%{search}%"))
    query = query.order_by(Customer.name).limit(200)
    result = await db.execute(query)
    items = [{"id": c.id, "name": c.name, "phone": c.phone, "email": c.email,
             "address": c.address, "balance": c.current_balance or 0,
             "current_balance": c.current_balance or 0,
             "credit_limit": c.credit_limit or 0, "company_id": c.company_id,
             "city": None, "isActive": True}
            for c in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"id": customer.id, "name": customer.name, "phone": customer.phone,
            "email": customer.email, "address": customer.address,
            "current_balance": customer.current_balance or 0,
            "credit_limit": customer.credit_limit or 0, "company_id": customer.company_id}


@router.post("/customers", response_model=dict)
async def create_customer(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = Customer(
        name=data.get("name", ""), phone=data.get("phone"),
        email=data.get("email"), address=data.get("address"),
        current_balance=data.get("current_balance", 0),
        credit_limit=data.get("credit_limit", 0),
        company_id=data.get("company_id"),
    )
    db.add(customer)
    await db.flush()
    return {"id": customer.id, "message": "Customer created"}


@router.put("/customers/{customer_id}", response_model=dict)
async def update_customer(customer_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")
    allowed = ['name', 'phone', 'email', 'address', 'current_balance', 'credit_limit', 'company_id']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Customer).where(Customer.id == customer_id).values(**values))
    return {"message": "Customer updated"}


@router.delete("/customers/{customer_id}", response_model=MessageResponse)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(delete(Customer).where(Customer.id == customer_id))
    return MessageResponse(message="Customer deleted")


# ── Suppliers ─────────────────────────────────────────────────

@router.get("/suppliers")
async def list_suppliers(
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Supplier)
    if search:
        query = query.where(Supplier.name.ilike(f"%{search}%"))
    query = query.order_by(Supplier.name).limit(200)
    result = await db.execute(query)
    items = [{"id": s.id, "name": s.name, "contactPerson": s.contact_person,
             "phone": s.phone, "email": s.email, "address": s.address,
             "balance": 0, "city": None, "isActive": True}
            for s in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"id": supplier.id, "name": supplier.name, "contact_person": supplier.contact_person,
            "phone": supplier.phone, "email": supplier.email, "address": supplier.address}


@router.post("/suppliers", response_model=dict)
async def create_supplier(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = Supplier(
        name=data.get("name", ""), contact_person=data.get("contact_person"),
        phone=data.get("phone"), email=data.get("email"), address=data.get("address"),
    )
    db.add(supplier)
    await db.flush()
    return {"id": supplier.id, "message": "Supplier created"}


@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(supplier_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")
    allowed = ['name', 'contact_person', 'phone', 'email', 'address']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Supplier).where(Supplier.id == supplier_id).values(**values))
    return {"message": "Supplier updated"}


@router.delete("/suppliers/{supplier_id}", response_model=MessageResponse)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(delete(Supplier).where(Supplier.id == supplier_id))
    return MessageResponse(message="Supplier deleted")


# ── Leads (read-only) ────────────────────────────────────────

@router.get("/leads")
async def list_leads(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        from sqlalchemy import text
        result = await db.execute(text("SELECT id, lead_name, company, phone, email, source, expected_amount, status FROM leads ORDER BY created_at DESC LIMIT 200"))
        rows = result.fetchall()
        return [{"id": r[0], "lead_name": r[1], "company": r[2], "phone": r[3],
                 "email": r[4], "source": r[5], "expected_amount": r[6], "status": r[7]}
                for r in rows]
    except Exception:
        return []
