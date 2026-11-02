from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class PromotionCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    promo_type: str = "percentage"  # percentage, fixed
    discount_value: float = 0
    applies_to: str = "all"  # all, category, product
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    min_purchase: float = 0
    max_discount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: bool = True
    usage_limit: Optional[int] = None
    priority: int = 0
    company_id: Optional[int] = 1
    branch_id: Optional[int] = 1


class PromotionUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    promo_type: Optional[str] = None
    discount_value: Optional[float] = None
    applies_to: Optional[str] = None
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None
    usage_limit: Optional[int] = None
    priority: Optional[int] = None
    branch_id: Optional[int] = None


class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: Optional[str] = None
    name: str
    description: Optional[str] = None
    promo_type: Optional[str] = None
    discount_value: Optional[float] = None
    applies_to: Optional[str] = None
    target_id: Optional[int] = None
    target_name: Optional[str] = None
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    is_active: Optional[bool] = None
    usage_limit: Optional[int] = None
    used_count: Optional[int] = None
    priority: Optional[int] = None
    company_id: Optional[int] = None
    branch_id: Optional[int] = None
    created_at: Optional[datetime] = None