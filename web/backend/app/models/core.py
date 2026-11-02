from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class AppSetting(Base):
    __tablename__ = "app_settings"
    __table_args__ = (Index("ix_app_settings_key", "key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    group: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_visible: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class WorkflowRule(Base):
    __tablename__ = "workflow_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    module: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    condition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approver_role: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tax_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    registration_no: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    website: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    default_currency: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    fiscal_year_start: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date_format: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    manager: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
