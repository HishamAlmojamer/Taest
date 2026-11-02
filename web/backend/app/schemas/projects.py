from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    customer_id: Optional[int] = None
    manager_id: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = 0
    status: Optional[str] = "planning"
    priority: Optional[str] = "medium"
    notes: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_ar: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: float = 0
    spent: float = 0
    status: str = "planning"
    priority: str = "medium"
    completion_percentage: Optional[float] = 0
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None


class ProjectTaskCreate(BaseModel):
    project_id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    priority: Optional[str] = "medium"
    status: Optional[str] = "todo"
    parent_task_id: Optional[int] = None


class ProjectTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    start_date: Optional[str] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    priority: str = "medium"
    status: str = "todo"
    parent_task_id: Optional[int] = None
    completion_percentage: Optional[float] = 0
    created_at: Optional[str] = None


class ProjectMilestoneCreate(BaseModel):
    project_id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: Optional[str] = "pending"


class ProjectMilestoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    name: str
    name_ar: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[str] = None
    status: str = "pending"
    completed_at: Optional[str] = None
    created_at: Optional[str] = None


class ProjectResourceCreate(BaseModel):
    project_id: int
    employee_id: int
    role: Optional[str] = None
    allocation_percentage: Optional[float] = 100
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    hourly_rate: Optional[float] = None
    notes: Optional[str] = None


class ProjectResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    employee_id: int
    employee_name: Optional[str] = None
    role: Optional[str] = None
    allocation_percentage: float = 100
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    hourly_rate: Optional[float] = None
    total_cost: Optional[float] = 0
    notes: Optional[str] = None
    created_at: Optional[str] = None


class ProjectBudgetCreate(BaseModel):
    project_id: int
    category: str
    description: Optional[str] = None
    budgeted_amount: float
    notes: Optional[str] = None


class ProjectBudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    category: str
    description: Optional[str] = None
    budgeted_amount: float
    spent_amount: float = 0
    variance: float = 0
    notes: Optional[str] = None
    created_at: Optional[str] = None


class ProjectExpenseCreate(BaseModel):
    project_id: int
    budget_id: Optional[int] = None
    description: str
    amount: float
    expense_date: Optional[str] = None
    category: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None


class ProjectExpenseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    budget_id: Optional[int] = None
    description: str
    amount: float
    expense_date: Optional[str] = None
    category: Optional[str] = None
    reference_number: Optional[str] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None
