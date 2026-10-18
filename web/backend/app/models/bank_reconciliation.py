"""
Bank Reconciliation models and endpoints.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class BankReconciliation(Base):
    __tablename__ = "bank_reconciliations"
    __table_args__ = (
        Index("ix_bank_reconciliations_bank", "bank_id"),
        Index("ix_bank_reconciliations_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reconciliation_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    statement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    statement_balance: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    book_balance: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    difference: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")  # DRAFT, COMPLETED, REVERSED
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reconciled_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BankReconciliationItem(Base):
    __tablename__ = "bank_reconciliation_items"
    __table_args__ = (
        Index("ix_bank_reconciliation_items_reconciliation", "reconciliation_id"),
        Index("ix_bank_reconciliation_items_transaction", "bank_transaction_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reconciliation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bank_transaction_id: Mapped[int] = mapped_column(Integer, nullable=False)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reconciled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class BankStatementImport(Base):
    __tablename__ = "bank_statement_imports"
    __table_args__ = (
        Index("ix_bank_statement_imports_bank", "bank_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bank_id: Mapped[int] = mapped_column(Integer, nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_format: Mapped[str] = mapped_column(String(50), nullable=False)  # CSV, OFX, QIF
    statement_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    matched_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unmatched_transactions: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="PENDING")  # PENDING, PROCESSED, FAILED
    imported_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
