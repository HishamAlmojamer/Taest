from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class AccountCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_code: str
    account_name: str
    account_name_en: Optional[str] = None
    account_type: str
    parent_id: Optional[int] = None
    is_control: bool = False
    currency_id: Optional[int] = None
    opening_balance: float = 0
    opening_balance_date: Optional[str] = None
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_code: str
    account_name: str
    account_name_en: Optional[str] = None
    account_type: str
    parent_id: Optional[int] = None
    is_control: bool
    is_active: bool
    currency_id: Optional[int] = None
    opening_balance: float
    opening_balance_date: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None



class JournalEntryLineCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: int
    description: Optional[str] = None
    debit: float = 0
    credit: float = 0
    currency_id: Optional[int] = None
    currency_rate: float = 1
    cost_center_id: Optional[int] = None


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

