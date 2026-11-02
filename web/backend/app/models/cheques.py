"""
Cheques Module — manages the full lifecycle of issued and received cheques.

Lifecycle:
  received → deposited → cleared | returned | stopped | cancelled | replaced
  issued   → cleared             | returned | stopped | cancelled | replaced
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Index, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Cheque(Base):
    __tablename__ = "cheques"
    __table_args__ = (
        Index("ix_cheques_status", "status"),
        Index("ix_cheques_cheque_type", "cheque_type"),
        Index("ix_cheques_bank_id", "bank_id"),
        Index("ix_cheques_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cheque_number: Mapped[str] = mapped_column(nullable=False)
    cheque_type: Mapped[str] = mapped_column(nullable=False)  # 'received' | 'issued'

    # Financial
    amount: Mapped[float] = mapped_column(nullable=False)
    currency_code: Mapped[str] = mapped_column(default="SAR")
    exchange_rate: Mapped[float] = mapped_column(default=1.0)

    # Parties
    payer_name: Mapped[Optional[str]] = mapped_column(Text)  # for received cheques
    payee_name: Mapped[Optional[str]] = mapped_column(Text)  # for issued cheques
    customer_id: Mapped[Optional[int]]
    supplier_id: Mapped[Optional[int]]

    # Bank info
    bank_id: Mapped[Optional[int]]
    bank_name: Mapped[Optional[str]]
    bank_branch: Mapped[Optional[str]]

    # Dates
    issue_date: Mapped[Optional[datetime]]
    due_date: Mapped[Optional[datetime]]
    deposit_date: Mapped[Optional[datetime]]
    clear_date: Mapped[Optional[datetime]]

    # Status
    status: Mapped[str] = mapped_column(default="on_hand")  # on_hand/deposited/under_collection/cleared/returned/stopped/cancelled/replaced
    status_reason: Mapped[Optional[str]] = mapped_column(Text)

    # Replacement tracking
    replaced_by_cheque_id: Mapped[Optional[int]]

    # Accounting
    journal_entry_id: Mapped[Optional[int]]  # original posting
    reversal_entry_id: Mapped[Optional[int]]  # reversal posting (bounced/returned)

    # Reference
    reference_type: Mapped[Optional[str]]  # 'customer_payment' | 'supplier_payment' | 'manual'
    reference_id: Mapped[Optional[int]]
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Audit
    created_by: Mapped[Optional[int]]
    updated_by: Mapped[Optional[int]]
    created_at: Mapped[Optional[datetime]]
    updated_at: Mapped[Optional[datetime]]
    company_id: Mapped[Optional[int]]
