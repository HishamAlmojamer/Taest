from typing import Optional
from pydantic import BaseModel, ConfigDict


class CurrencyCreate(BaseModel):
    code: str
    name: str
    name_ar: Optional[str] = None
    symbol: Optional[str] = None
    decimal_places: Optional[int] = 2
    is_base_currency: Optional[bool] = False
    is_active: Optional[bool] = True


class CurrencyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_ar: Optional[str] = None
    symbol: Optional[str] = None
    decimal_places: int = 2
    is_base_currency: bool = False
    is_active: bool = True
    created_at: Optional[str] = None


class ExchangeRateCreate(BaseModel):
    from_currency_code: str
    to_currency_code: str
    rate: float
    effective_date: Optional[str] = None
    notes: Optional[str] = None


class ExchangeRateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    from_currency_code: str
    to_currency_code: str
    rate: float
    effective_date: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
