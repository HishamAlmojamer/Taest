from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class QuotationItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: float
    discount: float = 0
    tax_percent: float = 0
    tax_amount: float = 0
    total_price: float


class QuotationItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    discount: Optional[float] = None
    tax_percent: Optional[float] = None
    tax_amount: Optional[float] = None
    total_price: Optional[float] = None


class QuotationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: Optional[int] = None
    quotation_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    total_amount: float = 0
    tax_amount: float = 0
    discount: float = 0
    final_amount: float = 0
    currency_code: Optional[str] = "SAR"
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1
    items: List[QuotationItemCreate] = []


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_number: str
    customer_id: Optional[int] = None
    quotation_date: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    status: Optional[str] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    discount: Optional[float] = None
    final_amount: Optional[float] = None
    currency_code: Optional[str] = None
    payment_terms: Optional[str] = None
    notes: Optional[str] = None
    sale_id: Optional[int] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    items: List[QuotationItemResponse] = []