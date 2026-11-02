from typing import Optional
from pydantic import BaseModel, ConfigDict


class CustomerPaymentCreate(BaseModel):
    customer_id: int
    amount: float
    payment_method: str = "cash"
    payment_date: Optional[str] = None
    reference_number: Optional[str] = None
    bank_id: Optional[int] = None
    notes: Optional[str] = None
    currency_code: Optional[str] = "SAR"


class CustomerPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    customer_name: Optional[str] = None
    amount: float
    payment_method: str
    payment_date: Optional[str] = None
    reference_number: Optional[str] = None
    bank_id: Optional[int] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    currency_code: str = "SAR"
    journal_entry_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


class SupplierPaymentCreate(BaseModel):
    supplier_id: int
    amount: float
    payment_method: str = "cash"
    payment_date: Optional[str] = None
    reference_number: Optional[str] = None
    bank_id: Optional[int] = None
    notes: Optional[str] = None
    currency_code: Optional[str] = "SAR"


class SupplierPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    supplier_id: int
    supplier_name: Optional[str] = None
    amount: float
    payment_method: str
    payment_date: Optional[str] = None
    reference_number: Optional[str] = None
    bank_id: Optional[int] = None
    bank_name: Optional[str] = None
    notes: Optional[str] = None
    currency_code: str = "SAR"
    journal_entry_id: Optional[int] = None
    created_by: Optional[int] = None
    created_at: Optional[str] = None


class BankCreate(BaseModel):
    name: str
    name_ar: Optional[str] = None
    code: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    currency_code: Optional[str] = "SAR"
    opening_balance: Optional[float] = 0
    notes: Optional[str] = None


class BankResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    name_ar: Optional[str] = None
    code: Optional[str] = None
    account_number: Optional[str] = None
    iban: Optional[str] = None
    currency_code: str = "SAR"
    current_balance: float = 0
    opening_balance: float = 0
    is_active: bool = True
    notes: Optional[str] = None
    created_at: Optional[str] = None


class BankTransactionCreate(BaseModel):
    bank_id: int
    transaction_type: str
    amount: float
    transaction_date: Optional[str] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    reconciled: Optional[bool] = False


class BankTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank_id: int
    transaction_type: str
    amount: float
    balance_after: Optional[float] = None
    transaction_date: Optional[str] = None
    reference_number: Optional[str] = None
    description: Optional[str] = None
    reconciled: bool = False
    created_at: Optional[str] = None
