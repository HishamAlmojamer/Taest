"""
Promotions models: Discounts and promotional offers.

Promotions apply automatic discounts to sales based on a discount type
(percentage or fixed amount) and can target all products, a category, or a
single product. They are time-bounded and can carry an optional minimum
purchase amount and a usage limit.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Promotion(Base):
    __tablename__ = "promotions"
    __table_args__ = (
        Index("ix_promotions_code", "code"),
        Index("ix_promotions_status", "status"),
        Index("ix_promotions_company", "company_id"),
        Index("ix_promotions_dates", "start_date", "end_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promo_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # percentage, fixed
    discount_value: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    applies_to: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # all, category, product
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # category/product id
    target_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    min_purchase: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    max_discount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="active")  # draft, active, paused, expired
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    used_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    priority: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)