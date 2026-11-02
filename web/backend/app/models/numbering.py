"""
Document numbering model for configurable, independent per-document counters.

Unlike numbering that relies on the record's primary key (which breaks when
records are deleted or inserted between types), this stores an explicit next
counter per document type so sequences remain contiguous and configurable.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class DocumentNumbering(Base):
    __tablename__ = "document_numbering"
    __table_args__ = (
        Index("ix_document_numbering_doc_type_period", "doc_type", "period"),
        Index("ix_document_numbering_doc_type_unique", "doc_type", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doc_type: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    prefix: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    suffix: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    zero_padding: Mapped[int] = mapped_column(Integer, nullable=False, default=6)
    include_year: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    separator: Mapped[Optional[str]] = mapped_column(String(5), nullable=True, default="-")
    period: Mapped[str] = mapped_column(String(10), nullable=False, default="YEAR")
    next_value: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
