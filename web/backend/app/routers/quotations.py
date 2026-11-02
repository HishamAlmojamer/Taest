import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.quotation import Quotation, QuotationItem
from app.models.sales import Customer, Sale, SaleItem
from app.models.inventory import Product
from app.models.user import User
from app.schemas.quotation import QuotationCreate
from app.schemas.common import PaginationResponse
from app.utils.deps import get_current_user, require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


def _ceil(n: float) -> int:
    return int(n) + (1 if n % 1 > 0 else 0)


async def _build_quotation(quotation, items, db) -> dict:
    customer_name = ""
    if quotation.customer_id:
        cust = (await db.execute(select(Customer).where(Customer.id == quotation.customer_id))).scalar_one_or_none()
        if cust:
            customer_name = cust.name

    product_ids = list({i.product_id for i in items if i.product_id})
    product_map = {}
    if product_ids:
        pr = await db.execute(select(Product).where(Product.id.in_(product_ids)))
        product_map = {p.id: p.name for p in pr.scalars().all()}

    return {
        "id": quotation.id,
        "quotation_number": quotation.quotation_number,
        "customer_id": quotation.customer_id,
        "customer_name": customer_name,
        "quotation_date": quotation.quotation_date,
        "valid_until": quotation.valid_until,
        "status": quotation.status,
        "total_amount": float(quotation.total_amount or 0),
        "tax_amount": float(quotation.tax_amount or 0),
        "discount": float(quotation.discount or 0),
        "final_amount": float(quotation.final_amount or 0),
        "currency_code": quotation.currency_code,
        "payment_terms": quotation.payment_terms,
        "notes": quotation.notes,
        "sale_id": quotation.sale_id,
        "company_id": quotation.company_id,
        "branch_id": quotation.branch_id,
        "created_by": quotation.created_by,
        "created_at": quotation.created_at.isoformat() if quotation.created_at else None,
        "items": [
            {
                "id": i.id, "quotation_id": i.quotation_id, "product_id": i.product_id,
                "product_name": product_map.get(i.product_id, ""),
                "quantity": i.quantity, "unit_price": float(i.unit_price or 0),
                "discount": float(i.discount or 0), "tax_percent": float(i.tax_percent or 0),
                "tax_amount": float(i.tax_amount or 0), "total_price": float(i.total_price or 0),
            }
            for i in items
        ],
    }


async def _build_quotation_list(quotations: list, db: AsyncSession) -> list:
    result = []
    for q in quotations:
        items = (await db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q.id))).scalars().all()
        result.append(await _build_quotation(q, items, db))
    return result


@router.get("")
async def list_quotations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Quotation)
    count_query = select(func.count(Quotation.id))
    if search:
        query = query.where(Quotation.quotation_number.ilike(f"%{search}%"))
        count_query = count_query.where(Quotation.quotation_number.ilike(f"%{search}%"))
    if status:
        query = query.where(Quotation.status == status)
        count_query = count_query.where(Quotation.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(Quotation.id.desc()).offset(offset).limit(per_page))
    quotations = list(result.scalars().all())
    items = await _build_quotation_list(quotations, db)

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=_ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/{quotation_id}")
async def get_quotation(quotation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    q = (await db.execute(select(Quotation).where(Quotation.id == quotation_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    items = (await db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q.id))).scalars().all()
    return await _build_quotation(q, items, db)


@router.post("", response_model=dict)
async def create_quotation(data: QuotationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_QUOTATION"))):
    count = (await db.execute(select(func.count(Quotation.id)))).scalar() or 0
    q_number = f"QT-{datetime.now().year}-{count + 1:05d}"

    quotation = Quotation(
        quotation_number=q_number,
        customer_id=data.customer_id,
        quotation_date=data.quotation_date or datetime.now(UTC).replace(tzinfo=None),
        valid_until=data.valid_until,
        status="draft",
        total_amount=data.total_amount,
        tax_amount=data.tax_amount,
        discount=data.discount,
        final_amount=data.final_amount,
        currency_code=data.currency_code,
        payment_terms=data.payment_terms,
        notes=data.notes,
        company_id=data.company_id,
        branch_id=data.branch_id,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(quotation)
    await db.flush()

    for item in data.items:
        db.add(QuotationItem(
            quotation_id=quotation.id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            tax_percent=item.tax_percent,
            tax_amount=item.tax_amount,
            total_price=item.total_price,
        ))
    await db.flush()
    return {"id": quotation.id, "quotation_number": q_number, "message": "Quotation created"}


@router.put("/{quotation_id}", response_model=dict)
async def update_quotation(quotation_id: int, data: QuotationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_QUOTATION"))):
    q = (await db.execute(select(Quotation).where(Quotation.id == quotation_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if q.status not in ("draft", "rejected"):
        raise HTTPException(status_code=400, detail="Cannot edit a submitted/accepted quotation")

    await db.execute(update(Quotation).where(Quotation.id == quotation_id).values(
        customer_id=data.customer_id,
        quotation_date=data.quotation_date,
        valid_until=data.valid_until,
        total_amount=data.total_amount,
        tax_amount=data.tax_amount,
        discount=data.discount,
        final_amount=data.final_amount,
        currency_code=data.currency_code,
        payment_terms=data.payment_terms,
        notes=data.notes,
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.execute(delete(QuotationItem).where(QuotationItem.quotation_id == quotation_id))
    for item in data.items:
        db.add(QuotationItem(
            quotation_id=quotation_id,
            product_id=item.product_id,
            quantity=item.quantity,
            unit_price=item.unit_price,
            discount=item.discount,
            tax_percent=item.tax_percent,
            tax_amount=item.tax_amount,
            total_price=item.total_price,
        ))
    await db.flush()
    return {"message": "Quotation updated"}


@router.post("/{quotation_id}/submit", response_model=dict)
async def submit_quotation(quotation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_QUOTATION"))):
    q = (await db.execute(select(Quotation).where(Quotation.id == quotation_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if q.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft quotations can be submitted")
    await db.execute(update(Quotation).where(Quotation.id == quotation_id).values(status="submitted", updated_at=datetime.now(UTC).replace(tzinfo=None)))
    await db.flush()
    return {"message": "Quotation submitted"}


@router.post("/{quotation_id}/accept", response_model=dict)
async def accept_quotation(quotation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_QUOTATION"))):
    q = (await db.execute(select(Quotation).where(Quotation.id == quotation_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if q.status != "submitted":
        raise HTTPException(status_code=400, detail="Only submitted quotations can be accepted")
    await db.execute(update(Quotation).where(Quotation.id == quotation_id).values(status="accepted", updated_at=datetime.now(UTC).replace(tzinfo=None)))
    await db.flush()
    return {"message": "Quotation accepted"}


@router.post("/{quotation_id}/convert", response_model=dict)
async def convert_quotation_to_sale(
    quotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_QUOTATION")),
):
    """
    Convert an accepted quotation into a Sales invoice.
    Creates a Sale + SaleItems linked to the quotation, then marks it 'converted'.
    The sale can then go through its normal lifecycle (submit -> approve -> ledger entry).
    """
    q = (await db.execute(select(Quotation).where(Quotation.id == quotation_id))).scalar_one_or_none()
    if not q:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if q.status != "accepted":
        raise HTTPException(status_code=400, detail="Only accepted quotations can be converted")

    items = (await db.execute(select(QuotationItem).where(QuotationItem.quotation_id == q.id))).scalars().all()

    sale = Sale(
        customer_id=q.customer_id,
        total_amount=q.total_amount,
        discount=q.discount,
        final_amount=q.final_amount,
        tax_amount=q.tax_amount,
        payment_method="credit",
        payment_status="unpaid",
        workflow_state="draft",
        company_id=q.company_id,
        branch_id=q.branch_id,
        invoice_number="",
        notes=f"Converted from quotation {q.quotation_number}",
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(sale)
    await db.flush()

    sale.invoice_number = f"INV-{datetime.now().year}-{sale.id:06d}"

    for item in items:
        db.add(SaleItem(
            sale_id=sale.id,
            product_id=item.product_id,
            quantity=item.quantity or 0,
            unit_price=item.unit_price or 0,
            total_price=item.total_price or 0,
        ))

    await db.execute(update(Quotation).where(Quotation.id == quotation_id).values(
        status="converted", sale_id=sale.id, updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.flush()
    return {"id": sale.id, "invoice_number": sale.invoice_number, "message": "Quotation converted to sale"}
