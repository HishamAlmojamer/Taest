"""
Period-End Closing procedures and audit trail.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PeriodClosingEntry(Base):
    __tablename__ = "period_closing_entries"
    __table_args__ = (
        Index("ix_period_closing_fiscal_period", "fiscal_period_id"),
        Index("ix_period_closing_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fiscal_period_id: Mapped[int] = mapped_column(Integer, nullable=False)
    closing_type: Mapped[str] = mapped_column(String(50), nullable=False)  # REVENUE_EXPENSE, RETAINED_EARNINGS, OPENING_BALANCE
    description: Mapped[str] = mapped_column(Text, nullable=False)
    total_debit: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    total_credit: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False, default=0.0)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="DRAFT")  # DRAFT, POSTED, REVERSED
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reversed_by_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    posted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_entity", "entity_type", "entity_id"),
        Index("ix_audit_logs_user", "user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)  # SALE, PURCHASE, JOURNAL_ENTRY, etc.
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, APPROVE, VOID
    changes_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON snapshot of changes
    user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    user_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
