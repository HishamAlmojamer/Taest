from datetime import datetime
from typing import Any, Optional, List
from pydantic import BaseModel, ConfigDict, field_validator

from app.utils.validation import coerce_datetime


class _TolerantCreatedAt(BaseModel):
    """Base for responses whose ``created_at`` column is legacy ``text``.

    A malformed stored timestamp must not fail validation for the whole
    endpoint, so it degrades to ``None`` instead.
    """

    @field_validator("created_at", mode="before", check_fields=False)
    @classmethod
    def _coerce_created_at(cls, value: Any) -> Optional[datetime]:
        return coerce_datetime(value)

    @field_validator("last_login_at", mode="before", check_fields=False)
    @classmethod
    def _coerce_last_login(cls, value: Any) -> Optional[datetime]:
        return coerce_datetime(value)


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    module: Optional[str] = None
    description: Optional[str] = None


class RoleResponse(_TolerantCreatedAt):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    permissions: List[PermissionResponse] = []


class RoleCreate(BaseModel):
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    is_active: bool = True
    permission_ids: List[int] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    name_en: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permission_ids: Optional[List[int]] = None


class UserWithPermissions(_TolerantCreatedAt):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    full_name: str = ""
    role: str = "user"
    role_id: Optional[int] = None
    is_active: bool = True
    email: Optional[str] = None
    phone: Optional[str] = None
    last_login_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    permissions: List[str] = []
