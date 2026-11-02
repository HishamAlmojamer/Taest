"""
Notifications models: In-app notifications for users.

Notifications can be user-specific (user_id set) or broadcast to everyone in
a company (user_id NULL). Each notification carries a type, an optional deep
link, and read state. The `notifications` table pre-dates this module, so the
model maps its `notification_type` attribute to the existing `type` column and
any missing columns are added via additive migrations in main.py.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, DateTime, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_created", "created_at"),
        Index("ix_notifications_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)  # NULL = broadcast
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notification_type: Mapped[Optional[str]] = mapped_column("type", String(50), nullable=True, default="info")  # maps to legacy `type` column
    link: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_read: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, default=lambda: datetime.utcnow())