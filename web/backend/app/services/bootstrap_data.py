"""First-run seed data for an empty database (non-destructive).

Creates a company, branch, fiscal year/periods and the chart of accounts when
the corresponding tables are empty. Existing installations are never modified.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)


def _month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    start = datetime(year, month, 1)
    end = next_month.replace(hour=23, minute=59, second=59, microsecond=0)
    return start, end


async def seed_default_data(conn, company_name: str, branch_name: str) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)

    company_id = (
        await conn.execute(text("SELECT id FROM companies ORDER BY id LIMIT 1"))
    ).scalar()
    if company_id is None:
        company_id = (
            await conn.execute(
                text(
                    """
                    INSERT INTO companies
                        (code, name, name_en, default_currency, fiscal_year_start,
                         date_format, is_active, created_at)
                    VALUES
                        ('COMP-001', :name, :name, 'SAR', '01-01', 'YYYY-MM-DD', true, :now)
                    RETURNING id
                    """
                ),
                {"name": company_name, "now": now},
            )
        ).scalar()
        logger.info("Seeded default company #%s", company_id)

    branch_id = (
        await conn.execute(text("SELECT id FROM branches ORDER BY id LIMIT 1"))
    ).scalar()
    if branch_id is None:
        await conn.execute(
            text(
                """
                INSERT INTO branches
                    (company_id, code, name, name_en, is_active, created_at)
                VALUES
                    (:company_id, 'BR-001', :name, :name, true, :now)
                """
            ),
            {"company_id": company_id, "name": branch_name, "now": now},
        )
        logger.info("Seeded default branch")

    year = now.year
    fiscal_year_id = (
        await conn.execute(
            text("SELECT id FROM fiscal_years WHERE company_id = :cid ORDER BY id LIMIT 1"),
            {"cid": company_id},
        )
    ).scalar()
    if fiscal_year_id is None:
        fiscal_year_id = (
            await conn.execute(
                text(
                    """
                    INSERT INTO fiscal_years
                        (name, name_en, start_date, end_date, is_closed,
                         opening_balances_posted, company_id, created_at)
                    VALUES
                        (:name, :name_en, :start, :end, false, false, :cid, :now)
                    RETURNING id
                    """
                ),
                {
                    "name": f"FY {year}",
                    "name_en": f"FY {year}",
                    "start": datetime(year, 1, 1),
                    "end": datetime(year, 12, 31, 23, 59, 59),
                    "cid": company_id,
                    "now": now,
                },
            )
        ).scalar()
        logger.info("Seeded fiscal year %s", year)

    period_count = (
        await conn.execute(
            text("SELECT COUNT(*) FROM fiscal_periods WHERE fiscal_year_id = :fy"),
            {"fy": fiscal_year_id},
        )
    ).scalar() or 0
    if period_count == 0:
        for month in range(1, 13):
            start, end = _month_bounds(year, month)
            await conn.execute(
                text(
                    """
                    INSERT INTO fiscal_periods
                        (fiscal_year_id, name, name_en, start_date, end_date,
                         is_closed, is_locked, is_soft_closed, created_at)
                    VALUES
                        (:fy, :name, :name_en, :start, :end, false, false, false, :now)
                    """
                ),
                {
                    "fy": fiscal_year_id,
                    "name": f"{year}-{month:02d}",
                    "name_en": f"{year}-{month:02d}",
                    "start": start,
                    "end": end,
                    "now": now,
                },
            )
        logger.info("Seeded 12 fiscal periods for %s", year)

    account_count = (
        await conn.execute(text("SELECT COUNT(*) FROM accounts"))
    ).scalar() or 0
    if account_count == 0:
        from app.seed_chart_of_accounts import ACCOUNTS

        code_map: dict[str, int] = {}
        for acc in ACCOUNTS:
            parent_code = acc.get("parent")
            parent_id = code_map.get(parent_code) if parent_code else None
            account_id = (
                await conn.execute(
                    text(
                        """
                        INSERT INTO accounts
                            (account_code, account_name, account_name_en, account_name_ar,
                             account_type, parent_id, is_control, is_active,
                             opening_balance, company_id, created_at, updated_at)
                        VALUES
                            (:code, :name, :name_en, :name_ar, :type, :parent_id,
                             :is_control, true, 0, :company_id, :now, :now)
                        RETURNING id
                        """
                    ),
                    {
                        "code": acc["code"],
                        "name": acc["name"],
                        "name_en": acc.get("name_en"),
                        "name_ar": acc.get("name_ar"),
                        "type": acc["type"],
                        "parent_id": parent_id,
                        "is_control": acc.get("control", False),
                        "company_id": company_id,
                        "now": now,
                    },
                )
            ).scalar()
            code_map[acc["code"]] = account_id
        logger.info("Seeded %s chart-of-accounts entries", len(ACCOUNTS))
