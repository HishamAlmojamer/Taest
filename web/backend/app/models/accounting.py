from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class Account(Base):
    __tablename__ = "accounts"
    __table_args__ = (
        Index("ix_accounts_code", "account_code"),
        Index("ix_accounts_type", "account_type"),
        Index("ix_accounts_is_active", "is_active"),
        Index("ix_accounts_parent_id", "parent_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_code: Mapped[str] = mapped_column(String(100), nullable=False)
    account_name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_name_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    account_type: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_control: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    currency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    opening_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    opening_balance_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class JournalEntry(Base):
    __tablename__ = "journal_entries"
    __table_args__ = (
        Index("ix_journal_entries_status", "status"),
        Index("ix_journal_entries_entry_date", "entry_date"),
        Index("ix_journal_entries_fiscal_period", "fiscal_period_id"),
        Index("ix_journal_entries_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entry_number: Mapped[str] = mapped_column(String(50), nullable=False)
    entry_date: Mapped[datetime] = mapped_column(nullable=False)
    fiscal_period_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reference_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    description_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    voided_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    workflow_state: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class JournalEntryLine(Base):
    __tablename__ = "journal_entry_lines"
    __table_args__ = (
        Index("ix_jel_journal_entry_id", "journal_entry_id"),
        Index("ix_jel_account_id", "account_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    journal_entry_id: Mapped[int] = mapped_column(Integer, nullable=False)
    account_id: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    debit: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    credit: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    currency_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    currency_rate: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    cost_center_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reconciliation_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class FiscalPeriod(Base):
    __tablename__ = "fiscal_periods"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    start_date: Mapped[datetime] = mapped_column(nullable=False)
    end_date: Mapped[datetime] = mapped_column(nullable=False)
    is_closed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_locked: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    closed_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class CostCenter(Base):
    __tablename__ = "cost_centers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
