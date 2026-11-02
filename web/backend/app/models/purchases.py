from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Date, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (
        Index("ix_suppliers_name", "name"),
        Index("ix_suppliers_code", "code"),
        Index("ix_suppliers_company_id", "company_id"),
        Index("ix_suppliers_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    current_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    payment_term_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fax: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="SAR")
    industry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    payment_terms: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    iban: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (
        Index("ix_purchases_supplier_id", "supplier_id"),
        Index("ix_purchases_created_at", "created_at"),
        Index("ix_purchases_workflow_state", "workflow_state"),
        Index("ix_purchases_payment_status", "payment_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    discount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    final_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    payment_status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    tax_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    tax_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    workflow_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fiscal_period_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    invoice_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    voided_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class PurchaseItem(Base):
    __tablename__ = "purchase_items"
    __table_args__ = (
        Index("ix_purchase_items_purchase_id", "purchase_id"),
        Index("ix_purchase_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("purchases.id"), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
