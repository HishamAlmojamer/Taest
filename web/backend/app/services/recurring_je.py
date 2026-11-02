"""
Recurring journal entry template service.

Shared entry-creation logic used by both the manual "run now" flow and the
background scheduler. The scheduler has no authenticated user, so actors are
expressed as `actor_user_id`/`company_id` and an optional `actor_name`.
"""

import json
from datetime import UTC, datetime
from typing import Optional

from dateutil.relativedelta import relativedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.accounting import JournalEntry, JournalEntryLine, RecurringJETemplate
from app.utils.audit import add_audit_log

_FREQ_MAP = {
    "WEEKLY": relativedelta(weeks=1),
    "MONTHLY": relativedelta(months=1),
    "QUARTERLY": relativedelta(months=3),
    "YEARLY": relativedelta(years=1),
}


def normalize_frequency(freq: Optional[str]) -> str:
    """Normalize recurring frequency to the canonical uppercase value."""
    if not freq:
        return "MONTHLY"
    f = freq.strip().upper()
    alias = {
        "WEEK": "WEEKLY",
        "MONTH": "MONTHLY",
        "QUARTER": "QUARTERLY",
        "YEAR": "YEARLY",
        "ANNUAL": "YEARLY",
    }
    return alias.get(f, f)


async def _generate_entry_number(db: AsyncSession) -> str:
    """Generate a unique journal entry number using the PostgreSQL sequence."""
    from app.routers.accounting import _generate_entry_number as _shared
    return await _shared(db)


def compute_run_plan(template: RecurringJETemplate) -> Optional[dict]:
    """
    Compute the journal entry that would be generated from this template
    WITHOUT persisting anything. Returns the raw plan dict or None if the
    template has no usable lines.
    """
    if not template.template_data:
        return None
    try:
        td = json.loads(template.template_data)
        # Handle doubly-JSON-encoded template_data (legacy bug: json.dumps of
        # an already-encoded string). Keep decoding until we reach a dict.
        decodes = 0
        while isinstance(td, str) and decodes < 3:
            td = json.loads(td)
            decodes += 1
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(td, dict):
        return None
    lines = td.get("lines") or []
    if not lines:
        return None
    total_debit = sum(float(l.get("debit") or 0) for l in lines)
    total_credit = sum(float(l.get("credit") or 0) for l in lines)
    return {
        "description": td.get("description") or template.name,
        "lines": lines,
        "total_debit": total_debit,
        "total_credit": total_credit,
        "balanced": abs(total_debit - total_credit) <= 0.01,
    }


async def create_entry_from_template(
    db: AsyncSession,
    template: RecurringJETemplate,
    *,
    entry_date=None,
    actor_user_id: Optional[int] = None,
    company_id: Optional[int] = None,
    actor_name: Optional[str] = None,
    source: str = "recurring_template",
) -> JournalEntry:
    """Create and immediately post a JournalEntry from the template's lines.

    Raises ValueError if the template is missing lines or is unbalanced. The
    caller is responsible for committing the transaction.
    """
    plan = compute_run_plan(template)
    if plan is None:
        raise ValueError("Template has no journal lines defined")
    if not plan["balanced"]:
        raise ValueError(
            f"Template debits ({plan['total_debit']}) != credits ({plan['total_credit']})"
        )

    now = datetime.now(UTC).replace(tzinfo=None)
    entry_number = await _generate_entry_number(db)

    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=entry_date or now,
        description=plan["description"],
        status="Posted",
        created_by=actor_user_id,
        posted_by=actor_user_id,
        posted_at=now,
        created_at=now,
        company_id=company_id,
    )
    db.add(entry)
    await db.flush()

    for line in plan["lines"]:
        db.add(JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=line["account_id"],
            description=line.get("description"),
            debit=line.get("debit", 0),
            credit=line.get("credit", 0),
            partner_id=line.get("partner_id"),
            project_id=line.get("project_id"),
            currency_id=line.get("currency_id"),
            currency_rate=line.get("currency_rate"),
            created_at=now,
        ))

    changes = {"entry_number": entry_number, "source": source}
    await add_audit_log(db, "JournalEntry", entry.id, "POST", None,
                        changes, company_id=company_id)
    return entry


def advance_next_run_date(template: RecurringJETemplate, now=None) -> datetime:
    """Compute the next_run_date after a successful run."""
    now = now or datetime.now(UTC).replace(tzinfo=None)
    delta = _FREQ_MAP.get(normalize_frequency(template.frequency), relativedelta(months=1))
    return now + delta


async def mark_template_run(
    db: AsyncSession, template_id: int, *, last_run_date, next_run_date
):
    """Update a template's last/next run timestamps."""
    await db.execute(
        update(RecurringJETemplate)
        .where(RecurringJETemplate.id == template_id)
        .values(
            last_run_date=last_run_date,
            next_run_date=next_run_date,
            updated_at=last_run_date,
        )
    )
    await db.flush()


async def run_template(db: AsyncSession, template: RecurringJETemplate, *, company_id=None, actor_user_id=None) -> JournalEntry:
    """Run (execute + advance schedule) a single template within an open tx."""
    entry = await create_entry_from_template(
        db, template, company_id=company_id, actor_user_id=actor_user_id,
    )
    now = datetime.now(UTC).replace(tzinfo=None)
    await mark_template_run(db, template.id, last_run_date=now, next_run_date=advance_next_run_date(template, now))
    return entry


async def fetch_due_templates(db: AsyncSession, as_of=None) -> list:
    """Fetch active templates whose next_run_date is due (<= as_of)."""
    as_of = as_of or datetime.now(UTC).replace(tzinfo=None)
    result = await db.execute(
        select(RecurringJETemplate)
        .where(
            RecurringJETemplate.is_active == True,  # noqa: E712
            RecurringJETemplate.next_run_date.isnot(None),
            RecurringJETemplate.next_run_date <= as_of,
        )
        .order_by(RecurringJETemplate.next_run_date.asc())
    )
    return result.scalars().all()
