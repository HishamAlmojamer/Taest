from datetime import UTC, datetime, date, timedelta
from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.sales import Customer, Lead
from app.models.purchases import Supplier, Purchase
from app.models.sales import Sale, SaleItem
from app.models.payments import CustomerPayment, SupplierPayment
from app.models.quotation import Quotation
from app.models.crm import (
    CustomerSegment, CustomerContact, CustomerAddress,
    OpportunityStage, Opportunity, FollowUp, CustomerLoyalty,
)
from app.models.user import User
from app.schemas.common import MessageResponse
from app.utils.deps import get_current_user, require_permission
from app.services.settings_service import get_setting

router = APIRouter()

MODEL_FIELDS = {
    "customer": Customer,
    "lead": Lead,
    "supplier": Supplier,
    "opportunity": Opportunity,
}

ENTITY_NAME_COLUMNS = {
    "customer": Customer.name,
    "lead": Lead.lead_name,
    "supplier": Supplier.name,
    "opportunity": Opportunity.name,
}


# ───────────────────────── Helpers ─────────────────────────

def _clean(data: dict, allowed: list[str]) -> dict:
    return {k: v for k, v in data.items() if k in allowed and v is not None}


async def _validate_parent(db, model, parent_id, node_id=None):
    """Ensure a parent exists and the assignment does not create a cycle."""
    if parent_id is None:
        return
    if node_id is not None and parent_id == node_id:
        raise HTTPException(status_code=400, detail="Cannot set a record as its own parent")
    result = await db.execute(select(model).where(model.id == parent_id))
    parent = result.scalar_one_or_none()
    if not parent:
        raise HTTPException(status_code=400, detail="Parent record not found")
    seen = set()
    current = parent
    while current is not None and current.parent_id is not None:
        if node_id is not None and current.parent_id == node_id:
            raise HTTPException(status_code=400, detail="Cannot set a descendant as parent")
        if current.parent_id in seen:
            break
        seen.add(current.parent_id)
        result = await db.execute(select(model).where(model.id == current.parent_id))
        current = result.scalar_one_or_none()


def _serialize_customer(c) -> dict:
    return {
        "id": c.id,
        "code": c.code,
        "name": c.name,
        "name_ar": c.name_ar,
        "phone": c.phone,
        "mobile": c.mobile,
        "email": c.email,
        "address": c.address,
        "city": c.city,
        "region": c.region,
        "country": c.country,
        "postal_code": c.postal_code,
        "website": c.website,
        "fax": c.fax,
        "national_id": c.national_id,
        "tax_id": c.tax_id,
        "customer_type": c.customer_type,
        "industry": c.industry,
        "segment_id": c.segment_id,
        "salesperson_id": c.salesperson_id,
        "parent_id": c.parent_id,
        "price_list": c.price_list,
        "currency": c.currency,
        "notes": c.notes,
        "birthdate": c.birthdate.isoformat() if c.birthdate else None,
        "gender": c.gender,
        "credit_limit": float(c.credit_limit or 0),
        "current_balance": float(c.current_balance or 0),
        "balance": float(c.current_balance or 0),
        "is_active": c.is_active if c.is_active is not None else True,
        "company_id": c.company_id,
        "last_interaction_at": c.last_interaction_at.isoformat() if c.last_interaction_at else None,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _serialize_supplier(s) -> dict:
    return {
        "id": s.id,
        "code": s.code,
        "name": s.name,
        "name_ar": s.name_ar,
        "contact_person": s.contact_person,
        "phone": s.phone,
        "email": s.email,
        "address": s.address,
        "city": s.city,
        "website": s.website,
        "fax": s.fax,
        "tax_id": s.tax_id,
        "industry": s.industry,
        "currency": s.currency,
        "payment_terms": s.payment_terms,
        "payment_term_id": s.payment_term_id,
        "bank_name": s.bank_name,
        "bank_account": s.bank_account,
        "iban": s.iban,
        "notes": s.notes,
        "current_balance": float(s.current_balance or 0),
        "balance": float(s.current_balance or 0),
        "is_active": s.is_active if s.is_active is not None else True,
        "company_id": s.company_id,
        "parent_id": s.parent_id,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


def _serialize_lead(l) -> dict:
    return {
        "id": l.id,
        "lead_name": l.lead_name,
        "company": l.company,
        "contact_person": l.contact_person,
        "phone": l.phone,
        "email": l.email,
        "source": l.source,
        "status": l.status,
        "industry": l.industry,
        "city": l.city,
        "expected_amount": float(l.expected_amount or 0),
        "budget": float(l.budget or 0) if l.budget else None,
        "lead_score": l.lead_score or 0,
        "assigned_to": l.assigned_to,
        "expected_close_date": l.expected_close_date.isoformat() if l.expected_close_date else None,
        "next_follow_up": l.next_follow_up.isoformat() if l.next_follow_up else None,
        "tags": l.tags,
        "notes": l.notes,
        "is_active": l.is_active if l.is_active is not None else True,
        "converted_customer_id": l.converted_customer_id,
        "converted_opportunity_id": l.converted_opportunity_id,
        "converted_at": l.converted_at.isoformat() if l.converted_at else None,
        "lost_reason": l.lost_reason,
        "won_amount": float(l.won_amount or 0) if l.won_amount else None,
        "company_id": l.company_id,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    }


def _serialize_opportunity(o, stage=None) -> dict:
    return {
        "id": o.id,
        "name": o.name,
        "customer_id": o.customer_id,
        "customer_name": o.customer_name,
        "lead_id": o.lead_id,
        "stage_id": o.stage_id,
        "stage": stage.name_ar if stage and stage.name_ar else (stage.name if stage else None),
        "stage_name": stage.name if stage else None,
        "stage_color": stage.color if stage else None,
        "source": o.source,
        "probability": float(o.probability or 0),
        "expected_amount": float(o.expected_amount or 0),
        "expected_close_date": o.expected_close_date.isoformat() if o.expected_close_date else None,
        "assigned_to": o.assigned_to,
        "description": o.description,
        "status": o.status,
        "won_amount": float(o.won_amount or 0),
        "closed_date": o.closed_date.isoformat() if o.closed_date else None,
        "won_lost_reason": o.won_lost_reason,
        "company_id": o.company_id,
        "created_at": o.created_at.isoformat() if o.created_at else None,
    }


def _serialize_followup(f) -> dict:
    return {
        "id": f.id,
        "entity_type": f.entity_type,
        "entity_id": f.entity_id,
        "type": f.type,
        "subject": f.subject,
        "description": f.description,
        "due_date": f.due_date.isoformat() if f.due_date else None,
        "completed_at": f.completed_at.isoformat() if f.completed_at else None,
        "assigned_to": f.assigned_to,
        "reminder_at": f.reminder_at.isoformat() if f.reminder_at else None,
        "priority": f.priority,
        "status": f.status,
        "created_by": f.created_by,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


# ───────────────────────── Segments ─────────────────────────

@router.get("/segments")
async def list_segments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CustomerSegment).order_by(CustomerSegment.name))
    items = []
    for s in result.scalars().all():
        count_res = await db.execute(select(func.count()).select_from(Customer).where(Customer.segment_id == s.id))
        items.append({
            "id": s.id,
            "name": s.name,
            "name_ar": s.name_ar,
            "description": s.description,
            "is_active": s.is_active if s.is_active is not None else True,
            "customer_count": count_res.scalar() or 0,
        })
    return {"items": items, "total": len(items)}


@router.post("/segments", response_model=dict)
async def create_segment(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    segment = CustomerSegment(
        name=data.get("name", ""),
        name_ar=data.get("name_ar"),
        description=data.get("description"),
        company_id=data.get("company_id"),
        is_active=data.get("is_active", True),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(segment)
    await db.flush()
    return {"id": segment.id, "message": "Segment created"}


@router.put("/segments/{segment_id}", response_model=dict)
async def update_segment(segment_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(CustomerSegment).where(CustomerSegment.id == segment_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Segment not found")
    values = _clean(data, ["name", "name_ar", "description", "is_active"])
    if values:
        await db.execute(update(CustomerSegment).where(CustomerSegment.id == segment_id).values(**values))
    return {"message": "Segment updated"}


@router.delete("/segments/{segment_id}", response_model=MessageResponse)
async def delete_segment(segment_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    linked = await db.execute(select(func.count()).select_from(Customer).where(Customer.segment_id == segment_id))
    if (linked.scalar() or 0) > 0:
        raise HTTPException(status_code=400, detail="Cannot delete segment with assigned customers")
    await db.execute(delete(CustomerSegment).where(CustomerSegment.id == segment_id))
    return MessageResponse(message="Segment deleted")


# ───────────────────────── Customers ─────────────────────────

@router.get("/customers")
async def list_customers(
    search: Optional[str] = None,
    segment_id: Optional[int] = None,
    customer_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Customer)
    count_query = select(func.count()).select_from(Customer)
    if search:
        like = f"%{search}%"
        query = query.where(Customer.name.ilike(like) | Customer.email.ilike(like) | Customer.phone.ilike(like) | Customer.code.ilike(like))
        count_query = count_query.where(Customer.name.ilike(like) | Customer.email.ilike(like) | Customer.phone.ilike(like) | Customer.code.ilike(like))
    if segment_id:
        query = query.where(Customer.segment_id == segment_id)
        count_query = count_query.where(Customer.segment_id == segment_id)
    if customer_type:
        query = query.where(Customer.customer_type == customer_type)
        count_query = count_query.where(Customer.customer_type == customer_type)
    if is_active is not None:
        query = query.where(Customer.is_active.is_(is_active))
        count_query = count_query.where(Customer.is_active.is_(is_active))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Customer.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    customers = result.scalars().all()

    # Bulk segment names
    segment_names = {}
    segment_ids = list({c.segment_id for c in customers if c.segment_id})
    if segment_ids:
        seg_res = await db.execute(select(CustomerSegment).where(CustomerSegment.id.in_(segment_ids)))
        segment_names = {s.id: s.name for s in seg_res.scalars().all()}

    items = []
    for c in customers:
        row = _serialize_customer(c)
        row["segment_name"] = segment_names.get(c.segment_id)
        items.append(row)
    return {"items": items, "total": total}


@router.get("/customers/tree")
async def get_customers_tree(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Customer).order_by(Customer.name)
    if not include_inactive:
        query = query.where(Customer.is_active.is_(True))
    customers = (await db.execute(query)).scalars().all()

    segment_ids = list({c.segment_id for c in customers if c.segment_id})
    segment_names = {}
    if segment_ids:
        seg_res = await db.execute(select(CustomerSegment).where(CustomerSegment.id.in_(segment_ids)))
        segment_names = {s.id: s.name for s in seg_res.scalars().all()}

    nodes = {}
    for c in customers:
        node = _serialize_customer(c)
        node["segment_name"] = segment_names.get(c.segment_id)
        node["children"] = []
        nodes[c.id] = node

    roots = []
    for c in customers:
        node = nodes[c.id]
        if c.parent_id and c.parent_id in nodes:
            nodes[c.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return {"items": roots, "total": len(customers)}


@router.get("/customers/{customer_id}")
async def get_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    customer = result.scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    contacts = (await db.execute(select(CustomerContact).where(CustomerContact.customer_id == customer_id).order_by(CustomerContact.is_primary.desc()))).scalars().all()
    addresses = (await db.execute(select(CustomerAddress).where(CustomerAddress.customer_id == customer_id))).scalars().all()
    loyalty = (await db.execute(select(CustomerLoyalty).where(CustomerLoyalty.customer_id == customer_id))).scalar_one_or_none()

    segment_name = None
    if customer.segment_id:
        seg = (await db.execute(select(CustomerSegment).where(CustomerSegment.id == customer.segment_id))).scalar_one_or_none()
        segment_name = seg.name if seg else None

    data = _serialize_customer(customer)
    data["segment_name"] = segment_name
    data["contacts"] = [{
        "id": ct.id,
        "customer_id": ct.customer_id,
        "name": ct.name,
        "title": ct.title,
        "department": ct.department,
        "phone": ct.phone,
        "mobile": ct.mobile,
        "email": ct.email,
        "is_primary": ct.is_primary or False,
        "is_active": ct.is_active if ct.is_active is not None else True,
        "notes": ct.notes,
    } for ct in contacts]
    data["addresses"] = [{
        "id": a.id,
        "customer_id": a.customer_id,
        "address_type": a.address_type,
        "address_line1": a.address_line1,
        "address_line2": a.address_line2,
        "city": a.city,
        "region": a.region,
        "country": a.country,
        "postal_code": a.postal_code,
        "is_primary": a.is_primary or False,
    } for a in addresses]
    data["loyalty"] = {
        "points_balance": float(loyalty.points_balance or 0) if loyalty else 0,
        "total_points_earned": float(loyalty.total_points_earned or 0) if loyalty else 0,
        "tier": loyalty.tier if loyalty else "regular",
    }
    return data


CUSTOMER_CREATE_FIELDS = [
    "name", "name_ar", "code", "phone", "mobile", "email", "address", "city",
    "region", "country", "postal_code", "website", "fax", "national_id",
    "tax_id", "customer_type", "industry", "segment_id", "salesperson_id",
    "parent_id", "price_list", "currency", "notes", "birthdate", "gender",
    "credit_limit", "current_balance", "payment_term_id", "company_id",
    "is_active",
]


@router.post("/customers", response_model=dict)
async def create_customer(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    values = _clean(data, CUSTOMER_CREATE_FIELDS)
    if not values.get("name"):
        raise HTTPException(status_code=400, detail="Customer name is required")
    if values.get("parent_id") == "":
        values.pop("parent_id", None)
    elif values.get("parent_id") is not None:
        values["parent_id"] = int(values["parent_id"])
        await _validate_parent(db, Customer, values["parent_id"])
    customer = Customer(**values)
    if customer.created_at is None:
        customer.created_at = datetime.now(UTC).replace(tzinfo=None)
    if customer.is_active is None:
        customer.is_active = True
    if not customer.currency:
        customer.currency = (await get_setting(db, "base_currency", default="SAR")).strip()
    db.add(customer)
    await db.flush()
    # Create an empty loyalty record
    db.add(CustomerLoyalty(customer_id=customer.id, points_balance=0, total_points_earned=0, tier="regular", created_at=datetime.now(UTC).replace(tzinfo=None)))
    await db.flush()
    return {"id": customer.id, "message": "Customer created"}


@router.put("/customers/{customer_id}", response_model=dict)
async def update_customer(customer_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(Customer).where(Customer.id == customer_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")
    values = _clean(data, CUSTOMER_CREATE_FIELDS)
    if "parent_id" in data:
        pv = data.get("parent_id")
        values["parent_id"] = None if pv is None or pv == "" else int(pv)
        if values["parent_id"] is not None:
            await _validate_parent(db, Customer, values["parent_id"], node_id=customer_id)
    if values:
        await db.execute(update(Customer).where(Customer.id == customer_id).values(**values))
    return {"message": "Customer updated"}


@router.delete("/customers/{customer_id}", response_model=MessageResponse)
async def delete_customer(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    children = (await db.execute(select(func.count()).select_from(Customer).where(Customer.parent_id == customer_id))).scalar() or 0
    if children > 0:
        raise HTTPException(status_code=400, detail="Cannot delete customer with branches. Remove or move child customers first.")
    related = (await db.execute(select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id))).scalar() or 0
    if related > 0:
        raise HTTPException(status_code=400, detail="Cannot delete customer with existing sales")
    await db.execute(delete(CustomerContact).where(CustomerContact.customer_id == customer_id))
    await db.execute(delete(CustomerAddress).where(CustomerAddress.customer_id == customer_id))
    await db.execute(delete(CustomerLoyalty).where(CustomerLoyalty.customer_id == customer_id))
    await db.execute(delete(Customer).where(Customer.id == customer_id))
    return MessageResponse(message="Customer deleted")


# ───────────── Customer Contacts ─────────────

@router.get("/customers/{customer_id}/contacts")
async def list_customer_contacts(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CustomerContact).where(CustomerContact.customer_id == customer_id).order_by(CustomerContact.is_primary.desc()))
    return {"items": [{
        "id": c.id, "customer_id": c.customer_id, "name": c.name, "title": c.title,
        "department": c.department, "phone": c.phone, "mobile": c.mobile,
        "email": c.email, "is_primary": c.is_primary or False,
        "is_active": c.is_active if c.is_active is not None else True, "notes": c.notes,
    } for c in result.scalars().all()]}


@router.post("/customers/{customer_id}/contacts", response_model=dict)
async def create_customer_contact(customer_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    if not (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")
    contact = CustomerContact(
        customer_id=customer_id,
        name=data.get("name", ""),
        title=data.get("title"),
        department=data.get("department"),
        phone=data.get("phone"),
        mobile=data.get("mobile"),
        email=data.get("email"),
        is_primary=data.get("is_primary", False),
        is_active=data.get("is_active", True),
        notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    if contact.is_primary:
        await db.execute(update(CustomerContact).where(CustomerContact.customer_id == customer_id).values(is_primary=False))
    db.add(contact)
    await db.flush()
    return {"id": contact.id, "message": "Contact created"}


@router.put("/contacts/{contact_id}", response_model=dict)
async def update_customer_contact(contact_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    contact = (await db.execute(select(CustomerContact).where(CustomerContact.id == contact_id))).scalar_one_or_none()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    values = _clean(data, ["name", "title", "department", "phone", "mobile", "email", "is_primary", "is_active", "notes"])
    if values.get("is_primary"):
        await db.execute(update(CustomerContact).where(CustomerContact.customer_id == contact.customer_id).values(is_primary=False))
    if values:
        await db.execute(update(CustomerContact).where(CustomerContact.id == contact_id).values(**values))
    return {"message": "Contact updated"}


@router.delete("/contacts/{contact_id}", response_model=MessageResponse)
async def delete_customer_contact(contact_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    await db.execute(delete(CustomerContact).where(CustomerContact.id == contact_id))
    return MessageResponse(message="Contact deleted")


# ───────────── Customer Addresses ─────────────

@router.get("/customers/{customer_id}/addresses")
async def list_customer_addresses(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CustomerAddress).where(CustomerAddress.customer_id == customer_id))
    return {"items": [{
        "id": a.id, "customer_id": a.customer_id, "address_type": a.address_type,
        "address_line1": a.address_line1, "address_line2": a.address_line2,
        "city": a.city, "region": a.region, "country": a.country,
        "postal_code": a.postal_code, "is_primary": a.is_primary or False,
    } for a in result.scalars().all()]}


@router.post("/customers/{customer_id}/addresses", response_model=dict)
async def create_customer_address(customer_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    if not (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")
    address = CustomerAddress(
        customer_id=customer_id,
        address_type=data.get("address_type", "billing"),
        address_line1=data.get("address_line1"),
        address_line2=data.get("address_line2"),
        city=data.get("city"),
        region=data.get("region"),
        country=data.get("country"),
        postal_code=data.get("postal_code"),
        is_primary=data.get("is_primary", False),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    if address.is_primary:
        await db.execute(update(CustomerAddress).where(CustomerAddress.customer_id == customer_id).values(is_primary=False))
    db.add(address)
    await db.flush()
    return {"id": address.id, "message": "Address created"}


@router.put("/addresses/{address_id}", response_model=dict)
async def update_customer_address(address_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    address = (await db.execute(select(CustomerAddress).where(CustomerAddress.id == address_id))).scalar_one_or_none()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    values = _clean(data, ["address_type", "address_line1", "address_line2", "city", "region", "country", "postal_code", "is_primary"])
    if values.get("is_primary"):
        await db.execute(update(CustomerAddress).where(CustomerAddress.customer_id == address.customer_id).values(is_primary=False))
    if values:
        await db.execute(update(CustomerAddress).where(CustomerAddress.id == address_id).values(**values))
    return {"message": "Address updated"}


@router.delete("/addresses/{address_id}", response_model=MessageResponse)
async def delete_customer_address(address_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    await db.execute(delete(CustomerAddress).where(CustomerAddress.id == address_id))
    return MessageResponse(message="Address deleted")


# ───────────── Customer Activities & Loyalty ─────────────

@router.get("/customers/{customer_id}/activities")
async def get_customer_activities(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    sales = (await db.execute(select(Sale).where(Sale.customer_id == customer_id).order_by(Sale.created_at.desc()).limit(50))).scalars().all()
    payments = (await db.execute(select(CustomerPayment).where(CustomerPayment.customer_id == customer_id).order_by(CustomerPayment.created_at.desc()).limit(50))).scalars().all()
    opportunities = (await db.execute(select(Opportunity).where(Opportunity.customer_id == customer_id).order_by(Opportunity.created_at.desc()).limit(50))).scalars().all()
    followups = (await db.execute(select(FollowUp).where(FollowUp.entity_type == "customer", FollowUp.entity_id == customer_id).order_by(FollowUp.created_at.desc()).limit(50))).scalars().all()
    quotations = (await db.execute(select(Quotation).where(Quotation.customer_id == customer_id).order_by(Quotation.created_at.desc()).limit(50))).scalars().all()

    activities = []
    for s in sales:
        activities.append({
            "type": "sale", "id": s.id, "title": f"فاتورة {s.invoice_number or s.id}",
            "amount": float(s.final_amount or 0), "status": s.workflow_state,
            "date": s.created_at.isoformat() if s.created_at else None,
        })
    for p in payments:
        activities.append({
            "type": "payment", "id": p.id, "title": "دفعة مستلمة",
            "amount": float(p.amount or 0), "status": p.payment_method,
            "date": p.payment_date.isoformat() if getattr(p, "payment_date", None) else (p.created_at.isoformat() if p.created_at else None),
        })
    for o in opportunities:
        activities.append({
            "type": "opportunity", "id": o.id, "title": o.name,
            "amount": float(o.expected_amount or 0), "status": o.status,
            "date": o.created_at.isoformat() if o.created_at else None,
        })
    for f in followups:
        activities.append({
            "type": "followup", "id": f.id, "title": f.subject or f.type,
            "amount": None, "status": f.status,
            "date": f.created_at.isoformat() if f.created_at else None,
        })
    for q in quotations:
        activities.append({
            "type": "quotation", "id": q.id, "title": f"عرض سعر {q.quotation_number or q.id}",
            "amount": float(q.final_amount or 0), "status": q.status,
            "date": q.created_at.isoformat() if q.created_at else None,
        })
    activities.sort(key=lambda a: a["date"] or "", reverse=True)
    return {"items": activities}


@router.get("/loyalty")
async def list_customer_loyalty(
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List customers with their loyalty points (for the loyalty dashboard)."""
    query = select(Customer)
    count_query = select(func.count(Customer.id)).select_from(Customer)
    if search:
        like = f"%{search}%"
        query = query.where(Customer.name.ilike(like) | Customer.name_ar.ilike(like) | Customer.email.ilike(like))
        count_query = count_query.where(Customer.name.ilike(like) | Customer.name_ar.ilike(like) | Customer.email.ilike(like))

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Customer.id.desc()).offset(offset).limit(page_size))
    customers = result.scalars().all()

    loyalties = {
        l.customer_id: l
        for l in (await db.execute(select(CustomerLoyalty))).scalars().all()
    }

    items = []
    for c in customers:
        l = loyalties.get(c.id)
        items.append({
            "customer_id": c.id,
            "customer_name": c.name,
            "customer_name_ar": c.name_ar if hasattr(c, "name_ar") else None,
            "customer_phone": getattr(c, "phone", None),
            "points_balance": float(l.points_balance or 0) if l else 0,
            "total_points_earned": float(l.total_points_earned or 0) if l else 0,
            "tier": l.tier if l else "regular",
        })

    items.sort(key=lambda it: it["points_balance"], reverse=True)
    return {"total": total, "page": page, "per_page": page_size, "pages": int((total + page_size - 1) // page_size) if total else 0, "items": items}


@router.get("/customers/{customer_id}/loyalty")
async def get_customer_loyalty(customer_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    loyalty = (await db.execute(select(CustomerLoyalty).where(CustomerLoyalty.customer_id == customer_id))).scalar_one_or_none()
    if not loyalty:
        return {"customer_id": customer_id, "points_balance": 0, "total_points_earned": 0, "tier": "regular"}
    return {
        "customer_id": customer_id,
        "points_balance": float(loyalty.points_balance or 0),
        "total_points_earned": float(loyalty.total_points_earned or 0),
        "tier": loyalty.tier,
    }


@router.post("/customers/{customer_id}/loyalty/adjust", response_model=dict)
async def adjust_customer_loyalty(customer_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    points = float(data.get("points", 0))
    loyalty = (await db.execute(select(CustomerLoyalty).where(CustomerLoyalty.customer_id == customer_id))).scalar_one_or_none()
    if not loyalty:
        loyalty = CustomerLoyalty(customer_id=customer_id, points_balance=0, total_points_earned=0, tier="regular", created_at=datetime.now(UTC).replace(tzinfo=None))
        db.add(loyalty)
        await db.flush()
    new_balance = float(loyalty.points_balance or 0) + points
    if new_balance < 0:
        raise HTTPException(status_code=400, detail="Insufficient loyalty points")
    loyalty.points_balance = new_balance
    if points > 0:
        loyalty.total_points_earned = float(loyalty.total_points_earned or 0) + points
        loyalty.last_earned_at = datetime.now(UTC).replace(tzinfo=None)
    return {"message": "Loyalty points updated", "points_balance": new_balance}


# ───────────────────────── Suppliers ─────────────────────────

SUPPLIER_CREATE_FIELDS = [
    "name", "name_ar", "code", "contact_person", "phone", "email", "address",
    "city", "website", "fax", "tax_id", "industry", "currency", "payment_terms",
    "payment_term_id", "bank_name", "bank_account", "iban", "notes",
    "current_balance", "company_id", "parent_id", "is_active",
]


@router.get("/suppliers")
async def list_suppliers(
    search: Optional[str] = None,
    is_active: Optional[bool] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Supplier)
    count_query = select(func.count()).select_from(Supplier)
    if search:
        like = f"%{search}%"
        query = query.where(Supplier.name.ilike(like) | Supplier.email.ilike(like) | Supplier.phone.ilike(like))
        count_query = count_query.where(Supplier.name.ilike(like) | Supplier.email.ilike(like) | Supplier.phone.ilike(like))
    if is_active is not None:
        query = query.where(Supplier.is_active.is_(is_active))
        count_query = count_query.where(Supplier.is_active.is_(is_active))
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Supplier.name).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [_serialize_supplier(s) for s in result.scalars().all()]
    return {"items": items, "total": total}


@router.get("/suppliers/tree")
async def get_suppliers_tree(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Supplier).order_by(Supplier.name)
    if not include_inactive:
        query = query.where(Supplier.is_active.is_(True))
    suppliers = (await db.execute(query)).scalars().all()

    nodes = {}
    for s in suppliers:
        node = _serialize_supplier(s)
        node["children"] = []
        nodes[s.id] = node

    roots = []
    for s in suppliers:
        node = nodes[s.id]
        if s.parent_id and s.parent_id in nodes:
            nodes[s.parent_id]["children"].append(node)
        else:
            roots.append(node)
    return {"items": roots, "total": len(suppliers)}


@router.get("/suppliers/{supplier_id}")
async def get_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    supplier = (await db.execute(select(Supplier).where(Supplier.id == supplier_id))).scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return _serialize_supplier(supplier)


@router.post("/suppliers", response_model=dict)
async def create_supplier(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    values = _clean(data, SUPPLIER_CREATE_FIELDS)
    if not values.get("name"):
        raise HTTPException(status_code=400, detail="Supplier name is required")
    if values.get("parent_id") == "":
        values.pop("parent_id", None)
    elif values.get("parent_id") is not None:
        values["parent_id"] = int(values["parent_id"])
        await _validate_parent(db, Supplier, values["parent_id"])
    supplier = Supplier(**values)
    if supplier.created_at is None:
        supplier.created_at = datetime.now(UTC).replace(tzinfo=None)
    if supplier.is_active is None:
        supplier.is_active = True
    if not supplier.currency:
        supplier.currency = (await get_setting(db, "base_currency", default="SAR")).strip()
    db.add(supplier)
    await db.flush()
    return {"id": supplier.id, "message": "Supplier created"}


@router.put("/suppliers/{supplier_id}", response_model=dict)
async def update_supplier(supplier_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Supplier not found")
    values = _clean(data, SUPPLIER_CREATE_FIELDS)
    if "parent_id" in data:
        pv = data.get("parent_id")
        values["parent_id"] = None if pv is None or pv == "" else int(pv)
        if values["parent_id"] is not None:
            await _validate_parent(db, Supplier, values["parent_id"], node_id=supplier_id)
    if values:
        await db.execute(update(Supplier).where(Supplier.id == supplier_id).values(**values))
    return {"message": "Supplier updated"}


@router.delete("/suppliers/{supplier_id}", response_model=MessageResponse)
async def delete_supplier(supplier_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    supplier = (await db.execute(select(Supplier).where(Supplier.id == supplier_id))).scalar_one_or_none()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    children = (await db.execute(select(func.count()).select_from(Supplier).where(Supplier.parent_id == supplier_id))).scalar() or 0
    if children > 0:
        raise HTTPException(status_code=400, detail="Cannot delete supplier with branches. Remove or move child suppliers first.")
    related = (await db.execute(select(func.count()).select_from(Purchase).where(Purchase.supplier_id == supplier_id))).scalar() or 0
    if related > 0:
        raise HTTPException(status_code=400, detail="Cannot delete supplier with existing purchases")
    await db.execute(delete(Supplier).where(Supplier.id == supplier_id))
    return MessageResponse(message="Supplier deleted")


# ───────────────────────── Leads ─────────────────────────

LEAD_CREATE_FIELDS = [
    "lead_name", "company", "contact_person", "phone", "email", "source",
    "status", "industry", "city", "expected_amount", "budget", "lead_score",
    "assigned_to", "expected_close_date", "next_follow_up", "tags", "notes",
    "company_id", "is_active",
]


@router.get("/leads")
async def list_leads(
    search: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    assigned_to: Optional[int] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Lead)
    count_query = select(func.count()).select_from(Lead)
    if search:
        like = f"%{search}%"
        query = query.where(Lead.lead_name.ilike(like) | Lead.company.ilike(like) | Lead.email.ilike(like) | Lead.phone.ilike(like))
        count_query = count_query.where(Lead.lead_name.ilike(like) | Lead.company.ilike(like) | Lead.email.ilike(like) | Lead.phone.ilike(like))
    if status:
        query = query.where(Lead.status == status)
        count_query = count_query.where(Lead.status == status)
    if source:
        query = query.where(Lead.source == source)
        count_query = count_query.where(Lead.source == source)
    if assigned_to:
        query = query.where(Lead.assigned_to == assigned_to)
        count_query = count_query.where(Lead.assigned_to == assigned_to)
    total = (await db.execute(count_query)).scalar() or 0
    query = query.order_by(Lead.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    items = [_serialize_lead(l) for l in result.scalars().all()]
    return {"items": items, "total": total}


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    data = _serialize_lead(lead)
    followups = (await db.execute(select(FollowUp).where(FollowUp.entity_type == "lead", FollowUp.entity_id == lead_id).order_by(FollowUp.due_date.desc()))).scalars().all()
    data["followups"] = [_serialize_followup(f) for f in followups]
    return data


@router.post("/leads", response_model=dict)
async def create_lead(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    values = _clean(data, LEAD_CREATE_FIELDS)
    if not values.get("lead_name"):
        raise HTTPException(status_code=400, detail="Lead name is required")
    lead = Lead(**values)
    if lead.created_at is None:
        lead.created_at = datetime.now(UTC).replace(tzinfo=None)
    lead.updated_at = datetime.now(UTC).replace(tzinfo=None)
    if lead.status is None:
        lead.status = "new"
    if lead.lead_score is None:
        lead.lead_score = 0
    if lead.is_active is None:
        lead.is_active = True
    db.add(lead)
    await db.flush()
    return {"id": lead.id, "message": "Lead created"}


@router.put("/leads/{lead_id}", response_model=dict)
async def update_lead(lead_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Lead not found")
    values = _clean(data, LEAD_CREATE_FIELDS)
    values["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
    if values:
        await db.execute(update(Lead).where(Lead.id == lead_id).values(**values))
    return {"message": "Lead updated"}


@router.delete("/leads/{lead_id}", response_model=MessageResponse)
async def delete_lead(lead_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    await db.execute(delete(FollowUp).where(FollowUp.entity_type == "lead", FollowUp.entity_id == lead_id))
    await db.execute(delete(Lead).where(Lead.id == lead_id))
    return MessageResponse(message="Lead deleted")


@router.post("/leads/{lead_id}/convert", response_model=dict)
async def convert_lead(lead_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    """Convert a lead into a customer (optionally creating an opportunity)."""
    lead = (await db.execute(select(Lead).where(Lead.id == lead_id))).scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.converted_customer_id:
        raise HTTPException(status_code=400, detail="Lead already converted")

    customer = Customer(
        name=lead.lead_name,
        name_ar=data.get("name_ar"),
        email=lead.email,
        phone=lead.phone,
        mobile=data.get("mobile"),
        address=lead.company or data.get("address"),
        city=lead.city,
        industry=lead.industry,
        customer_type=data.get("customer_type", "customer"),
        tax_id=data.get("tax_id"),
        credit_limit=data.get("credit_limit", 0),
        current_balance=0,
        company_id=data.get("company_id", lead.company_id),
        notes=lead.notes,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        is_active=True,
    )
    db.add(customer)
    await db.flush()
    db.add(CustomerLoyalty(customer_id=customer.id, points_balance=0, total_points_earned=0, tier="regular", created_at=datetime.now(UTC).replace(tzinfo=None)))

    lead.converted_customer_id = customer.id
    lead.converted_at = datetime.now(UTC).replace(tzinfo=None)
    lead.updated_at = datetime.now(UTC).replace(tzinfo=None)
    lead.status = "won"

    opportunity_id = None
    if data.get("create_opportunity", True):
        stage = (await db.execute(select(OpportunityStage).where(OpportunityStage.is_won.is_(False), OpportunityStage.is_lost.is_(False)).order_by(OpportunityStage.position))).scalars().first()
        opportunity = Opportunity(
            name=data.get("opportunity_name") or lead.lead_name,
            customer_id=customer.id,
            customer_name=customer.name,
            lead_id=lead.id,
            stage_id=stage.id if stage else None,
            source=lead.source,
            expected_amount=data.get("expected_amount", lead.expected_amount or 0),
            probability=float(stage.probability or 0) if stage else 0,
            expected_close_date=data.get("expected_close_date") or lead.expected_close_date,
            assigned_to=data.get("assigned_to", lead.assigned_to),
            description=lead.notes,
            status="OPEN",
            created_by=current_user.id,
            company_id=lead.company_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(opportunity)
        await db.flush()
        opportunity_id = opportunity.id
        lead.converted_opportunity_id = opportunity.id

    await db.flush()
    return {
        "message": "Lead converted to customer",
        "customer_id": customer.id,
        "opportunity_id": opportunity_id,
    }


# ─────────────────────── Opportunity Stages ───────────────────────

@router.get("/opportunity-stages")
async def list_opportunity_stages(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(OpportunityStage).order_by(OpportunityStage.position))
    return {"items": [{
        "id": s.id, "name": s.name, "name_ar": s.name_ar, "position": s.position,
        "probability": float(s.probability or 0), "is_won": s.is_won or False,
        "is_lost": s.is_lost or False, "color": s.color,
        "is_active": s.is_active if s.is_active is not None else True,
    } for s in result.scalars().all()]}


@router.post("/opportunity-stages", response_model=dict)
async def create_opportunity_stage(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    stage = OpportunityStage(
        name=data.get("name", ""),
        name_ar=data.get("name_ar"),
        position=data.get("position", 0),
        probability=data.get("probability", 0),
        is_won=data.get("is_won", False),
        is_lost=data.get("is_lost", False),
        color=data.get("color", "#0ea5e9"),
        is_active=data.get("is_active", True),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(stage)
    await db.flush()
    return {"id": stage.id, "message": "Stage created"}


@router.put("/opportunity-stages/{stage_id}", response_model=dict)
async def update_opportunity_stage(stage_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(OpportunityStage).where(OpportunityStage.id == stage_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Stage not found")
    values = _clean(data, ["name", "name_ar", "position", "probability", "is_won", "is_lost", "color", "is_active"])
    if values:
        await db.execute(update(OpportunityStage).where(OpportunityStage.id == stage_id).values(**values))
    return {"message": "Stage updated"}


@router.delete("/opportunity-stages/{stage_id}", response_model=MessageResponse)
async def delete_opportunity_stage(stage_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    linked = (await db.execute(select(func.count()).select_from(Opportunity).where(Opportunity.stage_id == stage_id))).scalar() or 0
    if linked > 0:
        raise HTTPException(status_code=400, detail="Cannot delete stage with opportunities")
    await db.execute(delete(OpportunityStage).where(OpportunityStage.id == stage_id))
    return MessageResponse(message="Stage deleted")


# ───────────────────────── Opportunities ─────────────────────────

OPPORTUNITY_CREATE_FIELDS = [
    "name", "customer_id", "customer_name", "lead_id", "stage_id", "source",
    "probability", "expected_amount", "expected_close_date", "assigned_to",
    "description", "status", "company_id",
]


@router.get("/opportunities")
async def list_opportunities(
    stage_id: Optional[int] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    customer_id: Optional[int] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Opportunity)
    if stage_id:
        query = query.where(Opportunity.stage_id == stage_id)
    if status:
        query = query.where(Opportunity.status == status)
    if assigned_to:
        query = query.where(Opportunity.assigned_to == assigned_to)
    if customer_id:
        query = query.where(Opportunity.customer_id == customer_id)
    if search:
        like = f"%{search}%"
        query = query.where(Opportunity.name.ilike(like) | Opportunity.customer_name.ilike(like))
    query = query.order_by(Opportunity.updated_at.desc())
    result = await db.execute(query)
    opportunities = result.scalars().all()

    stage_ids = list({o.stage_id for o in opportunities if o.stage_id})
    stages = {}
    if stage_ids:
        stage_res = await db.execute(select(OpportunityStage).where(OpportunityStage.id.in_(stage_ids)))
        stages = {s.id: s for s in stage_res.scalars().all()}

    return {"items": [_serialize_opportunity(o, stages.get(o.stage_id)) for o in opportunities]}


@router.get("/opportunities/{opportunity_id}")
async def get_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    opportunity = (await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    stage = None
    if opportunity.stage_id:
        stage = (await db.execute(select(OpportunityStage).where(OpportunityStage.id == opportunity.stage_id))).scalar_one_or_none()
    return _serialize_opportunity(opportunity, stage)


@router.post("/opportunities", response_model=dict)
async def create_opportunity(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    values = _clean(data, OPPORTUNITY_CREATE_FIELDS)
    if not values.get("name"):
        raise HTTPException(status_code=400, detail="Opportunity name is required")
    if not values.get("customer_id"):
        raise HTTPException(status_code=400, detail="Customer is required")
    # Auto-fill customer name
    if not values.get("customer_name"):
        customer = (await db.execute(select(Customer).where(Customer.id == values["customer_id"]))).scalar_one_or_none()
        if customer:
            values["customer_name"] = customer.name
    if values.get("stage_id"):
        stage = (await db.execute(select(OpportunityStage).where(OpportunityStage.id == values["stage_id"]))).scalar_one_or_none()
        if stage:
            values["probability"] = values.get("probability") or float(stage.probability or 0)
    opportunity = Opportunity(**values)
    if opportunity.created_at is None:
        opportunity.created_at = datetime.now(UTC).replace(tzinfo=None)
    opportunity.updated_at = datetime.now(UTC).replace(tzinfo=None)
    if opportunity.status is None:
        opportunity.status = "OPEN"
    if opportunity.expected_amount is None:
        opportunity.expected_amount = 0
    opportunity.created_by = current_user.id
    db.add(opportunity)
    await db.flush()
    # Touch last interaction on customer
    await db.execute(update(Customer).where(Customer.id == opportunity.customer_id).values(last_interaction_at=datetime.now(UTC).replace(tzinfo=None)))
    return {"id": opportunity.id, "message": "Opportunity created"}


@router.put("/opportunities/{opportunity_id}", response_model=dict)
async def update_opportunity(opportunity_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Opportunity not found")
    values = _clean(data, OPPORTUNITY_CREATE_FIELDS)
    values["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
    if values:
        await db.execute(update(Opportunity).where(Opportunity.id == opportunity_id).values(**values))
    return {"message": "Opportunity updated"}


@router.delete("/opportunities/{opportunity_id}", response_model=MessageResponse)
async def delete_opportunity(opportunity_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    await db.execute(delete(Opportunity).where(Opportunity.id == opportunity_id))
    return MessageResponse(message="Opportunity deleted")


@router.post("/opportunities/{opportunity_id}/move", response_model=dict)
async def move_opportunity(opportunity_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    """Move an opportunity to another pipeline stage."""
    opportunity = (await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    stage_id = data.get("stage_id")
    if not stage_id:
        raise HTTPException(status_code=400, detail="stage_id is required")
    stage = (await db.execute(select(OpportunityStage).where(OpportunityStage.id == stage_id))).scalar_one_or_none()
    if not stage:
        raise HTTPException(status_code=404, detail="Stage not found")
    opportunity.stage_id = stage_id
    opportunity.probability = float(stage.probability or opportunity.probability or 0)
    if stage.is_won:
        opportunity.status = "WON"
        opportunity.won_amount = float(opportunity.expected_amount or 0)
        opportunity.closed_date = date.today()
    elif stage.is_lost:
        opportunity.status = "LOST"
        opportunity.closed_date = date.today()
    else:
        opportunity.status = "OPEN"
    opportunity.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return {"message": "Opportunity moved", "status": opportunity.status}


@router.post("/opportunities/{opportunity_id}/close", response_model=dict)
async def close_opportunity(opportunity_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    """Close an opportunity as won or lost with amount and reason."""
    opportunity = (await db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))).scalar_one_or_none()
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    result_status = data.get("status", "WON").upper()
    if result_status not in ("WON", "LOST"):
        raise HTTPException(status_code=400, detail="status must be WON or LOST")
    opportunity.status = result_status
    opportunity.won_amount = data.get("won_amount") if result_status == "WON" else 0
    opportunity.won_lost_reason = data.get("reason")
    opportunity.closed_date = data.get("closed_date") or date.today()
    opportunity.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return {"message": f"Opportunity {result_status.lower()}", "id": opportunity.id}


# ───────────────────────── Follow-ups ─────────────────────────

FOLLOWUP_CREATE_FIELDS = [
    "entity_type", "entity_id", "type", "subject", "description", "due_date",
    "assigned_to", "reminder_at", "priority", "status",
]


@router.get("/follow-ups")
async def list_followups(
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    status: Optional[str] = None,
    assigned_to: Optional[int] = None,
    due_before: Optional[str] = None,
    overdue: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(FollowUp)
    if entity_type:
        query = query.where(FollowUp.entity_type == entity_type)
    if entity_id:
        query = query.where(FollowUp.entity_id == entity_id)
    if status:
        query = query.where(FollowUp.status == status)
    if assigned_to:
        query = query.where(FollowUp.assigned_to == assigned_to)
    if overdue:
        query = query.where(FollowUp.status == "OPEN", FollowUp.due_date < datetime.now(UTC).replace(tzinfo=None))
    elif due_before:
        query = query.where(FollowUp.due_date <= due_before)
    query = query.order_by(FollowUp.due_date.asc())
    result = await db.execute(query)
    items = [_serialize_followup(f) for f in result.scalars().all()]

    # Resolve entity display names
    ids_by_type: dict[str, list[int]] = {}
    for f in items:
        if f["entity_type"] and f["entity_id"]:
            ids_by_type.setdefault(f["entity_type"], []).append(f["entity_id"])
    names: dict[str, dict[int, str]] = {}
    for et, ids in ids_by_type.items():
        model = MODEL_FIELDS.get(et)
        if not model:
            continue
        name_col = ENTITY_NAME_COLUMNS.get(et) or getattr(model, "name", None)
        if name_col is None:
            continue
        rows = (await db.execute(select(model.id, name_col).where(model.id.in_(ids)))).all()
        names[et] = {r[0]: r[1] for r in rows}
    for f in items:
        f["entity_name"] = names.get(f["entity_type"], {}).get(f["entity_id"])

    return {"items": items}


@router.get("/follow-ups/{follow_up_id}")
async def get_followup(follow_up_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    followup = (await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))).scalar_one_or_none()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return _serialize_followup(followup)


@router.post("/follow-ups", response_model=dict)
async def create_followup(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    values = _clean(data, FOLLOWUP_CREATE_FIELDS)
    followup = FollowUp(**values)
    if followup.created_at is None:
        followup.created_at = datetime.now(UTC).replace(tzinfo=None)
    if followup.status is None:
        followup.status = "OPEN"
    if followup.priority is None:
        followup.priority = "medium"
    if followup.type is None:
        followup.type = "call"
    if not followup.subject and not followup.description:
        raise HTTPException(status_code=400, detail="Subject or description is required")
    followup.created_by = current_user.id
    db.add(followup)
    await db.flush()
    return {"id": followup.id, "message": "Follow-up created"}


@router.put("/follow-ups/{follow_up_id}", response_model=dict)
async def update_followup(follow_up_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    result = await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Follow-up not found")
    values = _clean(data, FOLLOWUP_CREATE_FIELDS)
    if values:
        await db.execute(update(FollowUp).where(FollowUp.id == follow_up_id).values(**values))
    return {"message": "Follow-up updated"}


@router.post("/follow-ups/{follow_up_id}/complete", response_model=dict)
async def complete_followup(follow_up_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    followup = (await db.execute(select(FollowUp).where(FollowUp.id == follow_up_id))).scalar_one_or_none()
    if not followup:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    followup.status = "DONE"
    followup.completed_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return {"message": "Follow-up completed"}


@router.delete("/follow-ups/{follow_up_id}", response_model=MessageResponse)
async def delete_followup(follow_up_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_CRM"))):
    await db.execute(delete(FollowUp).where(FollowUp.id == follow_up_id))
    return MessageResponse(message="Follow-up deleted")


# ───────────────────────── Dashboard & Reports ─────────────────────────

@router.get("/dashboard")
async def crm_dashboard(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_customers = (await db.execute(select(func.count()).select_from(Customer))).scalar() or 0
    total_leads = (await db.execute(select(func.count()).select_from(Lead))).scalar() or 0
    open_opportunities = (await db.execute(select(func.count()).select_from(Opportunity).where(Opportunity.status == "OPEN"))).scalar() or 0
    pipeline_value = (await db.execute(select(func.coalesce(func.sum(Opportunity.expected_amount), 0)).select_from(Opportunity).where(Opportunity.status == "OPEN"))).scalar() or 0
    won_value = (await db.execute(select(func.coalesce(func.sum(Opportunity.won_amount), 0)).select_from(Opportunity).where(Opportunity.status == "WON"))).scalar() or 0

    upcoming_followups = (await db.execute(
        select(FollowUp).where(FollowUp.status == "OPEN").order_by(FollowUp.due_date.asc()).limit(8)
    )).scalars().all()

    # Leads by status
    lead_rows = (await db.execute(select(Lead.status, func.count()).group_by(Lead.status))).all()
    leads_by_status = [{"status": s or "new", "count": c} for s, c in lead_rows]

    return {
        "total_customers": total_customers,
        "total_leads": total_leads,
        "open_opportunities": open_opportunities,
        "pipeline_value": float(pipeline_value),
        "won_value": float(won_value),
        "leads_by_status": leads_by_status,
        "upcoming_followups": [_serialize_followup(f) for f in upcoming_followups],
    }


@router.get("/reports/leads-by-source")
async def report_leads_by_source(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (await db.execute(select(Lead.source, func.count()).where(Lead.source.isnot(None)).group_by(Lead.source).order_by(func.count().desc()))).all()
    return {"items": [{"source": s, "count": c} for s, c in rows]}


@router.get("/reports/pipeline-funnel")
async def report_pipeline_funnel(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    stages = (await db.execute(select(OpportunityStage).where(OpportunityStage.is_active.is_(True)).order_by(OpportunityStage.position))).scalars().all()
    items = []
    for stage in stages:
        count = (await db.execute(select(func.count()).select_from(Opportunity).where(Opportunity.stage_id == stage.id))).scalar() or 0
        value = (await db.execute(select(func.coalesce(func.sum(Opportunity.expected_amount), 0)).select_from(Opportunity).where(Opportunity.stage_id == stage.id))).scalar() or 0
        items.append({
            "stage_id": stage.id,
            "name": stage.name,
            "name_ar": stage.name_ar,
            "color": stage.color,
            "count": count,
            "value": float(value),
            "is_won": stage.is_won or False,
            "is_lost": stage.is_lost or False,
        })
    return {"items": items}


@router.get("/reports/customers-by-segment")
async def report_customers_by_segment(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    segments = (await db.execute(select(CustomerSegment).order_by(CustomerSegment.name))).scalars().all()
    items = []
    for seg in segments:
        count = (await db.execute(select(func.count()).select_from(Customer).where(Customer.segment_id == seg.id))).scalar() or 0
        value = (await db.execute(select(func.coalesce(func.sum(Sale.final_amount), 0)).select_from(Sale).where(Sale.customer_id.in_(
            select(Customer.id).where(Customer.segment_id == seg.id)
        )))).scalar() or 0
        items.append({
            "segment_id": seg.id,
            "name": seg.name,
            "name_ar": seg.name_ar,
            "customer_count": count,
            "total_sales": float(value),
        })
    return {"items": items}


@router.get("/reports/top-customers")
async def report_top_customers(limit: int = Query(10, ge=1, le=50), db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rows = (await db.execute(
        select(Sale.customer_id, func.sum(Sale.final_amount).label("total"))
        .where(Sale.customer_id.isnot(None), Sale.workflow_state.in_(["approved", "submitted", "paid", "partially_paid"]) | Sale.workflow_state.is_(None))
        .group_by(Sale.customer_id)
        .order_by(func.sum(Sale.final_amount).desc())
        .limit(limit)
    )).all()
    items = []
    for customer_id, total in rows:
        customer = (await db.execute(select(Customer).where(Customer.id == customer_id))).scalar_one_or_none()
        if customer:
            items.append({
                "customer_id": customer.id,
                "name": customer.name,
                "total_sales": float(total),
            })
    return {"items": items}
