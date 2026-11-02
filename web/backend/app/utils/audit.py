"""
Audit logging utilities.

Provides a helper to write audit trail entries (audit_logs table) throughout
the application. Previously the table existed but nothing ever wrote to it.
"""

import json
from datetime import UTC, datetime
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


def _now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


async def add_audit_log(
    db: AsyncSession,
    entity_type: str,
    entity_id: int,
    action: str,
    user=None,
    changes: Optional[dict] = None,
    company_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Record an audit log entry. Commits are left to the caller."""
    user_name = None
    user_id = None
    if user is not None:
        user_id = getattr(user, "id", None)
        user_name = getattr(user, "username", None) or getattr(user, "full_name", None)

    log = AuditLog(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes_json=json.dumps(changes, ensure_ascii=False, default=str) if changes is not None else None,
        user_id=user_id,
        user_name=user_name,
        ip_address=ip_address,
        company_id=company_id,
        created_at=_now(),
    )
    db.add(log)
    await db.flush()
    return log
