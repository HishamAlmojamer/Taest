from typing import Optional
from pydantic import BaseModel, ConfigDict


class TaxRateCreate(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    rate: float = 0.0
    tax_type: str = "VAT"
    applies_to: str = "BOTH"
    is_recovery_allowed: bool = False
    gl_account_code: Optional[str] = None
    is_active: bool = True
    description: Optional[str] = None


class TaxRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_ar: Optional[str] = None
    rate: float
    tax_type: str = "VAT"
    applies_to: str = "BOTH"
    is_recovery_allowed: bool = False
    gl_account_code: Optional[str] = None
    is_active: bool = True
    description: Optional[str] = None
    created_at: Optional[str] = None


class TaxTransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tax_rate_id: int
    tax_rate_name: Optional[str] = None
    transaction_type: Optional[str] = None
    transaction_id: Optional[int] = None
    base_amount: float
    tax_amount: float
    invoice_number: Optional[str] = None
    created_at: Optional[str] = None
