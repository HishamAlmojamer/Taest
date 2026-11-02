from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class NotificationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: Optional[int] = None  # NULL = broadcast to company
    title: str
    message: Optional[str] = None
    notification_type: str = "system"
    link: Optional[str] = None
    company_id: Optional[int] = 1


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    title: str
    message: Optional[str] = None
    notification_type: Optional[str] = None
    link: Optional[str] = None
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    company_id: Optional[int] = None
    created_at: Optional[datetime] = None