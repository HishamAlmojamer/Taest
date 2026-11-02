import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.promotion import Promotion
from app.models.user import User
from app.schemas.promotions import PromotionCreate, PromotionUpdate
from app.schemas.common import PaginationResponse
from app.utils.deps import get_current_user, require_permission

logger = logging.getLogger(__name__)

router = APIRouter()


def _ceil(n: float) -> int:
    return int(n) + (1 if n % 1 > 0 else 0)


def _build_promotion(p: Promotion) -> dict:
    now = datetime.now(UTC).replace(tzinfo=None)
    status = p.status or "active"
    if p.is_active and p.start_date and p.start_date > now:
        status = "scheduled"
    elif p.is_active and p.end_date and p.end_date < now:
        status = "expired"
    elif not p.is_active:
        status = "paused"
    return {
        "id": p.id,
        "code": p.code,
        "name": p.name,
        "description": p.description,
        "promo_type": p.promo_type,
        "discount_value": float(p.discount_value or 0),
        "applies_to": p.applies_to,
        "target_id": p.target_id,
        "target_name": p.target_name,
        "min_purchase": float(p.min_purchase or 0),
        "max_discount": float(p.max_discount) if p.max_discount is not None else None,
        "start_date": p.start_date.isoformat() if p.start_date else None,
        "end_date": p.end_date.isoformat() if p.end_date else None,
        "status": status,
        "is_active": p.is_active,
        "usage_limit": p.usage_limit,
        "used_count": p.used_count or 0,
        "priority": p.priority or 0,
        "company_id": p.company_id,
        "branch_id": p.branch_id,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


@router.get("")
async def list_promotions(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Promotion)
    count_query = select(func.count(Promotion.id))
    if search:
        like = f"%{search}%"
        query = query.where(Promotion.name.ilike(like) | Promotion.code.ilike(like))
        count_query = count_query.where(Promotion.name.ilike(like) | Promotion.code.ilike(like))
    if status:
        query = query.where(Promotion.status == status)
        count_query = count_query.where(Promotion.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(Promotion.id.desc()).offset(offset).limit(per_page))
    items = [_build_promotion(p) for p in result.scalars().all()]

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=_ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/{promotion_id}")
async def get_promotion(promotion_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    p = (await db.execute(select(Promotion).where(Promotion.id == promotion_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion not found")
    return _build_promotion(p)


@router.post("", response_model=dict)
async def create_promotion(data: PromotionCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROMOTIONS"))):
    now = datetime.now(UTC).replace(tzinfo=None)
    status = "active" if data.is_active else "paused"
    if data.is_active and data.start_date and data.start_date > now:
        status = "scheduled"

    promotion = Promotion(
        code=data.code,
        name=data.name,
        description=data.description,
        promo_type=data.promo_type,
        discount_value=data.discount_value,
        applies_to=data.applies_to,
        target_id=data.target_id,
        target_name=data.target_name,
        min_purchase=data.min_purchase,
        max_discount=data.max_discount,
        start_date=data.start_date,
        end_date=data.end_date,
        status=status,
        is_active=data.is_active,
        usage_limit=data.usage_limit,
        used_count=0,
        priority=data.priority,
        company_id=data.company_id,
        branch_id=data.branch_id,
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
    )
    db.add(promotion)
    await db.flush()
    return {"id": promotion.id, "message": "Promotion created"}


@router.put("/{promotion_id}", response_model=dict)
async def update_promotion(promotion_id: int, data: PromotionUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROMOTIONS"))):
    p = (await db.execute(select(Promotion).where(Promotion.id == promotion_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion not found")

    values = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    values["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
    if "is_active" in values:
        values["status"] = "active" if values["is_active"] else "paused"
    await db.execute(update(Promotion).where(Promotion.id == promotion_id).values(**values))
    await db.flush()
    return {"message": "Promotion updated"}


@router.post("/{promotion_id}/toggle", response_model=dict)
async def toggle_promotion(promotion_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROMOTIONS"))):
    p = (await db.execute(select(Promotion).where(Promotion.id == promotion_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion not found")
    new_active = not bool(p.is_active)
    await db.execute(update(Promotion).where(Promotion.id == promotion_id).values(
        is_active=new_active,
        status="active" if new_active else "paused",
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.flush()
    return {"message": "Promotion status updated", "is_active": new_active}


@router.delete("/{promotion_id}", response_model=dict)
async def delete_promotion(promotion_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROMOTIONS"))):
    p = (await db.execute(select(Promotion).where(Promotion.id == promotion_id))).scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Promotion not found")
    await db.execute(delete(Promotion).where(Promotion.id == promotion_id))
    await db.flush()
    return {"message": "Promotion deleted"}