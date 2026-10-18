from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class PaginationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total: int
    page: int
    per_page: int
    pages: int
    items: List[Any]


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    message: str
    success: bool = True
    data: Optional[Any] = None


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: Optional[Any] = None
