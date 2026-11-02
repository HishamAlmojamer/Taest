from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class SalesReturnItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_price: float
    total_price: float
    tax_amount: float = 0
    reason: Optional[str] = None


class SalesReturnItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    total_price: Optional[float] = None
    tax_amount: Optional[float] = None
    reason: Optional[str] = None


class SalesReturnCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sale_id: Optional[int] = None
    sale_invoice_number: Optional[str] = None
    customer_id: Optional[int] = None
    return_date: Optional[datetime] = None
    total_amount: float = 0
    tax_amount: float = 0
    final_amount: float = 0
    reason: Optional[str] = None
    refund_method: Optional[str] = "credit"
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1
    notes: Optional[str] = None
    is_restocked: bool = True
    items: List[SalesReturnItemCreate] = []


class SalesReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_number: str
    sale_id: Optional[int] = None
    sale_invoice_number: Optional[str] = None
    customer_id: Optional[int] = None
    return_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    final_amount: Optional[float] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    refund_method: Optional[str] = None
    journal_entry_id: Optional[int] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    notes: Optional[str] = None
    is_restocked: Optional[bool] = None
    created_at: Optional[datetime] = None
    items: List[SalesReturnItemResponse] = []


class PurchaseReturnItemCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    quantity: int
    unit_cost: float
    total_cost: float
    tax_amount: float = 0
    reason: Optional[str] = None


class PurchaseReturnItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_id: Optional[int] = None
    product_id: Optional[int] = None
    quantity: Optional[int] = None
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    tax_amount: Optional[float] = None
    reason: Optional[str] = None


class PurchaseReturnCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    purchase_id: Optional[int] = None
    purchase_order_number: Optional[str] = None
    supplier_id: Optional[int] = None
    return_date: Optional[datetime] = None
    total_amount: float = 0
    tax_amount: float = 0
    final_amount: float = 0
    reason: Optional[str] = None
    refund_method: Optional[str] = "credit"
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1
    notes: Optional[str] = None
    is_restocked: bool = True
    items: List[PurchaseReturnItemCreate] = []


class PurchaseReturnResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    return_number: str
    purchase_id: Optional[int] = None
    purchase_order_number: Optional[str] = None
    supplier_id: Optional[int] = None
    return_date: Optional[datetime] = None
    total_amount: Optional[float] = None
    tax_amount: Optional[float] = None
    final_amount: Optional[float] = None
    status: Optional[str] = None
    reason: Optional[str] = None
    refund_method: Optional[str] = None
    journal_entry_id: Optional[int] = None
    created_by: Optional[int] = None
    approved_by: Optional[int] = None
    approved_at: Optional[datetime] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    notes: Optional[str] = None
    is_restocked: Optional[bool] = None
    created_at: Optional[datetime] = None
    items: List[PurchaseReturnItemResponse] = []

