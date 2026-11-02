"""
Generic, reusable Workflow Engine.

This engine turns the ad-hoc status checks scattered across routers into a
single declarative state machine. It is intentionally generic: every module
(sales, purchases, payroll, payments, budgets, cheques, ...) registers a
default transition graph keyed by ``entity_type``. Administrators can override
those defaults (change the required permission, add amount/branch conditions,
disable a transition) through the ``workflow_transitions`` table.

Usage
-----
    from app.services.workflow_engine import validate_transition
    await validate_transition(db, "SALE", sale.workflow_state, "approved",
                              amount=sale.final_amount, user=current_user)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workflow import WorkflowTransition


@dataclass(frozen=True)
class Transition:
    entity_type: str
    from_status: str
    to_status: str
    required_permission: Optional[str] = None
    requires_reason: bool = False
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    label: Optional[str] = None


_FULL_CHAIN = [
    ("draft", "submitted", None),
    ("submitted", "approved", None),
    ("submitted", "rejected", None),
    ("approved", "posted", None),
    ("approved", "voided", None),
    ("posted", "reversed", None),
    ("draft", "cancelled", None),
]

# Default transition graphs per entity type. Permissions mirror the ones the
# routers already enforce so behaviour is unchanged until an admin overrides it.
DEFAULT_WORKFLOWS: dict[str, list[Transition]] = {
    "SALE": [
        Transition("SALE", "draft", "submitted", "EDIT_SALE", label="Submit"),
        Transition("SALE", "submitted", "approved", "APPROVE_SALE", label="Approve"),
        Transition("SALE", "submitted", "rejected", "EDIT_SALE", label="Reject"),
        Transition("SALE", "approved", "cancelled", "APPROVE_SALE", label="Cancel"),
        Transition("SALE", "approved", "voided", "APPROVE_SALE", label="Void"),
    ],
    "PURCHASE": [
        Transition("PURCHASE", "draft", "submitted", "EDIT_PURCHASE", label="Submit"),
        Transition("PURCHASE", "submitted", "approved", "APPROVE_PURCHASE", label="Approve"),
        Transition("PURCHASE", "submitted", "rejected", "EDIT_PURCHASE", label="Reject"),
        Transition("PURCHASE", "approved", "voided", "APPROVE_PURCHASE", label="Void"),
    ],
    "PAYMENT": [
        Transition("PAYMENT", "draft", "submitted", "EDIT_PURCHASE", label="Submit"),
        Transition("PAYMENT", "submitted", "approved", "APPROVE_PURCHASE", label="Approve"),
        Transition("PAYMENT", "submitted", "rejected", "EDIT_PURCHASE", label="Reject"),
    ],
    "PAYROLL": [
        Transition("PAYROLL", "draft", "submitted", None, label="Submit"),
        Transition("PAYROLL", "submitted", "approved", None, label="Approve"),
        Transition("PAYROLL", "submitted", "rejected", None, label="Reject"),
        Transition("PAYROLL", "approved", "paid", None, label="Pay"),
    ],
    "BUDGET": [
        Transition("BUDGET", "draft", "submitted", "MANAGE_BUDGETS", label="Submit"),
        Transition("BUDGET", "submitted", "approved", "MANAGE_BUDGETS", label="Approve"),
        Transition("BUDGET", "submitted", "rejected", "MANAGE_BUDGETS", label="Reject"),
    ],
    "CHEQUE": [
        Transition("CHEQUE", "on_hand", "deposited", "MANAGE_CHEQUES", label="Deposit"),
        Transition("CHEQUE", "on_hand", "under_collection", "MANAGE_CHEQUES", label="Under collection"),
        Transition("CHEQUE", "on_hand", "cleared", "MANAGE_CHEQUES", label="Clear"),
        Transition("CHEQUE", "on_hand", "stopped", "MANAGE_CHEQUES", requires_reason=True, label="Stop"),
        Transition("CHEQUE", "on_hand", "cancelled", "MANAGE_CHEQUES", requires_reason=True, label="Cancel"),
        Transition("CHEQUE", "on_hand", "returned", "MANAGE_CHEQUES", requires_reason=True, label="Return"),
        Transition("CHEQUE", "on_hand", "replaced", "MANAGE_CHEQUES", requires_reason=True, label="Replace"),
        Transition("CHEQUE", "deposited", "under_collection", "MANAGE_CHEQUES", label="Under collection"),
        Transition("CHEQUE", "deposited", "cleared", "MANAGE_CHEQUES", label="Clear"),
        Transition("CHEQUE", "deposited", "returned", "MANAGE_CHEQUES", requires_reason=True, label="Return"),
        Transition("CHEQUE", "deposited", "cancelled", "MANAGE_CHEQUES", requires_reason=True, label="Cancel"),
        Transition("CHEQUE", "under_collection", "cleared", "MANAGE_CHEQUES", label="Clear"),
        Transition("CHEQUE", "under_collection", "returned", "MANAGE_CHEQUES", requires_reason=True, label="Return"),
        Transition("CHEQUE", "under_collection", "cancelled", "MANAGE_CHEQUES", requires_reason=True, label="Cancel"),
    ],
}


def _to_transition(row: WorkflowTransition) -> Transition:
    return Transition(
        entity_type=row.entity_type,
        from_status=row.from_status,
        to_status=row.to_status,
        required_permission=row.required_permission,
        requires_reason=bool(row.requires_reason),
        min_amount=float(row.min_amount) if row.min_amount is not None else None,
        max_amount=float(row.max_amount) if row.max_amount is not None else None,
        label=row.label,
    )


async def get_effective_transitions(
    db: AsyncSession, entity_type: str
) -> list[Transition]:
    """Return the effective transition list = defaults merged with DB overrides.

    A DB row with the same (from,to) replaces the default. A DB row with
    ``is_active`` false removes the transition entirely.
    """
    entity = entity_type.upper()
    defaults = {f"{t.from_status}->{t.to_status}": t for t in DEFAULT_WORKFLOWS.get(entity, [])}

    rows = (await db.execute(
        select(WorkflowTransition).where(WorkflowTransition.entity_type == entity)
    )).scalars().all()

    for row in rows:
        key = f"{row.from_status}->{row.to_status}"
        if row.is_active is False:
            defaults.pop(key, None)
        else:
            defaults[key] = _to_transition(row)

    return list(defaults.values())


async def get_transition(
    db: AsyncSession, entity_type: str, from_status: str, to_status: str
) -> Optional[Transition]:
    for t in await get_effective_transitions(db, entity_type):
        if t.from_status == from_status and t.to_status == to_status:
            return t
    return None


def _permission_ok(user, permission: Optional[str]) -> bool:
    if not permission:
        return True
    if user is None:
        return True
    if getattr(user, "role", None) in ("admin", "owner"):
        return True
    # When the caller does not expose a permissions list (legacy User shape),
    # defer permission enforcement to the endpoint's Depends(require_permission).
    # If a permissions list IS present, enforce it here.
    perms = getattr(user, "permissions", None)
    if not perms:
        return True
    return permission in perms


async def validate_transition(
    db: AsyncSession,
    entity_type: str,
    from_status: Optional[str],
    to_status: str,
    *,
    amount: Optional[float] = None,
    reason: Optional[str] = None,
    user=None,
    branch_id: Optional[int] = None,
) -> Transition:
    """Validate a state transition, raising HTTP 400/403 when it is not allowed."""
    from_status = from_status or "draft"
    transition = await get_transition(db, entity_type, from_status, to_status)
    if transition is None:
        allowed = sorted({
            t.to_status for t in await get_effective_transitions(db, entity_type)
            if t.from_status == from_status
        })
        raise HTTPException(
            status_code=400,
            detail=(
                f"Cannot transition {entity_type} from '{from_status}' to "
                f"'{to_status}'. Allowed: {allowed or 'none'}"
            ),
        )

    if amount is not None:
        if transition.min_amount is not None and amount < transition.min_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Amount {amount} is below the minimum ({transition.min_amount}) for this transition",
            )
        if transition.max_amount is not None and amount > transition.max_amount:
            raise HTTPException(
                status_code=400,
                detail=f"Amount {amount} exceeds the maximum ({transition.max_amount}) for this transition",
            )

    if transition.requires_reason and not reason:
        raise HTTPException(status_code=400, detail="A reason is required for this transition")

    if not _permission_ok(user, transition.required_permission):
        raise HTTPException(
            status_code=403,
            detail=f"Missing permission '{transition.required_permission}' for this transition",
        )
    return transition


async def available_transitions(
    db: AsyncSession, entity_type: str, from_status: Optional[str]
) -> list[Transition]:
    from_status = from_status or "draft"
    return [
        t for t in await get_effective_transitions(db, entity_type)
        if t.from_status == from_status
    ]


async def set_transition(
    db: AsyncSession,
    *,
    entity_type: str,
    from_status: str,
    to_status: str,
    required_permission: Optional[str] = None,
    requires_reason: bool = False,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    branch_id: Optional[int] = None,
    label: Optional[str] = None,
    is_active: bool = True,
    user_id: Optional[int] = None,
) -> WorkflowTransition:
    """Create or update a workflow transition override."""
    entity = entity_type.upper()
    row = (await db.execute(
        select(WorkflowTransition).where(
            WorkflowTransition.entity_type == entity,
            WorkflowTransition.from_status == from_status,
            WorkflowTransition.to_status == to_status,
        ).limit(1)
    )).scalar_one_or_none()

    now = datetime.now()
    if row is None:
        row = WorkflowTransition(
            entity_type=entity,
            from_status=from_status,
            to_status=to_status,
            created_at=now,
            created_by=user_id,
        )
        db.add(row)

    row.required_permission = required_permission
    row.requires_reason = requires_reason
    row.min_amount = min_amount
    row.max_amount = max_amount
    row.branch_id = branch_id
    row.label = label
    row.is_active = is_active
    row.updated_at = now
    await db.flush()
    return row
