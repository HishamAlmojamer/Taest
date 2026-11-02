"""
Returns models: Sales Returns and Purchase Returns.

These models support the return of goods from customers (sales returns) and
to suppliers (purchase returns). Each return reverses the original sale/purchase
and its associated journal entry, ensuring the double-entry ledger stays balanced.

Accounting Logic:
  - Sales Return: Debit Sales Returns (contra-revenue), Credit Accounts Receivable / Bank
  - Purchase Return: Debit Accounts Payable, Credit Purchase Returns (contra-expense)
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class SalesReturn(Base):
    __tablename__ = "sales_returns"
    __table_args__ = (
        Index("ix_sales_returns_number", "return_number"),
        Index("ix_sales_returns_customer", "customer_id"),
        Index("ix_sales_returns_sale", "sale_id"),
        Index("ix_sales_returns_status", "status"),
        Index("ix_sales_returns_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_number: Mapped[str] = mapped_column(String(100), nullable=False)
    sale_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sale_invoice_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    return_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    final_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # draft, submitted, approved, voided
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # cash, bank, credit
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_restocked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class SalesReturnItem(Base):
    __tablename__ = "sales_return_items"
    __table_args__ = (
        Index("ix_sales_return_items_return", "return_id"),
        Index("ix_sales_return_items_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_price: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PurchaseReturn(Base):
    __tablename__ = "purchase_returns"
    __table_args__ = (
        Index("ix_purchase_returns_number", "return_number"),
        Index("ix_purchase_returns_supplier", "supplier_id"),
        Index("ix_purchase_returns_purchase", "purchase_id"),
        Index("ix_purchase_returns_status", "status"),
        Index("ix_purchase_returns_company", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_number: Mapped[str] = mapped_column(String(100), nullable=False)
    purchase_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    purchase_order_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    return_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    total_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    final_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # draft, submitted, approved, voided
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refund_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_restocked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class PurchaseReturnItem(Base):
    __tablename__ = "purchase_return_items"
    __table_args__ = (
        Index("ix_purchase_return_items_return", "return_id"),
        Index("ix_purchase_return_items_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    unit_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
