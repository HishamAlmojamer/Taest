import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete, or_
from app.database import get_db
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notifications import NotificationCreate
from app.schemas.common import PaginationResponse
from app.utils.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter()


def _ceil(n: float) -> int:
    return int(n) + (1 if n % 1 > 0 else 0)


def _build_notification(n: Notification) -> dict:
    return {
        "id": n.id,
        "user_id": n.user_id,
        "title": n.title,
        "message": n.message,
        "notification_type": n.notification_type,
        "link": n.link,
        "is_read": bool(n.is_read),
        "read_at": n.read_at.isoformat() if n.read_at else None,
        "company_id": n.company_id,
        "created_at": n.created_at.isoformat() if n.created_at else None,
    }


@router.get("")
async def list_notifications(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    notification_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    base = or_(
        Notification.user_id == current_user.id,
        Notification.user_id.is_(None),
    )
    query = select(Notification).where(base)
    count_query = select(func.count(Notification.id)).where(base)
    if unread_only:
        query = query.where(Notification.is_read.is_(False))
        count_query = count_query.where(Notification.is_read.is_(False))
    if notification_type:
        query = query.where(Notification.notification_type == notification_type)
        count_query = count_query.where(Notification.notification_type == notification_type)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    result = await db.execute(query.order_by(Notification.created_at.desc()).offset(offset).limit(per_page))
    items = [_build_notification(n) for n in result.scalars().all()]

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=_ceil(total / per_page) if total else 0, items=items,
    )


@router.get("/unread-count")
async def unread_count(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = or_(
        Notification.user_id == current_user.id,
        Notification.user_id.is_(None),
    )
    count = (await db.execute(
        select(func.count(Notification.id)).where(base, Notification.is_read.is_(False))
    )).scalar() or 0
    return {"count": count}


@router.post("", response_model=dict)
async def create_notification(data: NotificationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = Notification(
        user_id=data.user_id,
        title=data.title,
        message=data.message,
        notification_type=data.notification_type,
        link=data.link,
        is_read=False,
        company_id=data.company_id,
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(n)
    await db.flush()
    return {"id": n.id, "message": "Notification created"}


@router.post("/{notification_id}/read", response_model=dict)
async def mark_as_read(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = (await db.execute(select(Notification).where(Notification.id == notification_id))).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.execute(update(Notification).where(Notification.id == notification_id).values(
        is_read=True, read_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.flush()
    return {"message": "Notification marked as read"}


@router.post("/read-all", response_model=dict)
async def mark_all_as_read(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    base = or_(
        Notification.user_id == current_user.id,
        Notification.user_id.is_(None),
    )
    await db.execute(update(Notification).where(base, Notification.is_read.is_(False)).values(
        is_read=True, read_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.flush()
    return {"message": "All notifications marked as read"}


@router.delete("/{notification_id}", response_model=dict)
async def delete_notification(notification_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    n = (await db.execute(select(Notification).where(Notification.id == notification_id))).scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Notification not found")
    await db.execute(delete(Notification).where(Notification.id == notification_id))
    await db.flush()
    return {"message": "Notification deleted"}