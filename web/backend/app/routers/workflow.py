"""
Workflow Management API — generic, reusable across all modules.

GET  /definitions            — list all entity types with default transition chains
GET  /{entity_type}          — effective transitions (defaults + DB overrides)
POST /{entity_type}          — create / update a transition override
POST /validate               — dry-run validation (no state change)
GET  /{entity_type}/{from}/{to}/options  — metadata for a specific transition
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.services import workflow_engine
from app.utils.audit import add_audit_log
from app.utils.deps import get_current_user, require_permission

router = APIRouter()


def _t_dict(t):
    return {
        "entity_type": t.entity_type,
        "from_status": t.from_status,
        "to_status": t.to_status,
        "required_permission": t.required_permission,
        "requires_reason": t.requires_reason,
        "min_amount": t.min_amount,
        "max_amount": t.max_amount,
        "label": t.label,
    }


@router.get("/definitions")
async def list_definitions(current_user: User = Depends(get_current_user)):
    return [
        {
            "entity_type": entity,
            "default_transitions": [_t_dict(t) for t in chain],
        }
        for entity, chain in workflow_engine.DEFAULT_WORKFLOWS.items()
    ]


@router.get("/entity-types")
async def entity_types(current_user: User = Depends(get_current_user)):
    return sorted(workflow_engine.DEFAULT_WORKFLOWS.keys())


@router.get("/available")
async def available_for(
    entity_type: str = Query(...),
    from_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transitions = await workflow_engine.available_transitions(db, entity_type, from_status)
    return [_t_dict(t) for t in transitions]


@router.get("/{entity_type}")
async def get_effective(
    entity_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    transitions = await workflow_engine.get_effective_transitions(db, entity_type)
    return {"entity_type": entity_type, "transitions": [_t_dict(t) for t in transitions]}


@router.post("/validate")
async def validate_endpoint(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    entity_type = data.get("entity_type")
    from_status = data.get("from_status", "draft")
    to_status = data.get("to_status")
    amount = data.get("amount")
    reason = data.get("reason")

    if not to_status:
        raise HTTPException(status_code=400, detail="to_status is required")

    transition = await workflow_engine.validate_transition(
        db, entity_type, from_status, to_status,
        amount=amount, reason=reason, user=current_user,
    )
    return {
        "valid": True,
        "transition": _t_dict(transition),
        "message": "Transition is allowed",
    }


@router.post("/{entity_type}")
async def upsert_transition(
    entity_type: str,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_WORKFLOW")),
):
    try:
        from_status = data["from_status"]
        to_status = data["to_status"]
    except KeyError:
        raise HTTPException(status_code=400, detail="from_status and to_status are required")

    rule = await workflow_engine.set_transition(
        db,
        entity_type=entity_type,
        from_status=from_status,
        to_status=to_status,
        required_permission=data.get("required_permission"),
        requires_reason=bool(data.get("requires_reason", False)),
        min_amount=data.get("min_amount"),
        max_amount=data.get("max_amount"),
        branch_id=data.get("branch_id"),
        label=data.get("label"),
        is_active=bool(data.get("is_active", True)),
        user_id=current_user.id,
    )

    await add_audit_log(
        db, "WorkflowTransition", rule.id, "UPSERT", current_user,
        {
            "entity_type": entity_type,
            "from_status": from_status,
            "to_status": to_status,
            "changes": list(data.keys()),
        },
    )
    await db.commit()

    return {"id": rule.id, "message": f"Workflow rule {entity_type} {from_status}→{to_status} saved"}


@router.get("/{entity_type}/{from_status}/{to_status}/options")
async def transition_options(
    entity_type: str,
    from_status: str,
    to_status: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t = await workflow_engine.get_transition(db, entity_type.upper(), from_status, to_status)
    if t is None:
        raise HTTPException(status_code=404, detail="Transition not found")
    return _t_dict(t)
