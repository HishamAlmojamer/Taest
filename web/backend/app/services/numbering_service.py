"""
Configurable document numbering service.

Provides generation and preview of per-document-type sequences backed by the
`document_numbering` table, so each document type keeps an independent,
contiguous counter independent of primary keys.
"""

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.numbering import DocumentNumbering


def _year_str(period, now=None) -> str:
    now = now or datetime.now(UTC).replace(tzinfo=None)
    if period == "YEAR":
        return str(now.year)
    if period == "MONTH":
        return f"{now.year}{now.month:02d}"
    if period == "NO_PERIOD":
        return ""
    return str(now.year)


def render_number(numbering: DocumentNumbering, value: int = None, now=None) -> str:
    """Render the formatted document number from the numbering config."""
    n = int(value if value is not None else numbering.next_value)
    sep = numbering.separator or ""
    parts = []
    if numbering.prefix:
        parts.append(numbering.prefix)
    period = _year_str(numbering.period or "YEAR", now)
    if period and numbering.include_year:
        parts.append(period)
    body = str(n).zfill(numbering.zero_padding)
    return sep.join(parts + [body]) + (f"{sep}{numbering.suffix}" if numbering.suffix else "")


async def get_numbering(db: AsyncSession, doc_type: str) -> Optional[DocumentNumbering]:
    result = await db.execute(select(DocumentNumbering).where(DocumentNumbering.doc_type == doc_type))
    return result.scalar_one_or_none()


async def get_or_create_numbering(db: AsyncSession, doc_type: str, **defaults) -> DocumentNumbering:
    numbering = await get_numbering(db, doc_type)
    if numbering:
        return numbering
    numbering = DocumentNumbering(
        doc_type=doc_type,
        name=defaults.get("name", doc_type),
        name_ar=defaults.get("name_ar"),
        prefix=defaults.get("prefix", ""),
        zero_padding=defaults.get("zero_padding", 6),
        include_year=defaults.get("include_year", True),
        separator=defaults.get("separator", "-"),
        period=defaults.get("period", "YEAR"),
        next_value=defaults.get("next_value", 1),
        is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(numbering)
    await db.flush()
    return numbering


async def generate_next_number(db: AsyncSession, doc_type: str, **defaults) -> str:
    """Allocate and store the next number for the document type."""
    numbering = await get_or_create_numbering(db, doc_type, **defaults)
    current = numbering.next_value
    number = render_number(numbering, current)
    numbering.next_value = current + 1
    numbering.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return number


async def reset_counter(db: AsyncSession, doc_type: str, next_value: int) -> Optional[DocumentNumbering]:
    numbering = await get_numbering(db, doc_type)
    if not numbering:
        return None
    numbering.next_value = max(1, int(next_value))
    numbering.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return numbering
