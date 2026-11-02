"""
Generic Workflow state-machine model.

A workflow is described by a set of transitions between states for a given
entity type. Default transitions are defined in code (see
``app.services.workflow_engine``); rows in this table override or disable the
defaults and allow administrators to attach amount / branch conditions and a
required permission per transition.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Text, Numeric, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class WorkflowTransition(Base):
    __tablename__ = "workflow_transitions"
    __table_args__ = (
        Index("ix_workflow_transitions_entity", "entity_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str] = mapped_column(String(50), nullable=False)
    to_status: Mapped[str] = mapped_column(String(50), nullable=False)
    required_permission: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    requires_reason: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    min_amount: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    max_amount: Mapped[Optional[float]] = mapped_column(Numeric(18, 4), nullable=True)
    branch_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    label: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
