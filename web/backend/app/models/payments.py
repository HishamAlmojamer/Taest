from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CustomerPayment(Base):
    __tablename__ = "customer_payments"
    __table_args__ = (
        Index("ix_cust_payments_customer", "customer_id"),
        Index("ix_cust_payments_date", "payment_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class SupplierPayment(Base):
    __tablename__ = "supplier_payments"
    __table_args__ = (
        Index("ix_supp_payments_supplier", "supplier_id"),
        Index("ix_supp_payments_date", "payment_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    supplier_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(nullable=False)
    payment_method: Mapped[str] = mapped_column(String(50), nullable=False)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class Bank(Base):
    __tablename__ = "banks"
    __table_args__ = (Index("ix_banks_is_active", "is_active"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_number: Mapped[str] = mapped_column(String(100), nullable=False)
    iban: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    account_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    currency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opening_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    current_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    account_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class BankTransaction(Base):
    __tablename__ = "bank_transactions"
    __table_args__ = (
        Index("ix_bank_txns_bank", "bank_id"),
        Index("ix_bank_txns_date", "transaction_date"),
        Index("ix_bank_txns_reconciled", "reconciled"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    transaction_date: Mapped[datetime] = mapped_column(nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reconciled: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    reconciliation_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
