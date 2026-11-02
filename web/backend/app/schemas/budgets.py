from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class BudgetCreate(BaseModel):
    account_id: int
    fiscal_period_id: int
    budget_amount: float = 0.0
    notes: Optional[str] = None
    company_id: Optional[int] = None


class BudgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    fiscal_period_id: int
    budget_amount: float = 0.0
    actual_amount: float = 0.0
    variance: float = 0.0
    notes: Optional[str] = None
    company_id: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    status: str = "DRAFT"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
