from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator


class AssetCategoryCreate(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    depreciation_rate: float = 0.0
    depreciation_method: str = "STRAIGHT_LINE"
    useful_life_months: Optional[int] = None
    gl_account_id: Optional[int] = None
    depreciation_expense_account_id: Optional[int] = None
    accumulated_depreciation_account_id: Optional[int] = None
    description: Optional[str] = None

    @field_validator("depreciation_method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v = v.upper()
        if v not in {"STRAIGHT_LINE", "DECLINING_BALANCE", "UNITS_OF_PRODUCTION"}:
            raise ValueError("depreciation_method must be STRAIGHT_LINE, DECLINING_BALANCE or UNITS_OF_PRODUCTION")
        return v


class AssetCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_ar: Optional[str] = None
    depreciation_rate: float = 0.0
    depreciation_method: str = "STRAIGHT_LINE"
    useful_life_months: Optional[int] = None
    gl_account_id: Optional[int] = None
    depreciation_expense_account_id: Optional[int] = None
    accumulated_depreciation_account_id: Optional[int] = None
    is_active: bool = True
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class FixedAssetCreate(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    category_id: int
    description: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: float = 0.0
    salvage_value: float = 0.0
    useful_life_months: int = 0
    depreciation_method: str = "STRAIGHT_LINE"
    location: Optional[str] = None
    serial_number: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    warranty_expiry: Optional[str] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None

    @field_validator("depreciation_method")
    @classmethod
    def validate_method(cls, v: str) -> str:
        v = v.upper()
        if v not in {"STRAIGHT_LINE", "DECLINING_BALANCE", "UNITS_OF_PRODUCTION"}:
            raise ValueError("depreciation_method must be STRAIGHT_LINE, DECLINING_BALANCE or UNITS_OF_PRODUCTION")
        return v


class FixedAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_ar: Optional[str] = None
    category_id: int
    description: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: float = 0.0
    salvage_value: float = 0.0
    useful_life_months: int = 0
    depreciation_method: str = "STRAIGHT_LINE"
    accumulated_depreciation: float = 0.0
    current_value: float = 0.0
    status: str = "ACTIVE"
    location: Optional[str] = None
    serial_number: Optional[str] = None
    supplier_name: Optional[str] = None
    invoice_number: Optional[str] = None
    disposal_date: Optional[datetime] = None
    disposal_amount: Optional[float] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DepreciationEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: int
    asset_code: str
    asset_name: str
    period_month: int
    period_year: int
    depreciation_amount: float
    accumulated_depreciation: float
    book_value: float
    journal_entry_id: Optional[int] = None
    status: str = "DRAFT"
    created_at: Optional[datetime] = None
