from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


class CategoryCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    parent_id: Optional[int] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Any = None


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    unit_id: Optional[int] = None
    unit: str = "pcs"
    purchase_price: float = 0
    selling_price: float = 0
    current_stock: float = 0
    min_stock: float = 0
    max_stock: float = 0
    reorder_point: float = 0
    location: Optional[str] = None
    valuation_method: str = "fifo"
    weight: Optional[float] = None
    tax_percent: float = 0
    brand: Optional[str] = None
    description: Optional[str] = None
    company_id: int = 1


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: str
    name_en: Optional[str] = None
    barcode: Optional[str] = None
    category_id: Optional[int] = None
    unit_id: Optional[int] = None
    unit: str = ""
    purchase_price: float = 0
    selling_price: float = 0
    last_purchase_price: Optional[float] = None
    current_stock: float = 0
    min_stock: float = 0
    max_stock: float = 0
    reorder_point: float = 0
    location: Optional[str] = None
    valuation_method: Optional[str] = None
    weight: Optional[float] = None
    tax_percent: float = 0
    brand: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    company_id: Optional[int] = None
    created_at: Any = None
    updated_at: Any = None
