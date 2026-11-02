from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AccountingVoucher(Base):
    """Accounting vouchers (سند قبض / سند صرف).

    A receipt voucher (RECEIPT) records money received into the fund/bank,
    crediting the partner (customer) or a counter account. A payment voucher
    (PAYMENT) records money paid out, debiting the partner (supplier) or a
    counter account. Each voucher produces a double-entry journal entry that is
    posted immediately on creation; voiding creates an automatic reversal.
    """

    __tablename__ = "accounting_vouchers"
    __table_args__ = (
        Index("ix_vouchers_type", "voucher_type"),
        Index("ix_vouchers_status", "status"),
        Index("ix_vouchers_partner", "partner_type", "partner_id"),
        Index("ix_vouchers_voucher_date", "voucher_date"),
        Index("ix_vouchers_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    voucher_type: Mapped[str] = mapped_column(String(20), nullable=False)  # RECEIPT | PAYMENT
    voucher_number: Mapped[str] = mapped_column(String(50), nullable=False)
    voucher_date: Mapped[datetime] = mapped_column(nullable=False)
    partner_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # customer | supplier
    partner_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(20), nullable=False)  # cash | bank
    bank_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="Posted")
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reversal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    void_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    currency_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="SAR")
    exchange_rate: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=1.0)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    updated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)