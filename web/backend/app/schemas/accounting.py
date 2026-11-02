from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ── Account Schemas ──────────────────────────────────────────

ACCOUNT_TYPES = {"asset", "liability", "equity", "revenue", "expense"}


class AccountCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_code: str
    account_name: str
    account_name_en: Optional[str] = None
    account_name_ar: Optional[str] = None
    account_type: str
    parent_id: Optional[int] = None
    is_control: bool = False
    currency_id: Optional[int] = None
    opening_balance: float = 0
    opening_balance_date: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("account_type")
    @classmethod
    def validate_account_type(cls, v: str) -> str:
        if v.lower() not in ACCOUNT_TYPES:
            raise ValueError(f"Account type must be one of: {', '.join(sorted(ACCOUNT_TYPES))}")
        return v.lower()


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_code: str
    account_name: str
    account_name_en: Optional[str] = None
    account_name_ar: Optional[str] = None
    account_type: str
    parent_id: Optional[int] = None
    is_control: bool = False
    is_active: bool = True
    currency_id: Optional[int] = None
    opening_balance: float = 0
    opening_balance_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AccountTreeNode(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    name_ar: Optional[str] = None
    type: str
    parent_id: Optional[int] = None
    is_active: bool = True
    is_control: bool = False
    balance: float = 0
    cumulative_balance: float = 0
    children: List["AccountTreeNode"] = []


AccountTreeNode.model_rebuild()


# ── Journal Entry Schemas ────────────────────────────────────

class JournalEntryLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    description: Optional[str] = None
    debit: float = 0
    credit: float = 0
    currency_id: Optional[int] = None
    currency_rate: float = 1
    cost_center_id: Optional[int] = None
    partner_id: Optional[int] = None
    project_id: Optional[int] = None

    @field_validator("debit")
    @classmethod
    def validate_debit(cls, v: float) -> float:
        if v < 0:
            raise ValueError("debit must be >= 0")
        return v

    @field_validator("credit")
    @classmethod
    def validate_credit(cls, v: float) -> float:
        if v < 0:
            raise ValueError("credit must be >= 0")
        return v

    @model_validator(mode="after")
    def validate_debit_credit(self):
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Each journal line must have either a debit or a credit amount")
        if self.debit > 0 and self.credit > 0:
            raise ValueError("A journal line cannot have both debit and credit amounts")
        return self


class JournalEntryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    entry_date: str
    fiscal_period_id: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    lines: List[JournalEntryLineCreate] = []


class JournalEntryLineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    journal_entry_id: int
    account_id: Optional[int] = None
    description: Optional[str] = None
    debit: float
    credit: float
    currency_id: Optional[int] = None
    currency_rate: float
    cost_center_id: Optional[int] = None
    partner_id: Optional[int] = None
    project_id: Optional[int] = None
    created_at: Optional[datetime] = None


class JournalEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    entry_number: str
    entry_date: str
    fiscal_period_id: Optional[int] = None
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    description: str
    status: str
    created_by: Optional[int] = None
    posted_by: Optional[int] = None
    posted_at: Optional[str] = None
    created_at: Optional[datetime] = None
    lines: List[JournalEntryLineResponse] = []


class JournalEntryUpdate(BaseModel):
    entry_date: Optional[str] = None
    fiscal_period_id: Optional[int] = None
    description: Optional[str] = None
    lines: Optional[List[JournalEntryLineCreate]] = None


class CostCenterCreate(BaseModel):
    code: str
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[int] = None


class FiscalPeriodCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    start_date: str
    end_date: str


class CostCenterResponse(BaseModel):
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: bool = True
    created_at: Optional[datetime] = None


class RecurringJETemplateCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    frequency: str = "MONTHLY"
    next_run_date: Optional[str] = None
    template_data: Optional[str] = None


class RecurringJETemplateResponse(BaseModel):
    id: int
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    frequency: str
    next_run_date: Optional[str] = None
    last_run_date: Optional[str] = None
    is_active: bool = True
    template_data: Optional[str] = None
    created_at: Optional[str] = None
