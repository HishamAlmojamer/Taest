import math
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.projects import (
    Project, ProjectTask, ProjectMilestone,
    ProjectResource, ProjectBudget, ProjectExpense,
)
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission

router = APIRouter()


# ── Projects ──────────────────────────────────────────────────

@router.get("", response_model=PaginationResponse)
async def list_projects(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Project).where(Project.is_active == True)
    count_query = select(func.count(Project.id)).where(Project.is_active == True)
    if status:
        query = query.where(Project.status == status)
        count_query = count_query.where(Project.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Project.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    projects = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{"id": p.id, "code": p.code, "name": p.name_en or p.name_ar,
                "nameAr": p.name_ar, "nameEn": p.name_en,
                "description": p.notes, "status": p.status, "priority": p.priority,
                "budget": p.budget_amount or 0, "budgetAmount": p.budget_amount,
                "spentAmount": p.spent_amount, "progress": 0,
                "startDate": p.start_date, "endDate": p.end_date,
                "customerName": None, "managerName": None,
                "currency": p.currency, "managerId": p.manager_id,
                "customerId": None, "companyId": p.company_id}
               for p in projects],
    )


@router.get("/{project_id}")
async def get_project(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.is_active == True))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "id": project.id, "code": project.code, "name_ar": project.name_ar,
        "name_en": project.name_en, "description": project.description,
        "company_id": project.company_id, "branch_id": project.branch_id,
        "manager_id": project.manager_id, "start_date": project.start_date,
        "end_date": project.end_date, "status": project.status,
        "priority": project.priority, "budget_amount": project.budget_amount,
        "spent_amount": project.spent_amount, "currency": project.currency,
        "notes": project.notes, "is_active": project.is_active,
    }


@router.post("", response_model=dict)
async def create_project(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    if not data.get("name_ar"):
        raise HTTPException(status_code=400, detail="Project name (name_ar) is required")
    count = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    code = f"PRJ-{datetime.now().year}-{count + 1:04d}"

    project = Project(
        code=code, name_ar=data["name_ar"], name_en=data.get("name_en"),
        description=data.get("description"), company_id=data.get("company_id"),
        branch_id=data.get("branch_id"), manager_id=data.get("manager_id"),
        start_date=data.get("start_date"), end_date=data.get("end_date"),
        status=data.get("status", "planned"), priority=data.get("priority", "medium"),
        budget_amount=float(data.get("budget_amount", 0)),
        currency=data.get("currency", "YER"), notes=data.get("notes"),
        created_by=current_user.id, created_at=datetime.now(UTC).replace(tzinfo=None),
        is_active=True,
    )
    db.add(project)
    await db.flush()
    return {"id": project.id, "code": code, "message": "Project created"}


@router.put("/{project_id}", response_model=dict)
async def update_project(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    result = await db.execute(select(Project).where(Project.id == project_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Project not found")
    allowed = {'name_ar', 'name_en', 'description', 'manager_id', 'start_date', 'end_date',
               'status', 'priority', 'budget_amount', 'currency', 'notes', 'company_id', 'branch_id'}
    values = {k: v for k, v in data.items() if k in allowed}
    if values:
        await db.execute(update(Project).where(Project.id == project_id).values(**values))
    return {"message": "Project updated"}


@router.delete("/{project_id}", response_model=MessageResponse)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    await db.execute(update(Project).where(Project.id == project_id).values(is_active=False))
    return MessageResponse(message="Project deleted")


@router.get("/{project_id}/dashboard")
async def project_dashboard(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tasks_count = (await db.execute(select(func.count(ProjectTask.id))
        .where(ProjectTask.project_id == project_id, ProjectTask.is_active == True))).scalar() or 0
    completed_tasks = (await db.execute(select(func.count(ProjectTask.id))
        .where(ProjectTask.project_id == project_id, ProjectTask.is_active == True, ProjectTask.status == "completed"))).scalar() or 0
    budget_result = await db.execute(
        select(func.coalesce(func.sum(ProjectBudget.budget_amount), 0),
               func.coalesce(func.sum(ProjectBudget.spent_amount), 0))
        .where(ProjectBudget.project_id == project_id))
    budget_row = budget_result.one()

    return {
        "project_id": project_id, "status": project.status,
        "budget_amount": project.budget_amount, "spent_amount": project.spent_amount,
        "tasks_total": tasks_count, "tasks_completed": completed_tasks,
        "completion_pct": round(completed_tasks / tasks_count * 100, 1) if tasks_count else 0,
        "budget_total": budget_row[0], "budget_spent": budget_row[1],
        "budget_remaining": budget_row[0] - budget_row[1],
    }


# ── Tasks ─────────────────────────────────────────────────────

@router.get("/{project_id}/tasks")
async def list_tasks(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectTask)
        .where(ProjectTask.project_id == project_id, ProjectTask.is_active == True)
        .order_by(ProjectTask.created_at.desc()))
    return [{"id": t.id, "project_id": t.project_id, "milestone_id": t.milestone_id,
             "name_ar": t.name_ar, "name_en": t.name_en, "description": t.description,
             "assigned_to": t.assigned_to, "start_date": t.start_date, "end_date": t.end_date,
             "estimated_hours": t.estimated_hours, "actual_hours": t.actual_hours,
             "completion_percentage": t.completion_percentage, "status": t.status,
             "priority": t.priority, "cost_estimate": t.cost_estimate, "actual_cost": t.actual_cost}
            for t in result.scalars().all()]


@router.post("/{project_id}/tasks", response_model=dict)
async def create_task(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    if not data.get("name_ar"):
        raise HTTPException(status_code=400, detail="Task name (name_ar) is required")
    task = ProjectTask(
        project_id=project_id, milestone_id=data.get("milestone_id"),
        parent_task_id=data.get("parent_task_id"),
        name_ar=data["name_ar"], name_en=data.get("name_en"),
        description=data.get("description"), assigned_to=data.get("assigned_to"),
        start_date=data.get("start_date"), end_date=data.get("end_date"),
        estimated_hours=float(data.get("estimated_hours", 0)),
        status=data.get("status", "pending"), priority=data.get("priority", "medium"),
        cost_estimate=float(data.get("cost_estimate", 0)),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        is_active=True,
    )
    db.add(task)
    await db.flush()
    return {"id": task.id, "message": "Task created"}


@router.put("/tasks/{task_id}", response_model=dict)
async def update_task(task_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    result = await db.execute(select(ProjectTask).where(ProjectTask.id == task_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Task not found")
    allowed = {'name_ar', 'name_en', 'description', 'assigned_to', 'start_date', 'end_date',
               'estimated_hours', 'actual_hours', 'completion_percentage', 'status',
               'priority', 'cost_estimate', 'actual_cost', 'notes', 'milestone_id'}
    values = {k: v for k, v in data.items() if k in allowed}
    if values:
        await db.execute(update(ProjectTask).where(ProjectTask.id == task_id).values(**values))
    return {"message": "Task updated"}


@router.delete("/tasks/{task_id}", response_model=MessageResponse)
async def delete_task(task_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    await db.execute(update(ProjectTask).where(ProjectTask.id == task_id).values(is_active=False))
    return MessageResponse(message="Task deleted")


# ── Milestones ────────────────────────────────────────────────

@router.get("/{project_id}/milestones")
async def list_milestones(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectMilestone)
        .where(ProjectMilestone.project_id == project_id)
        .order_by(ProjectMilestone.due_date))
    return [{"id": m.id, "project_id": m.project_id, "name": m.name,
             "description": m.description, "due_date": m.due_date,
             "status": m.status, "completion_percentage": m.completion_percentage}
            for m in result.scalars().all()]


@router.post("/{project_id}/milestones", response_model=dict)
async def create_milestone(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    if not data.get("name"):
        raise HTTPException(status_code=400, detail="Milestone name is required")
    milestone = ProjectMilestone(
        project_id=project_id, name=data["name"],
        description=data.get("description"), due_date=data.get("due_date"),
        status=data.get("status", "pending"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(milestone)
    await db.flush()
    return {"id": milestone.id, "message": "Milestone created"}


@router.put("/milestones/{milestone_id}", response_model=dict)
async def update_milestone(milestone_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    result = await db.execute(select(ProjectMilestone).where(ProjectMilestone.id == milestone_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Milestone not found")
    values = {k: data[k] for k in ("name", "description", "due_date", "status", "completion_percentage") if k in data}
    if values:
        await db.execute(update(ProjectMilestone).where(ProjectMilestone.id == milestone_id).values(**values))
    return {"message": "Milestone updated"}


# ── Resources ─────────────────────────────────────────────────

@router.get("/{project_id}/resources")
async def list_resources(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectResource)
        .where(ProjectResource.project_id == project_id)
        .order_by(ProjectResource.created_at.desc()))
    return [{"id": r.id, "project_id": r.project_id, "task_id": r.task_id,
             "resource_type": r.resource_type, "resource_id": r.resource_id,
             "qty": r.qty, "unit_cost": r.unit_cost, "total_cost": r.total_cost,
             "start_date": r.start_date, "end_date": r.end_date, "notes": r.notes}
            for r in result.scalars().all()]


@router.post("/{project_id}/resources", response_model=dict)
async def create_resource(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    qty = float(data.get("qty", 1))
    unit_cost = float(data.get("unit_cost", 0))
    resource = ProjectResource(
        project_id=project_id, task_id=data.get("task_id"),
        resource_type=data.get("resource_type", ""),
        resource_id=data.get("resource_id"), qty=qty,
        unit_cost=unit_cost, total_cost=qty * unit_cost,
        start_date=data.get("start_date"), end_date=data.get("end_date"),
        notes=data.get("notes"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(resource)
    await db.flush()
    return {"id": resource.id, "message": "Resource added"}


# ── Budget ────────────────────────────────────────────────────

@router.get("/{project_id}/budget")
async def list_budget(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectBudget)
        .where(ProjectBudget.project_id == project_id)
        .order_by(ProjectBudget.category))
    return [{"id": b.id, "project_id": b.project_id, "category": b.category,
             "description": b.description, "budget_amount": b.budget_amount,
             "spent_amount": b.spent_amount,
             "remaining": b.budget_amount - b.spent_amount}
            for b in result.scalars().all()]


@router.post("/{project_id}/budget", response_model=dict)
async def create_budget(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    budget = ProjectBudget(
        project_id=project_id, category=data.get("category", ""),
        description=data.get("description"),
        budget_amount=float(data.get("budget_amount", 0)),
        notes=data.get("notes"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(budget)
    await db.flush()
    return {"id": budget.id, "message": "Budget line created"}


# ── Expenses ──────────────────────────────────────────────────

@router.get("/{project_id}/expenses")
async def list_expenses(project_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectExpense)
        .where(ProjectExpense.project_id == project_id)
        .order_by(ProjectExpense.created_at.desc()))
    return [{"id": e.id, "project_id": e.project_id, "task_id": e.task_id,
             "budget_id": e.budget_id, "expense_type": e.expense_type,
             "amount": e.amount, "description": e.description,
             "expense_date": e.expense_date, "receipt_ref": e.receipt_ref,
             "approved_by": e.approved_by, "notes": e.notes}
            for e in result.scalars().all()]


@router.post("/{project_id}/expenses", response_model=dict)
async def create_expense(project_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_PROJECTS"))):
    expense = ProjectExpense(
        project_id=project_id, task_id=data.get("task_id"),
        budget_id=data.get("budget_id"),
        expense_type=data.get("expense_type", ""),
        amount=float(data.get("amount", 0)),
        description=data.get("description"),
        expense_date=data.get("expense_date"),
        receipt_ref=data.get("receipt_ref"),
        notes=data.get("notes"), created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(expense)

    if expense.budget_id:
        budget_result = await db.execute(select(ProjectBudget).where(ProjectBudget.id == expense.budget_id))
        budget = budget_result.scalar_one_or_none()
        if budget:
            budget.spent_amount = (budget.spent_amount or 0) + expense.amount

    proj_result = await db.execute(select(Project).where(Project.id == project_id))
    proj = proj_result.scalar_one_or_none()
    if proj:
        proj.spent_amount = (proj.spent_amount or 0) + expense.amount

    await db.flush()
    return {"id": expense.id, "message": "Expense recorded"}
