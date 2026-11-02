"""
Quotation models: Sales Quotations that can be converted to sales invoices.

Quotations allow businesses to provide price quotes to customers before
committing to a sale. A quotation can be:
  - Draft: being prepared
  - Submitted: sent to the customer
  - Accepted: customer accepted the quote
  - Converted: converted into a Sales invoice
  - Expired: past its validity date
  - Rejected: customer declined
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Quotation(Base):
    __tablename__ = "quotations"
    __table_args__ = (
        Index("ix_quotations_number", "quotation_number"),
        Index("ix_quotations_customer", "customer_id"),
        Index("ix_quotations_status", "status"),
        Index("ix_quotations_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_number: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quotation_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    valid_until: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # draft, submitted, accepted, converted, expired, rejected
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    discount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    final_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sale_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # linked sale when converted
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    __table_args__ = (
        Index("ix_quotation_items_quotation", "quotation_id"),
        Index("ix_quotation_items_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quotation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    discount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_percent: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
