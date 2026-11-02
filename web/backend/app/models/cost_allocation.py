"""
Cost Center Allocation Rule models.

An allocation rule reclassifies the period balance of a source (expense)
account across multiple cost centers by percentage. Applying a rule posts a
balanced journal entry:

    Dr  target expense account(s)         balance * percentage
    Cr  source account                    balance

The cost-center dimension is carried on the posted lines via cost_center_id.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CostCenterAllocationRule(Base):
    __tablename__ = "cost_center_allocation_rules"
    __table_args__ = (
        Index("ix_cc_alloc_rule_source", "source_account_id"),
        Index("ix_cc_alloc_rule_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source_account_id: Mapped[int] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=False)
    target_account_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("accounts.id"), nullable=True)
    allocation_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="ONCE")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class CostCenterAllocationRuleLine(Base):
    __tablename__ = "cost_center_allocation_rule_lines"
    __table_args__ = (
        Index("ix_cc_alloc_rule_line_rule", "rule_id"),
        Index("ix_cc_alloc_rule_line_cc", "cost_center_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, ForeignKey("cost_center_allocation_rules.id"), nullable=False)
    cost_center_id: Mapped[int] = mapped_column(Integer, ForeignKey("cost_centers.id"), nullable=False)
    percentage: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)