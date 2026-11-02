from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    entity_name: Optional[str] = None
    old_value: Optional[str] = None
    new_value: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[str] = None


class PeriodClosingEntryCreate(BaseModel):
    fiscal_period_id: int
    description: Optional[str] = None
    notes: Optional[str] = None


class PeriodClosingEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fiscal_period_id: int
    period_name: Optional[str] = None
    description: Optional[str] = None
    closing_journal_entry_id: Optional[int] = None
    closing_date: Optional[str] = None
    closed_by: Optional[int] = None
    closed_by_name: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
