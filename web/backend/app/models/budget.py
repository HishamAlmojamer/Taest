"""
Budget Management models for GL-level budgeting.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class GLBudget(Base):
    __tablename__ = "gl_budgets"
    __table_args__ = (
        Index("ix_gl_budgets_account_period", "account_id", "fiscal_period_id"),
        Index("ix_gl_budgets_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, nullable=False)
    budget_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    actual_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    variance: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")  # DRAFT, APPROVED, REJECTED
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
