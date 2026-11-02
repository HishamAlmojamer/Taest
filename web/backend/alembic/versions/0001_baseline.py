"""Baseline schema (full metadata, idempotent)

This is the initial baseline for databases created before Alembic was wired
in. On a fresh database it creates the complete schema; on an existing one
``create_all(checkfirst=True)`` is a no-op for the tables that already exist.

Revision ID: 0001_baseline
Revises:
Create Date: 2026-11-02
"""
from typing import Sequence, Union

from alembic import op

from app.database import Base
import app.models  # noqa: F401

revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind(), checkfirst=True)


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind(), checkfirst=True)
