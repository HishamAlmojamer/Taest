from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class BankReconciliationCreate(BaseModel):
    bank_id: int
    statement_date: str
    statement_balance: float
    book_balance: Optional[float] = 0
    notes: Optional[str] = None


class BankReconciliationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_id: int
    bank_name: Optional[str] = None
    statement_date: str
    statement_balance: float
    book_balance: float = 0
    difference: float = 0
    status: str = "in_progress"
    reconciled_by: Optional[int] = None
    reconciled_at: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List["BankReconciliationItemResponse"]] = None
    created_at: Optional[str] = None


class BankReconciliationItemCreate(BaseModel):
    reconciliation_id: int
    journal_entry_id: Optional[int] = None
    bank_transaction_id: Optional[int] = None
    description: Optional[str] = None
    amount: float
    type: str  # 'deposit' or 'withdrawal'
    is_matched: Optional[bool] = False


class BankReconciliationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reconciliation_id: int
    journal_entry_id: Optional[int] = None
    journal_entry_number: Optional[str] = None
    bank_transaction_id: Optional[int] = None
    description: Optional[str] = None
    amount: float
    type: str
    is_matched: bool = False
    matched_at: Optional[str] = None
    created_at: Optional[str] = None


class BankStatementImportCreate(BaseModel):
    bank_id: int
    file_name: str
    file_format: str  # 'csv', 'ofx', 'qif'
    statement_date: Optional[str] = None
    notes: Optional[str] = None


class BankStatementImportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_id: int
    bank_name: Optional[str] = None
    file_name: str
    file_format: str
    statement_date: Optional[str] = None
    status: str = "pending"
    records_imported: int = 0
    records_matched: int = 0
    records_unmatched: int = 0
    notes: Optional[str] = None
    imported_by: Optional[int] = None
    created_at: Optional[str] = None
