"""
Cheques Router — CRUD + lifecycle management for issued and received cheques.

Lifecycle:
  on_hand → deposited → under_collection → cleared
  on_hand → stopped | cancelled | returned | replaced

Accounting events are emitted to the Node.js Gateway Ledger Engine via
the event_emitter module.
"""

import logging
from datetime import datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.cheques import Cheque
from app.models.payments import Bank
from app.models.user import User
from app.services.numbering_service import generate_next_number
from app.utils.deps import get_current_user, require_permission
from app.utils.event_emitter import (
    _base_currency_code,
    emit_cheque_received,
    emit_cheque_issued,
    emit_cheque_deposited,
    emit_cheque_cleared,
    emit_cheque_returned,
)

logger = logging.getLogger(__name__)
router = APIRouter()

_VALID_TRANSITIONS = {
    "on_hand":    {"deposited", "under_collection", "cleared", "stopped", "cancelled", "returned", "replaced"},
    "deposited":  {"under_collection", "cleared", "returned", "cancelled"},
    "under_collection": {"cleared", "returned", "cancelled"},
    "cleared":    set(),
    "returned":   set(),
    "stopped":    set(),
    "cancelled":  set(),
    "replaced":   set(),
}


def _extract_entry_id(event_result) -> Optional[int]:
    results = (event_result.get("data") or {}).get("results") or []
    for r in results:
        if isinstance(r, dict) and r.get("entryId"):
            return int(r["entryId"])
    return None


# ──────────────────── LIST ────────────────────

@router.get("")
async def list_cheques(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    cheque_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    bank_id: Optional[int] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    conditions = []
    if cheque_type:
        conditions.append(Cheque.cheque_type == cheque_type)
    if status:
        conditions.append(Cheque.status == status)
    if bank_id:
        conditions.append(Cheque.bank_id == bank_id)
    if search:
        conditions.append(
            Cheque.cheque_number.ilike(f"%{search}%")
            | Cheque.payer_name.ilike(f"%{search}%")
            | Cheque.payee_name.ilike(f"%{search}%")
        )
    if current_user.role != "admin" and current_user.company_id:
        conditions.append(Cheque.company_id == current_user.company_id)

    where = and_(*conditions) if conditions else True

    count_q = select(func.count()).select_from(Cheque).where(where)
    total = (await db.execute(count_q)).scalar() or 0

    offset = (page - 1) * per_page
    q = (
        select(Cheque)
        .where(where)
        .order_by(Cheque.created_at.desc().nullslast(), Cheque.id.desc())
        .offset(offset)
        .limit(per_page)
    )
    result = await db.execute(q)
    items = result.scalars().all()

    return {
        "items": [_serialize(c) for c in items],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, (total + per_page - 1) // per_page),
    }


@router.get("/{cheque_id}")
async def get_cheque(
    cheque_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    c = await db.get(Cheque, cheque_id)
    if not c:
        raise HTTPException(status_code=404, detail="Cheque not found")
    return _serialize(c)


# ──────────────────── CREATE ────────────────────

@router.post("")
async def create_cheque(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_CHEQUES")),
):
    cheque_type = data.get("cheque_type")
    if cheque_type not in ("received", "issued"):
        raise HTTPException(status_code=400, detail="cheque_type must be 'received' or 'issued'")

    amount = data.get("amount")
    if not amount or float(amount) <= 0:
        raise HTTPException(status_code=400, detail="amount must be positive")

    cheque_number = data.get("cheque_number", "")
    if not cheque_number:
        cheque_number = await generate_next_number(
            db, "CHEQUE",
            name="Cheque", name_ar="شيك", prefix="CHQ", zero_padding=6, include_year=True,
        )

    now = datetime.now(UTC).replace(tzinfo=None)

    cheque = Cheque(
        cheque_number=cheque_number,
        cheque_type=cheque_type,
        amount=float(amount),
        currency_code=data.get("currency_code") or await _base_currency_code(),
        exchange_rate=float(data.get("exchange_rate", 1)),
        payer_name=data.get("payer_name"),
        payee_name=data.get("payee_name"),
        customer_id=data.get("customer_id"),
        supplier_id=data.get("supplier_id"),
        bank_id=data.get("bank_id"),
        bank_name=data.get("bank_name"),
        bank_branch=data.get("bank_branch"),
        issue_date=_parse_date(data.get("issue_date")),
        due_date=_parse_date(data.get("due_date")),
        status="on_hand",
        description=data.get("description"),
        reference_type=data.get("reference_type"),
        reference_id=data.get("reference_id"),
        created_by=current_user.id,
        created_at=now,
        updated_at=now,
        company_id=current_user.company_id,
    )
    db.add(cheque)
    await db.flush()

    # Ensure the fiscal period for the cheque posting is open
    from app.services.fiscal_period_guard import check_period_open
    post_date = cheque.issue_date or cheque.due_date or now
    await check_period_open(db, post_date, None)

    # Emit accounting event. A failure here must abort the cheque creation so
    # no cheque is stored without its ledger entry.
    if cheque_type == "received":
        event = await emit_cheque_received(
            cheque_id=cheque.id,
            cheque_number=cheque.cheque_number,
            amount=cheque.amount,
            customer_id=cheque.customer_id,
            customer_name=data.get("customer_name"),
            payer_name=cheque.payer_name,
            bank_name=cheque.bank_name,
            due_date=str(cheque.due_date.date()) if cheque.due_date else None,
            user_id=current_user.id,
            company_id=current_user.company_id,
        )
    else:
        event = await emit_cheque_issued(
            cheque_id=cheque.id,
            cheque_number=cheque.cheque_number,
            amount=cheque.amount,
            supplier_id=cheque.supplier_id,
            supplier_name=data.get("supplier_name"),
            payee_name=cheque.payee_name,
            bank_name=cheque.bank_name,
            due_date=str(cheque.due_date.date()) if cheque.due_date else None,
            user_id=current_user.id,
            company_id=current_user.company_id,
        )
    entry_id = _extract_entry_id(event)
    if entry_id:
        cheque.journal_entry_id = entry_id
        await db.flush()

    return {"id": cheque.id, "cheque_number": cheque.cheque_number, "message": "Cheque created"}


# ──────────────────── UPDATE ────────────────────

@router.put("/{cheque_id}")
async def update_cheque(
    cheque_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_CHEQUES")),
):
    cheque = await db.get(Cheque, cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")
    if cheque.status not in ("on_hand",):
        raise HTTPException(status_code=400, detail="Cannot update cheque in current status")

    updatable = [
        "cheque_number", "payer_name", "payee_name", "customer_id", "supplier_id",
        "bank_id", "bank_name", "bank_branch", "issue_date", "due_date", "description",
    ]
    for field in updatable:
        if field in data:
            val = data[field]
            if field in ("issue_date", "due_date"):
                val = _parse_date(val)
            setattr(cheque, field, val)

    cheque.updated_by = current_user.id
    cheque.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return {"message": "Cheque updated"}


# ──────────────────── LIFECYCLE TRANSITIONS ────────────────────

@router.post("/{cheque_id}/transition")
async def transition_cheque(
    cheque_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_CHEQUES")),
):
    """Transition a cheque to a new status with optional accounting event."""
    new_status = data.get("status")
    reason = data.get("reason")

    cheque = await db.get(Cheque, cheque_id)
    if not cheque:
        raise HTTPException(status_code=404, detail="Cheque not found")

    allowed = _VALID_TRANSITIONS.get(cheque.status, set())
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{cheque.status}' to '{new_status}'. Allowed: {sorted(allowed)}",
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    previous_status = cheque.status

    # Ensure the fiscal period for the posting is open before any accounting side effect
    from app.services.fiscal_period_guard import check_period_open
    if new_status in ("deposited", "cleared", "returned"):
        await check_period_open(db, now, None)

    # Side effects per transition
    if new_status == "deposited":
        cheque.deposit_date = _parse_date(data.get("deposit_date")) or now
        cheque.bank_id = data.get("bank_id") or cheque.bank_id
        cheque.bank_name = data.get("bank_name") or cheque.bank_name
        # Emit deposit event (received cheques only)
        if cheque.cheque_type == "received":
            event = await emit_cheque_deposited(
                cheque_id=cheque.id,
                cheque_number=cheque.cheque_number,
                amount=cheque.amount,
                bank_id=cheque.bank_id,
                bank_name=cheque.bank_name,
                user_id=current_user.id,
                company_id=current_user.company_id,
            )
            entry_id = _extract_entry_id(event)
            if entry_id:
                cheque.journal_entry_id = entry_id

    elif new_status == "cleared":
        cheque.clear_date = _parse_date(data.get("clear_date")) or now
        # Emit clear event for issued cheques (Dr Cheques-Issued / Cr Bank)
        if cheque.cheque_type == "issued":
            event = await emit_cheque_cleared(
                cheque_id=cheque.id,
                cheque_number=cheque.cheque_number,
                amount=cheque.amount,
                cheque_type=cheque.cheque_type,
                user_id=current_user.id,
                company_id=current_user.company_id,
            )
            entry_id = _extract_entry_id(event)
            if entry_id:
                cheque.reversal_entry_id = entry_id

    elif new_status == "returned":
        cheque.status_reason = reason
        # Emit return event (reverses original posting)
        event = await emit_cheque_returned(
            cheque_id=cheque.id,
            cheque_number=cheque.cheque_number,
            amount=cheque.amount,
            cheque_type=cheque.cheque_type,
            reason=reason,
            original_entry_id=cheque.journal_entry_id,
            pre_status=previous_status,
            user_id=current_user.id,
            company_id=current_user.company_id,
        )
        entry_id = _extract_entry_id(event)
        if entry_id:
            cheque.reversal_entry_id = entry_id

    elif new_status in ("stopped", "cancelled"):
        cheque.status_reason = reason

    elif new_status == "replaced":
        new_cheque_id = data.get("replaced_by_cheque_id")
        if not new_cheque_id:
            raise HTTPException(status_code=400, detail="replaced_by_cheque_id is required for replacement")
        cheque.replaced_by_cheque_id = new_cheque_id
        cheque.status_reason = reason

    cheque.status = new_status
    cheque.updated_by = current_user.id
    cheque.updated_at = now
    await db.flush()

    # Audit log
    try:
        import json
        from app.models.audit import AuditLog
        audit = AuditLog(
            user_id=current_user.id,
            user_name=current_user.username,
            entity_type="Cheque",
            entity_id=cheque.id,
            action=f"TRANSITION_{new_status.upper()}",
            changes_json=json.dumps({
                "cheque_number": cheque.cheque_number,
                "from_status": previous_status,
                "to_status": new_status,
                "reason": reason,
            }, ensure_ascii=False),
            created_at=now,
            company_id=current_user.company_id,
        )
        db.add(audit)
    except Exception as e:
        logger.warning("Audit log for cheque transition failed: %s", e)

    return {"message": f"Cheque transitioned to '{new_status}'", "status": new_status}


# ──────────────────── BULK OPERATIONS ────────────────────

@router.post("/bulk-deposit")
async def bulk_deposit(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_CHEQUES")),
):
    """Deposit multiple received cheques to a bank account."""
    cheque_ids = data.get("cheque_ids", [])
    bank_id = data.get("bank_id")
    if not cheque_ids or not bank_id:
        raise HTTPException(status_code=400, detail="cheque_ids and bank_id required")

    bank = await db.get(Bank, bank_id)
    bank_name = bank.bank_name if bank else None
    deposited = 0

    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime.now(), None)

    for cid in cheque_ids:
        cheque = await db.get(Cheque, cid)
        if cheque and cheque.cheque_type == "received" and cheque.status == "on_hand":
            now = datetime.now(UTC).replace(tzinfo=None)
            cheque.status = "deposited"
            cheque.deposit_date = now
            cheque.bank_id = bank_id
            cheque.bank_name = bank_name
            cheque.updated_by = current_user.id
            cheque.updated_at = now
            deposited += 1
            event = await emit_cheque_deposited(
                cheque_id=cheque.id,
                cheque_number=cheque.cheque_number,
                amount=cheque.amount,
                bank_id=bank_id,
                bank_name=bank_name,
                user_id=current_user.id,
                company_id=current_user.company_id,
            )
            entry_id = _extract_entry_id(event)
            if entry_id:
                cheque.journal_entry_id = entry_id

    await db.flush()
    return {"deposited": deposited, "message": f"Deposited {deposited} cheques"}


# ──────────────────── SUMMARY ────────────────────

@router.get("/summary/counts")
async def cheque_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return counts by status and type."""
    conditions = []
    if current_user.role != "admin" and current_user.company_id:
        conditions.append(Cheque.company_id == current_user.company_id)
    where = and_(*conditions) if conditions else True

    q = (
        select(Cheque.cheque_type, Cheque.status, func.count())
        .where(where)
        .group_by(Cheque.cheque_type, Cheque.status)
    )
    result = await db.execute(q)
    rows = result.all()

    summary = {"received": {}, "issued": {}}
    for cheque_type, status, count in rows:
        summary.setdefault(cheque_type, {})[status] = count
    return summary


# ──────────────────── HELPERS ────────────────────

def _serialize(c: Cheque) -> dict:
    return {
        "id": c.id,
        "cheque_number": c.cheque_number,
        "cheque_type": c.cheque_type,
        "amount": c.amount,
        "currency_code": c.currency_code,
        "payer_name": c.payer_name,
        "payee_name": c.payee_name,
        "customer_id": c.customer_id,
        "supplier_id": c.supplier_id,
        "bank_id": c.bank_id,
        "bank_name": c.bank_name,
        "bank_branch": c.bank_branch,
        "issue_date": str(c.issue_date.date()) if c.issue_date else None,
        "due_date": str(c.due_date.date()) if c.due_date else None,
        "deposit_date": str(c.deposit_date.date()) if c.deposit_date else None,
        "clear_date": str(c.clear_date.date()) if c.clear_date else None,
        "status": c.status,
        "status_reason": c.status_reason,
        "replaced_by_cheque_id": c.replaced_by_cheque_id,
        "journal_entry_id": c.journal_entry_id,
        "reversal_entry_id": c.reversal_entry_id,
        "reference_type": c.reference_type,
        "reference_id": c.reference_id,
        "description": c.description,
        "created_by": c.created_by,
        "created_at": str(c.created_at) if c.created_at else None,
        "updated_at": str(c.updated_at) if c.updated_at else None,
        "company_id": c.company_id,
    }


def _parse_date(val):
    if not val:
        return None
    if isinstance(val, datetime):
        return val
    try:
        return datetime.fromisoformat(str(val))
    except (ValueError, TypeError):
        return None
