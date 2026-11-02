from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.models.audit import AuditLog
from app.utils.deps import get_current_user

router = APIRouter()


@router.get("/logs")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(AuditLog)

    if action:
        query = query.where(AuditLog.action == action)
    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format, expected ISO datetime")
        query = query.where(AuditLog.created_at >= start_dt)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format, expected ISO datetime")
        query = query.where(AuditLog.created_at <= end_dt)

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(desc(AuditLog.created_at))
    query = query.offset((page - 1) * per_page).limit(per_page)

    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "changes_json": log.changes_json,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "ip_address": log.ip_address,
                "company_id": log.company_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    }


@router.get("/logs/{log_id}")
async def get_audit_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = select(AuditLog).where(AuditLog.id == log_id)
    result = await db.execute(query)
    log = result.scalar_one_or_none()

    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return {
        "id": log.id,
        "entity_type": log.entity_type,
        "entity_id": log.entity_id,
        "action": log.action,
        "changes_json": log.changes_json,
        "user_id": log.user_id,
        "user_name": log.user_name,
        "ip_address": log.ip_address,
        "company_id": log.company_id,
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


@router.get("/logs/entity/{entity_type}/{entity_id}")
async def get_audit_logs_by_entity(
    entity_type: str,
    entity_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = (
        select(AuditLog)
        .where(AuditLog.entity_type == entity_type, AuditLog.entity_id == entity_id)
        .order_by(desc(AuditLog.created_at))
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "changes_json": log.changes_json,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }


@router.get("/logs/user/{user_id}")
async def get_audit_logs_by_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    query = (
        select(AuditLog)
        .where(AuditLog.user_id == user_id)
        .order_by(desc(AuditLog.created_at))
    )
    result = await db.execute(query)
    logs = result.scalars().all()

    return {
        "logs": [
            {
                "id": log.id,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "action": log.action,
                "changes_json": log.changes_json,
                "user_id": log.user_id,
                "user_name": log.user_name,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ]
    }
