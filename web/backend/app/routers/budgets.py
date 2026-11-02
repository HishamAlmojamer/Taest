"""
Budget Management endpoints with budget vs actual comparison.
"""

from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.budget import GLBudget
from app.models.accounting import Account, JournalEntry, JournalEntryLine, FiscalPeriod
from app.routers.accounting import _LEDGER_STATUSES
from app.schemas.budgets import BudgetCreate
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log

router = APIRouter()


@router.get("/")
async def list_budgets(
    fiscal_period_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all GL budgets"""
    query = select(GLBudget).order_by(GLBudget.account_id)
    if fiscal_period_id:
        query = query.where(GLBudget.fiscal_period_id == fiscal_period_id)
    if account_id:
        query = query.where(GLBudget.account_id == account_id)
    if company_id:
        query = query.where(GLBudget.company_id == company_id)
    result = await db.execute(query)
    budgets = result.scalars().all()
    return [{"id": b.id, "account_id": b.account_id, "fiscal_period_id": b.fiscal_period_id,
             "budget_amount": b.budget_amount, "actual_amount": b.actual_amount,
             "variance": b.variance, "notes": b.notes, "status": b.status} for b in budgets]


@router.post("/")
async def create_budget(
    data: BudgetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_BUDGETS")),
):
    """Create a new budget entry"""
    # Check if budget already exists for this account and period
    existing = await db.execute(
        select(GLBudget)
        .where(GLBudget.account_id == data.account_id)
        .where(GLBudget.fiscal_period_id == data.fiscal_period_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Budget already exists for this account and period")

    budget = GLBudget(
        account_id=data.account_id,
        fiscal_period_id=data.fiscal_period_id,
        budget_amount=data.budget_amount,
        actual_amount=0.0,
        variance=data.budget_amount,
        notes=data.notes,
        company_id=data.company_id,
        status="DRAFT",
        created_at=datetime.now(),
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    await add_audit_log(db, "GLBudget", budget.id, "CREATE", current_user,
                        {"account_id": budget.account_id, "amount": budget.budget_amount})
    await db.commit()
    return {"id": budget.id, "message": "Budget created"}


@router.put("/{budget_id}")
async def update_budget(
    budget_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_BUDGETS")),
):
    """Update a budget entry"""
    result = await db.execute(select(GLBudget).where(GLBudget.id == budget_id))
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if budget.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Cannot update approved budget")

    for key, value in data.items():
        if hasattr(budget, key) and key not in ["id", "created_at", "actual_amount"]:
            setattr(budget, key, value)
    budget.updated_at = datetime.now()
    await db.commit()
    return {"success": True, "message": "Budget updated"}


@router.post("/{budget_id}/approve")
async def approve_budget(
    budget_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_BUDGETS")),
):
    """Approve a budget"""
    result = await db.execute(select(GLBudget).where(GLBudget.id == budget_id))
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")

    budget.status = "APPROVED"
    budget.approved_by = current_user.id if hasattr(current_user, "id") else None
    budget.approved_at = datetime.now()
    await db.commit()
    await db.refresh(budget)
    await add_audit_log(db, "GLBudget", budget.id, "APPROVE", current_user,
                        {"account_id": budget.account_id, "amount": budget.budget_amount})
    await db.commit()
    return {"success": True, "message": "Budget approved"}


@router.get("/vs-actual")
async def get_budget_vs_actual(
    fiscal_period_id: int = Query(...),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Compare budget vs actual amounts for a fiscal period.
    """
    # Get fiscal period
    period_result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == fiscal_period_id))
    period = period_result.scalar_one_or_none()
    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    # Get budgets for this period
    budget_conditions = [GLBudget.fiscal_period_id == fiscal_period_id]
    if company_id:
        budget_conditions.append(GLBudget.company_id == company_id)

    budgets_result = await db.execute(
        select(GLBudget).where(and_(*budget_conditions))
    )
    budgets = budgets_result.scalars().all()

    results = []
    for budget in budgets:
        # Get actual amount from journal entries
        actual_conditions = [
            JournalEntry.status.in_(_LEDGER_STATUSES),
            JournalEntry.entry_date >= period.start_date,
            JournalEntry.entry_date <= period.end_date,
        ]
        if company_id:
            actual_conditions.append(JournalEntry.company_id == company_id)

        actual_result = await db.execute(
            select(
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id == budget.account_id)
            .where(and_(*actual_conditions))
        )
        actual = actual_result.one_or_none()

        # Get account info
        account_result = await db.execute(select(Account).where(Account.id == budget.account_id))
        account = account_result.scalar_one_or_none()

        total_debit = float(actual.total_debit if actual else 0)
        total_credit = float(actual.total_credit if actual else 0)

        # For expense accounts, actual = debits - credits
        # For revenue accounts, actual = credits - debits
        if account and account.account_type == "revenue":
            actual_amount = total_credit - total_debit
        else:
            actual_amount = total_debit - total_credit

        variance = budget.budget_amount - actual_amount
        variance_percent = (variance / budget.budget_amount * 100) if budget.budget_amount != 0 else 0

        results.append({
            "budget_id": budget.id,
            "account_id": budget.account_id,
            "account_code": account.account_code if account else None,
            "account_name": account.account_name if account else None,
            "budget_amount": budget.budget_amount,
            "actual_amount": round(actual_amount, 4),
            "variance": round(variance, 4),
            "variance_percent": round(variance_percent, 2),
            "is_over_budget": variance < 0,
        })

    return {
        "fiscal_period": {"id": period.id, "name": period.name},
        "budgets": results,
        "total_budget": round(sum(r["budget_amount"] for r in results), 4),
        "total_actual": round(sum(r["actual_amount"] for r in results), 4),
    }


@router.get("/alerts")
async def get_budget_alerts(
    threshold_percent: float = Query(80.0),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Get budget alerts where actual spending exceeds threshold % of budget.
    """
    # Get current fiscal period
    today = datetime.now().date()
    period_result = await db.execute(
        select(FiscalPeriod)
        .where(FiscalPeriod.start_date <= today)
        .where(FiscalPeriod.end_date >= today)
        .where(FiscalPeriod.is_closed == False)
        .limit(1)
    )
    period = period_result.scalar_one_or_none()
    if not period:
        return {"alerts": [], "message": "No active fiscal period"}

    # Get budgets with actual comparison
    budget_conditions = [GLBudget.fiscal_period_id == period.id, GLBudget.status == "APPROVED"]
    if company_id:
        budget_conditions.append(GLBudget.company_id == company_id)

    budgets_result = await db.execute(
        select(GLBudget).where(and_(*budget_conditions))
    )
    budgets = budgets_result.scalars().all()

    alerts = []
    for budget in budgets:
        # Get actual amount
        actual_conditions = [
            JournalEntry.status.in_(_LEDGER_STATUSES),
            JournalEntry.entry_date >= period.start_date,
            JournalEntry.entry_date <= period.end_date,
        ]
        if company_id:
            actual_conditions.append(JournalEntry.company_id == company_id)

        actual_result = await db.execute(
            select(
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            )
            .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id == budget.account_id)
            .where(and_(*actual_conditions))
        )
        actual = actual_result.one_or_none()

        total_debit = float(actual.total_debit if actual else 0)
        total_credit = float(actual.total_credit if actual else 0)
        actual_amount = total_debit - total_credit  # Simplified for expenses

        if budget.budget_amount > 0:
            usage_percent = (actual_amount / budget.budget_amount) * 100
            if usage_percent >= threshold_percent:
                # Get account info
                account_result = await db.execute(select(Account).where(Account.id == budget.account_id))
                account = account_result.scalar_one_or_none()

                alerts.append({
                    "account_code": account.account_code if account else None,
                    "account_name": account.account_name if account else None,
                    "budget_amount": budget.budget_amount,
                    "actual_amount": round(actual_amount, 4),
                    "usage_percent": round(usage_percent, 2),
                    "remaining": round(budget.budget_amount - actual_amount, 4),
                    "severity": "CRITICAL" if usage_percent >= 100 else "WARNING",
                })

    return {"alerts": alerts, "threshold_percent": threshold_percent}


@router.post("/{budget_id}/reject")
async def reject_budget(budget_id: int, data: dict = {}, db: AsyncSession = Depends(get_db), current_user=Depends(require_permission("MANAGE_BUDGETS"))):
    from app.models.budget import GLBudget
    result = await db.execute(select(GLBudget).where(GLBudget.id == budget_id))
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    if budget.status == "APPROVED":
        raise HTTPException(status_code=400, detail="Cannot reject an approved budget")
    from sqlalchemy import update as sql_update
    await db.execute(sql_update(GLBudget).where(GLBudget.id == budget_id).values(
        status="REJECTED", approved_by=current_user.id, approved_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await add_audit_log(db, "GLBudget", budget_id, "REJECT", current_user,
                        {"account_id": budget.account_id, "status": "REJECTED"})
    await db.commit()
    return {"message": "Budget rejected"}
