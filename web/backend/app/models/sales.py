from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Date, Index, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_name", "name"),
        Index("ix_customers_code", "code"),
        Index("ix_customers_company_id", "company_id"),
        Index("ix_customers_current_balance", "current_balance"),
        Index("ix_customers_segment_id", "segment_id"),
        Index("ix_customers_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    credit_limit: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    current_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    payment_term_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    national_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fax: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="SAR")
    price_list: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salesperson_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    segment_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    birthdate: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class Sale(Base):
    __tablename__ = "sales"
    __table_args__ = (
        Index("ix_sales_customer_id", "customer_id"),
        Index("ix_sales_created_at", "created_at"),
        Index("ix_sales_workflow_state", "workflow_state"),
        Index("ix_sales_payment_status", "payment_status"),
        Index("ix_sales_company_id", "company_id"),
        Index("ix_sales_invoice_number", "invoice_number"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    discount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    final_amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    payment_method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
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
    voided_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class SaleItem(Base):
    __tablename__ = "sale_items"
    __table_args__ = (
        Index("ix_sale_items_sale_id", "sale_id"),
        Index("ix_sale_items_product_id", "product_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("sales.id"), nullable=True)
    product_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("products.id"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    total_price: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_leads_status", "status"),
        Index("ix_leads_company", "company"),
        Index("ix_leads_assigned_to", "assigned_to"),
        Index("ix_leads_converted_customer_id", "converted_customer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lead_name: Mapped[str] = mapped_column(String(200), nullable=False)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    expected_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    lead_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    next_follow_up: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    industry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    budget: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    converted_customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    converted_opportunity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    won_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
