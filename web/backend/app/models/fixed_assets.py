"""
Fixed Assets and Depreciation models.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AssetCategory(Base):
    __tablename__ = "asset_categories"
    __table_args__ = (
        Index("ix_asset_categories_code", "code", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    depreciation_rate: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)  # Annual rate %
    depreciation_method: Mapped[str] = mapped_column(String(50), nullable=False, default="STRAIGHT_LINE")  # STRAIGHT_LINE, DECLINING_BALANCE, UNITS_OF_PRODUCTION
    useful_life_months: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    gl_account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Asset GL account
    depreciation_expense_account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Expense account
    accumulated_depreciation_account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Contra-asset account
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class FixedAsset(Base):
    __tablename__ = "fixed_assets"
    __table_args__ = (
        Index("ix_fixed_assets_code", "code", unique=True),
        Index("ix_fixed_assets_category", "category_id"),
        Index("ix_fixed_assets_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    category_id: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    purchase_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    purchase_cost: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    salvage_value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    useful_life_months: Mapped[int] = mapped_column(Integer, nullable=False)
    depreciation_method: Mapped[str] = mapped_column(String(50), nullable=False, default="STRAIGHT_LINE")
    accumulated_depreciation: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    current_value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="ACTIVE")  # ACTIVE, FULLY_DEPRECIATED, DISPOSED, SOLD
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    serial_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    supplier_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    warranty_expiry: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disposal_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    disposal_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class DepreciationEntry(Base):
    __tablename__ = "depreciation_entries"
    __table_args__ = (
        Index("ix_depreciation_entries_asset", "asset_id"),
        Index("ix_depreciation_entries_period", "period_month", "period_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_code: Mapped[str] = mapped_column(String(50), nullable=False)
    asset_name: Mapped[str] = mapped_column(String(200), nullable=False)
    period_month: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    depreciation_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    accumulated_depreciation: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    book_value: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")  # DRAFT, POSTED
    posted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
