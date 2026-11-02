from datetime import datetime, date
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Date, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CustomerSegment(Base):
    """Group customers into market segments for targeting & reporting."""

    __tablename__ = "customer_segments"
    __table_args__ = (
        Index("ix_customer_segments_name", "name"),
        Index("ix_customer_segments_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class CustomerContact(Base):
    """Multiple contact persons per customer."""

    __tablename__ = "customer_contacts"
    __table_args__ = (
        Index("ix_customer_contacts_customer_id", "customer_id"),
        Index("ix_customer_contacts_email", "email"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    department: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class CustomerAddress(Base):
    """Billing / shipping addresses per customer."""

    __tablename__ = "customer_addresses"
    __table_args__ = (
        Index("ix_customer_addresses_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    address_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, default="billing")
    address_line1: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address_line2: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    country: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class OpportunityStage(Base):
    """Configurable sales pipeline stage (new -> qualification -> ... -> won/lost)."""

    __tablename__ = "opportunity_stages"
    __table_args__ = (
        Index("ix_opportunity_stages_position", "position"),
        Index("ix_opportunity_stages_is_active", "is_active"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    name_ar: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    probability: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    is_won: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    is_lost: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="#0ea5e9")
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class Opportunity(Base):
    """Sales pipeline deal linked to a customer and optionally a lead."""

    __tablename__ = "opportunities"
    __table_args__ = (
        Index("ix_opportunities_customer_id", "customer_id"),
        Index("ix_opportunities_lead_id", "lead_id"),
        Index("ix_opportunities_stage_id", "stage_id"),
        Index("ix_opportunities_status", "status"),
        Index("ix_opportunities_assigned_to", "assigned_to"),
        Index("ix_opportunities_company_id", "company_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    customer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    customer_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lead_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stage_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    probability: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    expected_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="OPEN")
    won_amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    closed_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    won_lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    company_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class FollowUp(Base):
    """Scheduled activities: calls, meetings, tasks, emails on any CRM entity."""

    __tablename__ = "follow_ups"
    __table_args__ = (
        Index("ix_follow_ups_entity", "entity_type", "entity_id"),
        Index("ix_follow_ups_due_date", "due_date"),
        Index("ix_follow_ups_assigned_to", "assigned_to"),
        Index("ix_follow_ups_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="lead")
    entity_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="call")
    subject: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reminder_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    priority: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="medium")
    status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, default="OPEN")
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)


class CustomerLoyalty(Base):
    """Loyalty points balance per customer."""

    __tablename__ = "customer_loyalty"
    __table_args__ = (
        Index("ix_customer_loyalty_customer_id", "customer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, nullable=False)
    points_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    total_points_earned: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True, default=0)
    tier: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, default="regular")
    last_earned_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)
