"""
Tax Rate model for VAT/GST/tax management.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class TaxRate(Base):
    __tablename__ = "tax_rates"
    __table_args__ = (
        Index("ix_tax_rates_code", "code", unique=True),
        Index("ix_tax_rates_type", "tax_type"),
        Index("ix_tax_rates_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    rate: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    tax_type: Mapped[str] = mapped_column(String(50), nullable=False)  # VAT, GST, WITHHOLDING, EXEMPT
    applies_to: Mapped[str] = mapped_column(String(50), nullable=False, default="SALES")  # SALES, PURCHASES, BOTH
    is_recovery_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # Can input tax be claimed
    gl_account_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # e.g., '2120' for VAT Output
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class TaxTransaction(Base):
    __tablename__ = "tax_transactions"
    __table_args__ = (
        Index("ix_tax_transactions_invoice", "invoice_type", "invoice_id"),
        Index("ix_tax_transactions_tax_rate", "tax_rate_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_type: Mapped[str] = mapped_column(String(50), nullable=False)  # SALE, PURCHASE
    invoice_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_id: Mapped[int] = mapped_column(Integer, nullable=False)
    tax_rate_code: Mapped[str] = mapped_column(String(50), nullable=False)
    tax_rate: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    taxable_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    is_input_tax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)  # True for purchases (VAT Input)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
