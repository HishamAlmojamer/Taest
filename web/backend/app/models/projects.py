from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        Index("ix_projects_status", "status"),
        Index("ix_projects_manager", "manager_id"),
        Index("ix_projects_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    spent_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class ProjectTask(Base):
    __tablename__ = "project_tasks"
    __table_args__ = (
        Index("ix_project_tasks_project", "project_id"),
        Index("ix_project_tasks_status", "status"),
        Index("ix_project_tasks_assigned", "assigned_to"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    milestone_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name_ar: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    completion_percentage: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_estimate: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class ProjectMilestone(Base):
    __tablename__ = "project_milestones"
    __table_args__ = (Index("ix_project_milestones_project", "project_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    completion_percentage: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ProjectResource(Base):
    __tablename__ = "project_resources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    resource_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    qty: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ProjectBudget(Base):
    __tablename__ = "project_budgets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    spent_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class ProjectExpense(Base):
    __tablename__ = "project_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, nullable=False)
    task_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    budget_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expense_type: Mapped[str] = mapped_column(Text, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expense_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    receipt_ref: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
