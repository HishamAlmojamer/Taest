from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SaleItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: float
    total_price: float


class SaleItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sale_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: int
    unit_price: float
    total_price: float



class SaleCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: Optional[int] = None
    total_amount: float
    discount: float = 0
    final_amount: float
    payment_method: str = "cash"
    payment_status: str = "paid"
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1
    fiscal_period_id: Optional[int] = None
    invoice_number: Optional[str] = None
    tax_amount: float = 0
    tax_id: Optional[int] = None
    notes: Optional[str] = None
    items: List[SaleItemCreate] = []


class SaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: Optional[int] = None
    total_amount: float
    discount: float
    final_amount: float
    payment_method: str
    payment_status: str
    workflow_state: str
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    fiscal_period_id: Optional[int] = None
    invoice_number: Optional[str] = None
    journal_entry_id: Optional[int] = None
    tax_amount: float
    tax_id: Optional[int] = None
    notes: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None
    items: List[SaleItemResponse] = []

