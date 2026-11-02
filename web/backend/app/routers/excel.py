"""
Excel import/export endpoints for accounting units and financial reports.

Exports serialize the SAME data/reports exposed by the existing JSON endpoints
(by re-using those functions) so numbers always match the UI. Imports validate
row-by-row and never partially commit a bad row: each imported row is either
applied or reported in the `errors` list.

All endpoints are grouped under /api/excel.
"""

from datetime import UTC, date, datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.accounting import Account, CostCenter, JournalEntry, JournalEntryLine
from app.models.currency import Currency
from app.models.tax import TaxRate
from app.models.user import User
from app.services import excel_service as xlsx
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log

# Reuse the live report functions so exports and UI stay in lock-step.
from app.routers.accounting import (
    trial_balance,
    general_ledger,
    cost_center_report,
    _generate_entry_number,
    _check_period_lock,
    _resolve_fiscal_period_id,
    _LEDGER_STATUSES,
    _ensure_account_code_index,
    _account_code_exists,
    _normalize_account_code,
    _normalize_account_name,
)
from app.routers.financial_statements import (
    get_income_statement,
    get_balance_sheet,
    get_cash_flow_statement,
)
from app.routers.taxes import get_vat_return
from app.routers.aging_reports import get_ar_aging, get_ap_aging

router = APIRouter()

XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

VALID_ACCOUNT_TYPES = {"asset", "liability", "equity", "revenue", "expense"}


# ── Helpers ──────────────────────────────────────────────────

def _xlsx_response(content: bytes, filename: str) -> Response:
    """Build a download response for .xlsx bytes."""
    return Response(
        content=content,
        media_type=XLSX_MEDIA,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _company_filter(current_user: User, column):
    """Replicate multi-company isolation used across the accounting routers."""
    if current_user.company_id:
        return (column == current_user.company_id) | (column.is_(None))
    return None


async def _paged(fn, *, per_page: int, max_pages: int = 200, **kwargs) -> dict:
    """Call a paginated report function repeatedly until all rows are fetched."""
    page = 1
    accumulator: dict[int, Any] = {}
    last_total = None
    while page <= max_pages:
        result = await fn(page=page, per_page=per_page, **kwargs)
        items = result.get("items")
        if items is None:
            items = result.get("transactions") or result.get("accounts") or []
        for item in items:
            key = item.get("id") or item.get("entry_number") or f"{page}-{len(accumulator)}"
            accumulator[key] = item
        last_total = result.get("total")
        if last_total is None:
            break
        if page * per_page >= last_total:
            break
        page += 1
    return {"total": last_total or len(accumulator), "items": list(accumulator.values())}


# ── Exports ──────────────────────────────────────────────────

@router.get("/exports/chart-of-accounts")
async def export_chart_of_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Account).where(Account.is_active == True).order_by(Account.account_code)
    )
    accounts = result.scalars().all()
    account_ids = [a.id for a in accounts]
    parent_codes = {}
    if account_ids:
        parents = await db.execute(select(Account.id, Account.account_code).where(
            Account.id.in_([a.parent_id for a in accounts if a.parent_id] or [0])
        ))
        parent_codes = {row.id: row.account_code for row in parents.all()}
    currency_codes = {}
    if account_ids:
        cids = {a.currency_id for a in accounts if a.currency_id}
        if cids:
            curs = await db.execute(select(Currency.id, Currency.code).where(Currency.id.in_(cids)))
            currency_codes = {row.id: row.code for row in curs.all()}
    journal_balances = {}
    if account_ids:
        balances = await db.execute(
            select(
                JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id.in_(account_ids), JournalEntry.status.in_(_LEDGER_STATUSES))
            .group_by(JournalEntryLine.account_id)
        )
        journal_balances = {row[0]: (float(row[1]), float(row[2])) for row in balances.all()}

    headers = ["code", "name", "name_ar", "name_en", "type", "parent_code",
               "is_control", "currency_code", "opening_balance", "balance"]
    rows = []
    for a in accounts:
        jb = journal_balances.get(a.id, (0, 0))
        is_expense_like = (a.account_type or "").lower() in ("asset", "expense")
        balance = float(a.opening_balance or 0) + (jb[0] - jb[1] if is_expense_like else jb[1] - jb[0])
        rows.append([
            a.account_code, a.account_name, a.account_name_ar, a.account_name_en,
            a.account_type, parent_codes.get(a.parent_id, ""),
            bool(a.is_control), currency_codes.get(a.currency_id, ""),
            float(a.opening_balance or 0), round(balance, 4),
        ])
    return _xlsx_response(
        xlsx.build_workbook("ChartOfAccounts", headers, rows),
        "chart-of-accounts.xlsx",
    )


@router.get("/exports/journal-entries")
async def export_journal_entries(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = (
        select(
            JournalEntry,
            JournalEntryLine,
            Account.account_code,
            Account.account_name,
            CostCenter.code.label("cc_code"),
            Currency.code.label("cur_code"),
        )
        .join(JournalEntryLine, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, Account.id == JournalEntryLine.account_id)
        .outerjoin(CostCenter, CostCenter.id == JournalEntryLine.cost_center_id)
        .outerjoin(Currency, Currency.id == JournalEntryLine.currency_id)
        .order_by(JournalEntry.entry_date, JournalEntry.id)
    )
    if status:
        query = query.where(JournalEntry.status == status)
    company_filter = _company_filter(current_user, JournalEntry.company_id)
    if company_filter is not None:
        query = query.where(company_filter)
    result = await db.execute(query)
    headers = ["entry_number", "entry_date", "status", "description",
               "reference_type", "reference_id", "account_code", "account_name",
               "cost_center_code", "currency_code", "debit", "credit"]
    rows = []
    for entry, line, acc_code, acc_name, cc_code, cur_code in result.all():
        entry_date = entry.entry_date
        if hasattr(entry_date, "isoformat"):
            entry_date = entry_date.isoformat()
        rows.append([
            entry.entry_number, str(entry_date), entry.status, entry.description,
            entry.reference_type, entry.reference_id, acc_code, acc_name,
            cc_code, cur_code, float(line.debit or 0), float(line.credit or 0),
        ])
    return _xlsx_response(
        xlsx.build_workbook("JournalEntries", headers, rows),
        "journal-entries.xlsx",
    )


@router.get("/exports/trial-balance")
async def export_trial_balance(
    fiscal_period_id: Optional[int] = Query(None),
    date: Optional[str] = Query(None),
    account_type: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await _paged(
        trial_balance, per_page=500,
        fiscal_period_id=fiscal_period_id, date=date, account_type=account_type,
        db=db, current_user=current_user,
    )
    headers = ["account_code", "account_name", "account_type",
               "opening_balance", "debit", "credit", "net_balance"]
    rows = [[
        a.get("account_code"), a.get("account_name"), a.get("account_type"),
        a.get("opening_balance", 0), a.get("debit", 0), a.get("credit", 0),
        a.get("net_balance", 0),
    ] for a in data["items"]]
    return _xlsx_response(
        xlsx.build_workbook("TrialBalance", headers, rows),
        "trial-balance.xlsx",
    )


@router.get("/exports/general-ledger")
async def export_general_ledger(
    account_id: int = Query(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    data = await _paged(
        general_ledger, per_page=500, account_id=account_id,
        from_date=from_date, to_date=to_date, db=db, current_user=current_user,
    )
    headers = ["entry_date", "entry_number", "description", "reference",
               "debit", "credit", "running_balance", "status"]
    rows = [[
        t.get("entry_date"), t.get("entry_number"), t.get("description"),
        t.get("reference"), t.get("debit", 0), t.get("credit", 0),
        t.get("running_balance", 0), t.get("status"),
    ] for t in data["items"]]
    acc = data.get("account") or {}
    body = xlsx.build_workbook("GeneralLedger", headers, rows)
    # prefixed meta row so the file names the account even when empty
    return _xlsx_response(body, f"general-ledger-{acc.get('code') or account_id}.xlsx")


@router.get("/exports/income-statement")
async def export_income_statement(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_income_statement(
        period_start=period_start, period_end=period_end,
        company_id=getattr(current_user, "company_id", None) or None,
        db=db, current_user=current_user,
    )
    headers = ["section", "account_code", "account_name", "amount"]
    rows = [("revenue", a.get("code"), a.get("name"), a.get("balance"))
            for a in report["revenue"]["accounts"]]
    rows += [("revenue", "", "إجمالي الإيرادات", report["revenue"]["total"])]
    rows += [("expense", a.get("code"), a.get("name"), a.get("balance"))
             for a in report["expenses"]["accounts"]]
    rows += [("expense", "", "إجمالي المصروفات", report["expenses"]["total"])]
    rows += [("summary", "", "صافي الربح", report["net_income"])]
    return _xlsx_response(
        xlsx.build_workbook("IncomeStatement", headers, rows),
        "income-statement.xlsx",
    )


@router.get("/exports/balance-sheet")
async def export_balance_sheet(
    as_of_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_balance_sheet(
        as_of_date=as_of_date,
        company_id=getattr(current_user, "company_id", None) or None,
        db=db, current_user=current_user,
    )
    headers = ["section", "account_code", "account_name", "balance"]
    rows = [("الأصول", a.get("code"), a.get("name"), a.get("balance"))
            for a in report["assets"]["accounts"]]
    rows += [("الأصول", "", "إجمالي الأصول", report["assets"]["total"])]
    rows += [("الالتزامات", a.get("code"), a.get("name"), a.get("balance"))
             for a in report["liabilities"]["accounts"]]
    rows += [("الالتزامات", "", "إجمالي الالتزامات", report["liabilities"]["total"])]
    rows += [("حقوق الملكية", a.get("code"), a.get("name"), a.get("balance"))
             for a in report["equity"]["accounts"]]
    rows += [("حقوق الملكية", "", "إجمالي حقوق الملكية", report["equity"]["total"])]
    rows += [("summary", "", "إجمالي الخصوم والملكية", report["total_liabilities_and_equity"])]
    return _xlsx_response(
        xlsx.build_workbook("BalanceSheet", headers, rows),
        "balance-sheet.xlsx",
    )


@router.get("/exports/cash-flow")
async def export_cash_flow(
    period_start: Optional[str] = Query(None),
    period_end: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_cash_flow_statement(
        period_start=period_start, period_end=period_end,
        company_id=getattr(current_user, "company_id", None) or None,
        db=db, current_user=current_user,
    )
    headers = ["section", "inflows", "outflows", "net"]
    sections = [
        ("التشغيلية", "operating_activities"),
        ("الاستثمارية", "investing_activities"),
        ("التمويلية", "financing_activities"),
    ]
    rows = [[label, report[key]["inflows"], report[key]["outflows"], report[key]["net"]]
            for label, key in sections]
    rows.append(["صافي التدفق النقدي", "", "", report["net_cash_flow"]])
    return _xlsx_response(
        xlsx.build_workbook("CashFlow", headers, rows),
        "cash-flow.xlsx",
    )


@router.get("/exports/cost-centers")
async def export_cost_centers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CostCenter).where(CostCenter.is_active == True).order_by(CostCenter.code)
    )
    headers = ["code", "name", "name_en", "parent_center_id", "is_active"]
    rows = [[c.code, c.name, c.name_en, c.parent_id, c.is_active]
            for c in result.scalars().all()]
    return _xlsx_response(
        xlsx.build_workbook("CostCenters", headers, rows), "cost-centers.xlsx"
    )


@router.get("/exports/cost-center-report")
async def export_cost_center_report(
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    fiscal_period_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cost-center activity report export (per-center + per-account rows)."""
    report = await cost_center_report(
        from_date=from_date, to_date=to_date, fiscal_period_id=fiscal_period_id,
        include_unallocated=True, db=db, current_user=current_user,
    )
    headers = ["center_code", "center_name", "account_code", "account_name",
               "debit", "credit", "net"]
    rows = []
    for center in report.get("centers", []):
        for acc in center.get("accounts", []):
            rows.append([center.get("code"), center.get("name"), acc.get("account_code"),
                         acc.get("account_name"), acc.get("debit"), acc.get("credit"),
                         acc.get("net")])
        rows.append([center.get("code"), center.get("name"), "", "إجمالي المركز",
                     center.get("total_debit"), center.get("total_credit"), center.get("net")])
    un = report.get("unallocated", {})
    if un.get("accounts"):
        for acc in un["accounts"]:
            rows.append(["", "غير موزع", acc.get("account_code"), acc.get("account_name"),
                         acc.get("debit"), acc.get("credit"), acc.get("net")])
        rows.append(["", "غير موزع", "", "الإجمالي غير الموزع",
                     un.get("total_debit"), un.get("total_credit"), un.get("net")])
    g = report.get("grand_total", {})
    rows.append(["", "الإجمالي الكلي", "", "", g.get("total_debit"), g.get("total_credit"), g.get("net")])
    return _xlsx_response(
        xlsx.build_workbook("CostCenterReport", headers, rows), "cost-center-report.xlsx"
    )


@router.get("/exports/currencies")
async def export_currencies(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Currency).order_by(Currency.code))
    headers = ["code", "name", "symbol", "decimal_places", "is_base_currency", "is_active"]
    rows = [[c.code, c.name or c.name_ar, c.symbol, c.decimal_places,
             c.is_base_currency, c.is_active] for c in result.scalars().all()]
    return _xlsx_response(
        xlsx.build_workbook("Currencies", headers, rows), "currencies.xlsx"
    )


@router.get("/exports/tax-rates")
async def export_tax_rates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(TaxRate).order_by(TaxRate.code))
    headers = ["code", "name", "rate", "tax_type", "applies_to",
               "is_recovery_allowed", "gl_account_code", "is_active"]
    rows = [[r.code, r.name, r.rate, r.tax_type, r.applies_to,
             r.is_recovery_allowed, r.gl_account_code, r.is_active]
            for r in result.scalars().all()]
    return _xlsx_response(
        xlsx.build_workbook("TaxRates", headers, rows), "tax-rates.xlsx"
    )


@router.get("/exports/vat-return")
async def export_vat_return(
    from_date: str = Query(...),
    to_date: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_vat_return(from_date=from_date, to_date=to_date,
                                  db=db, current_user=current_user)
    headers = ["item", "amount"]
    rows = [
        ("ضريبة المبيعات (الناتج)", report["output_vat"]),
        ("ضريبة المشتريات (المدخل)", report["input_vat"]),
        ("صافي الضريبة المستحقة", report["net_vat_due"]),
        ("حالة الاسترداد", "نعم" if report["is_refund"] else "لا"),
    ]
    return _xlsx_response(
        xlsx.build_workbook("VATReturn", headers, rows), f"vat-return-{from_date}-{to_date}.xlsx"
    )


@router.get("/exports/ar-aging")
async def export_ar_aging(
    as_of_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_ar_aging(
        as_of_date=(date.fromisoformat(as_of_date) if as_of_date else None),
        company_id=getattr(current_user, "company_id", None) or None,
        db=db, current_user=current_user,
    )
    headers = ["customer_code", "customer_name", "current", "1_30_days",
               "31_60_days", "61_90_days", "over_90_days", "outstanding_amount"]
    rows = [[c.get("customer_code"), c.get("customer_name"), c.get("current"),
             c.get("1_30_days"), c.get("31_60_days"), c.get("61_90_days"),
             c.get("over_90_days"), c.get("outstanding_amount")]
            for c in report.get("customers", [])]
    s = report.get("summary", {})
    rows.append(["الإجمالي", "", s.get("current"), s.get("1_30_days"),
                 s.get("31_60_days"), s.get("61_90_days"), s.get("over_90_days"),
                 s.get("total_outstanding")])
    return _xlsx_response(
        xlsx.build_workbook("AR-Aging", headers, rows), "ar-aging.xlsx"
    )


@router.get("/exports/ap-aging")
async def export_ap_aging(
    as_of_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = await get_ap_aging(
        as_of_date=(date.fromisoformat(as_of_date) if as_of_date else None),
        company_id=getattr(current_user, "company_id", None) or None,
        db=db, current_user=current_user,
    )
    headers = ["supplier_code", "supplier_name", "current", "1_30_days",
               "31_60_days", "61_90_days", "over_90_days", "outstanding_amount"]
    rows = [[s.get("supplier_code"), s.get("supplier_name"), s.get("current"),
             s.get("1_30_days"), s.get("31_60_days"), s.get("61_90_days"),
             s.get("over_90_days"), s.get("outstanding_amount")]
            for s in report.get("suppliers", [])]
    sm = report.get("summary", {})
    rows.append(["الإجمالي", "", sm.get("current"), sm.get("1_30_days"),
                 sm.get("31_60_days"), sm.get("61_90_days"), sm.get("over_90_days"),
                 sm.get("total_outstanding")])
    return _xlsx_response(
        xlsx.build_workbook("AP-Aging", headers, rows), "ap-aging.xlsx"
    )


# ── Templates ────────────────────────────────────────────────

@router.get("/templates/chart-of-accounts")
async def account_template(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    headers = ["code", "name", "name_ar", "name_en", "type", "parent_code",
               "is_control", "currency_code", "opening_balance"]
    sample = [
        ["1100", "النقدية", "النقدية", "Cash", "asset", "", "TRUE", "SAR", "0"],
        ["1110", "البنك", "البنك", "Bank", "asset", "1100", "FALSE", "SAR", "0"],
        ["4000", "المبيعات", "المبيعات", "Sales", "revenue", "", "FALSE", "SAR", "0"],
    ]
    return _xlsx_response(
        xlsx.build_workbook("ChartOfAccounts-Template", headers, sample),
        "chart-of-accounts-template.xlsx",
    )


@router.get("/templates/journal-entries")
async def journal_template(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    headers = ["entry_reference", "entry_date", "description", "account_code",
               "cost_center_code", "currency_code", "debit", "credit", "counterpart_code"]
    sample = [
        ["ADJ-001", "2026-01-31", "إثبات استهلاك", "5100", "", "SAR", "500", "0", ""],
        ["ADJ-001", "2026-01-31", "إثبات استهلاك", "1100", "", "SAR", "0", "500", ""],
        ["EXP-001", "2026-02-01", "مصاريف تشغيلية", "5200", "PRD", "USD", "120", "0", "1100"],
    ]
    return _xlsx_response(
        xlsx.build_workbook("JournalEntries-Template", headers, sample),
        "journal-entries-template.xlsx",
    )


# ── Imports ──────────────────────────────────────────────────

@router.post("/imports/chart-of-accounts")
async def import_chart_of_accounts(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    """Import chart of accounts from an Excel/CSV workbook.

    Expected columns: code, name, type (+ optional name_ar, name_en, parent_code,
    is_control, currency_code, opening_balance). Rows are validated one-by-one
    with the exact same rules as the interactive create/update endpoints:
      - codes are trimmed and matched case-insensitively (no duplicates),
      - a parent may reference a code defined earlier in the SAME sheet,
      - a child's type must match its parent's type,
      - control accounts may not carry an opening balance,
      - parents are automatically flagged as control accounts.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        headers, data = xlsx.parse_sheet(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Unreadable Excel file")

    col = {h.strip().lower(): i for i, h in enumerate(headers) if h.strip()}
    required = ["code", "name", "type"]
    missing = [r for r in required if r not in col]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing required columns: {', '.join(missing)}")

    await _ensure_account_code_index(db)

    def _cell(row: list, key: str):
        if key not in col or len(row) <= col[key] or row[col[key]] is None:
            return None
        return row[col[key]]

    errors: list[dict] = []
    failed: int = 0

    # ── Pass 0: scan every row; index in-file codes + referenced parents ──
    file_meta: dict[str, str] = {}          # lower(code) -> account_type
    referenced_parents: dict[str, list[int]] = {}  # lower(parent_code) -> child rows
    valid_rows: list[tuple[int, list]] = []        # (row_idx, raw_row)
    for row_idx, row in enumerate(data, start=2):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        code_raw = str(_cell(row, "code") or "").strip()
        if code_raw:
            file_meta[code_raw.lower()] = str(_cell(row, "type") or "").strip().lower()
        parent_raw = str(_cell(row, "parent_code") or "").strip()
        if parent_raw:
            referenced_parents.setdefault(parent_raw.lower(), []).append(row_idx)
        valid_rows.append((row_idx, row))

    # ── Pass 1: validate + create accounts (any failure skips JUST that row) ──
    parsed: list[tuple[int, Account, Optional[str]]] = []  # (row_idx, obj, parent_code_lower or None)
    created_map: dict[str, Account] = {}
    for row_idx, row in valid_rows:
        try:
            code = _normalize_account_code(str(_cell(row, "code") or ""))
            name = _normalize_account_name(str(_cell(row, "name") or ""))
            acc_type = str(_cell(row, "type") or "").strip().lower()
            if acc_type not in VALID_ACCOUNT_TYPES:
                raise ValueError(f"نوع الحساب غير صالح: {acc_type or '(فارغ)'}")

            code_lower = code.lower()
            if code_lower in created_map:
                raise ValueError(f"كود الحساب {code} مكرر في الملف")
            if await _account_code_exists(db, code):
                raise ValueError(f"كود الحساب {code} موجود مسبقاً")

            is_control_flag = False
            raw_flag = _cell(row, "is_control")
            if raw_flag is not None and str(raw_flag).strip():
                is_control_flag = str(raw_flag).strip().upper() in ("TRUE", "YES", "1", "نعم")

            opening_balance = 0.0
            raw_opening = _cell(row, "opening_balance")
            if raw_opening is not None and str(raw_opening).strip():
                try:
                    opening_balance = float(raw_opening)
                except (TypeError, ValueError):
                    raise ValueError(f"الرصيد الافتتاحي غير صالح: {raw_opening}")

            currency_id = None
            raw_ccy = _cell(row, "currency_code")
            if raw_ccy is not None and str(raw_ccy).strip():
                cur = await db.execute(select(Currency).where(Currency.code == str(raw_ccy).strip()))
                cur_obj = cur.scalar_one_or_none()
                if not cur_obj:
                    raise ValueError(f"العملة غير موجودة: {raw_ccy}")
                currency_id = cur_obj.id

            # Any code referenced as a parent (inside this file) becomes a
            # control/group account — and therefore cannot carry an opening balance.
            will_be_parent = code_lower in referenced_parents
            parent_code_lower = None
            parent_id_now = None
            raw_parent = _cell(row, "parent_code")
            if raw_parent is not None and str(raw_parent).strip():
                parent_code_lower = str(raw_parent).strip().lower()
                if code_lower == parent_code_lower:
                    raise ValueError("الحساب لا يمكن أن يكون أباً لنفسه")
                if parent_code_lower in file_meta:
                    # Parent defined within the same file: validate its type now,
                    # resolve the primary key after the batch flush.
                    if file_meta[parent_code_lower] != acc_type:
                        raise ValueError(
                            f"نوع الحساب {acc_type} يجب أن يطابق نوع الحساب الأب {file_meta[parent_code_lower]} (للأب {raw_parent})"
                        )
                else:
                    parent_res = await db.execute(
                        select(Account).where(Account.account_code == str(raw_parent).strip())
                    )
                    parent_acc = parent_res.scalar_one_or_none()
                    if parent_acc is None:
                        raise ValueError(f"الحساب الأب غير موجود: {raw_parent}")
                    if not parent_acc.is_active:
                        raise ValueError(f"الحساب الأب غير نشط: {raw_parent}")
                    if parent_acc.account_type != acc_type:
                        raise ValueError(
                            f"نوع الحساب {acc_type} يجب أن يطابق نوع الحساب الأب {parent_acc.account_type} (للأب {raw_parent})"
                        )
                    parent_id_now = parent_acc.id

            effective_is_control = is_control_flag or will_be_parent
            if effective_is_control and opening_balance != 0:
                raise ValueError(
                    f"حساب التحكم {code} لا يمكن أن يحمل رصيداً افتتاحياً"
                    + (" (تستخدم كحساب أب في الملف)" if will_be_parent else "")
                )
            if parent_id_now is None and parent_code_lower is not None:
                pass  # resolved post-flush

            account = Account(
                account_code=code, account_name=name,
                account_name_ar=(str(_cell(row, "name_ar") or "")).strip() or name,
                account_name_en=(str(_cell(row, "name_en") or "")).strip() or None,
                account_type=acc_type,
                is_control=effective_is_control, is_active=True,
                parent_id=parent_id_now, currency_id=currency_id,
                opening_balance=opening_balance,
                company_id=current_user.company_id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            )
            db.add(account)
            created_map[code_lower] = account
            parsed.append((row_idx, account, parent_code_lower))
        except Exception as e:
            failed += 1
            errors.append({"row": row_idx, "error": str(e)})

    await db.flush()

    # ── Pass 2: link same-file parents (ids now known; cannot fail) ────────
    for _, account, parent_code_lower in parsed:
        if parent_code_lower and parent_code_lower in created_map:
            parent = created_map[parent_code_lower]
            account.parent_id = parent.id
            parent.is_control = True

    await db.flush()
    created = len(parsed)
    await add_audit_log(db, "Account", 0, "IMPORT", current_user,
                        {"imported": created, "failed": failed, "kind": "chart-of-accounts"})
    return {"imported": created, "failed": failed, "errors": errors}


@router.post("/imports/journal-entries")
async def import_journal_entries(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("CREATE_JOURNAL")),
):
    """Import draft journal entries from a workbook.

    Group rows by `entry_reference` (blank reference = one line per entry).
    Every group must balance before its draft entry is created. Account codes
    must already exist in the chart of accounts.
    """
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        headers, data = xlsx.parse_sheet(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Unreadable Excel file")

    col = {h.strip().lower(): i for i, h in enumerate(headers) if h.strip()}
    required = ["entry_date", "description", "account_code"]
    missing = [r for r in required if r not in col]
    if missing:
        raise HTTPException(status_code=400,
                            detail=f"Missing required columns: {', '.join(missing)}")

    account_cache: dict[str, Optional[Account]] = {}
    cc_cache: dict[str, int] = {}
    currency_cache: dict[str, tuple[int, float]] = {}

    lines_by_group: dict[str, list] = {}
    order: list[str] = []

    for row_idx, row in enumerate(data, start=2):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        code_idx = col["account_code"]
        account_code = str(row[code_idx]).strip()
        if not account_code:
            continue
        if account_code not in account_cache:
            acc = await db.execute(select(Account).where(Account.account_code == account_code))
            account_cache[account_code] = acc.scalar_one_or_none()
        acc_obj = account_cache[account_code]

        ref = str(row[col["entry_reference"]]).strip() if "entry_reference" in col and row[col["entry_reference"]] else f"row{row_idx}"
        if ref not in lines_by_group:
            lines_by_group[ref] = []
            order.append(ref)

        if acc_obj is None:
            lines_by_group[ref].append({"row_idx": row_idx, "_error": f"الحساب غير موجود: {account_code}"})
            continue
        if not acc_obj.is_active:
            lines_by_group[ref].append({"row_idx": row_idx, "_error": f"الحساب {account_code} غير نشط"})
            continue
        if acc_obj.is_control:
            lines_by_group[ref].append({
                "row_idx": row_idx,
                "_error": f"الحساب {account_code} حساب علبة (تجمعي) ولا يقبل ترحيلاً مباشراً",
            })
            continue

        debit = float(row[col["debit"]] or 0) if "debit" in col and row[col["debit"]] not in (None, "") else 0.0
        credit = float(row[col["credit"]] or 0) if "credit" in col and row[col["credit"]] not in (None, "") else 0.0
        if debit <= 0 and credit <= 0:
            continue

        lines_by_group[ref].append({
            "row_idx": row_idx,
            "entry_date": str(row[col["entry_date"]]).strip(),
            "description": str(row[col["description"]]).strip() if row[col["description"]] is not None else "",
            "account_id": account_cache[account_code].id,
            "debit": debit,
            "credit": credit,
            "cost_center_id": None,
            "currency_id": None,
            "currency_rate": 1.0,
        })

    created, failed = 0, 0
    errors = []
    period_cache: dict[str, Optional[int]] = {}
    for ref in order:
        group = lines_by_group[ref]
        error_line = next((l for l in group if l.get("_error")), None)
        if error_line:
            failed += 1
            errors.append({"row": error_line["row_idx"], "error": error_line["_error"]})
            continue
        total_dr = sum(l["debit"] for l in group)
        total_cr = sum(l["credit"] for l in group)
        if abs(total_dr - total_cr) > 0.01:
            failed += 1
            errors.append({"row": group[0]["row_idx"], "error": f"القيد {ref} غير متوازن (مدين {total_dr} / دائن {total_cr})"})
            continue
        try:
            entry_date = datetime.fromisoformat(group[0]["entry_date"].replace("Z", "+00:00"))
        except ValueError:
            try:
                entry_date = datetime.strptime(group[0]["entry_date"], "%Y-%m-%d")
            except ValueError:
                failed += 1
                errors.append({"row": group[0]["row_idx"], "error": f"تاريخ غير صالح: {group[0]['entry_date']}"})
                continue

        # Guard against importing drafts into a closed / locked period and link
        # every imported entry to a covering fiscal period.
        date_key = group[0]["entry_date"]
        if date_key not in period_cache:
            period_cache[date_key] = await _resolve_fiscal_period_id(db, entry_date)
        period_id = period_cache[date_key]
        try:
            await _check_period_lock(db, period_id, entry_date)
        except HTTPException as exc:
            failed += 1
            errors.append({"row": group[0]["row_idx"], "error": f"القيد {ref}: {exc.detail}"})
            continue

        entry_number = await _generate_entry_number(db)
        entry = JournalEntry(
            entry_number=entry_number,
            entry_date=entry_date,
            fiscal_period_id=period_id,
            description=group[0]["description"] or f"استيراد Excel ({ref})",
            status="Draft",
            reference_type="ExcelImport",
            created_by=current_user.id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(entry)
        await db.flush()
        for line in group:
            db.add(JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=line["account_id"],
                description=line["description"] or None,
                debit=line["debit"],
                credit=line["credit"],
                cost_center_id=line["cost_center_id"],
                currency_id=line["currency_id"],
                currency_rate=line["currency_rate"],
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
        created += 1

    await db.flush()
    await add_audit_log(db, "JournalEntry", 0, "IMPORT", current_user,
                        {"imported": created, "failed": failed, "kind": "journal-entries"})
    return {"imported": created, "failed": failed, "errors": errors}


@router.post("/imports/tax-rates")
async def import_tax_rates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    """Import tax rates. Columns: code, name, rate, tax_type, applies_to,
    is_recovery_allowed, gl_account_code."""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        headers, data = xlsx.parse_sheet(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Unreadable Excel file")

    col = {h.strip().lower(): i for i, h in enumerate(headers) if h.strip()}
    required = ["code", "name", "rate"]
    if any(r not in col for r in required):
        raise HTTPException(status_code=400, detail="Missing required columns: code, name, rate")

    existing = set((await db.execute(select(TaxRate.code))).scalars().all())
    created, failed = 0, 0
    errors = []
    for row_idx, row in enumerate(data, start=2):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        try:
            code = str(row[col["code"]]).strip()
            if not code or code in existing:
                raise ValueError(f"كود الضريبة موجود: {code}")
            rate = float(row[col["rate"]])
            if rate < 0:
                raise ValueError("المعدل يجب ألا يكون سالباً")
            db.add(TaxRate(
                code=code,
                name=str(row[col["name"]]).strip(),
                name_ar=str(row[col["name_ar"]]).strip() if "name_ar" in col and row[col["name_ar"]] else None,
                rate=rate,
                tax_type=str(row[col["tax_type"]]).strip() if "tax_type" in col and row[col["tax_type"]] else "VAT",
                applies_to=str(row[col["applies_to"]]).strip() if "applies_to" in col and row[col["applies_to"]] else "both",
                is_recovery_allowed=bool(row[col["is_recovery_allowed"]]) if "is_recovery_allowed" in col and row[col["is_recovery_allowed"]] not in (None, "") else True,
                gl_account_code=str(row[col["gl_account_code"]]).strip() if "gl_account_code" in col and row[col["gl_account_code"]] else None,
                is_active=True,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
            existing.add(code)
            created += 1
        except Exception as e:
            failed += 1
            errors.append({"row": row_idx, "error": str(e)})
    await db.flush()
    await add_audit_log(db, "TaxRate", 0, "IMPORT", current_user,
                        {"imported": created, "failed": failed})
    return {"imported": created, "failed": failed, "errors": errors}


@router.post("/imports/exchange-rates")
async def import_exchange_rates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import exchange rates. Columns: from_currency_code, to_currency_code,
    rate, effective_date."""
    from app.models.currency import ExchangeRate

    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        headers, data = xlsx.parse_sheet(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Unreadable Excel file")

    col = {h.strip().lower(): i for i, h in enumerate(headers) if h.strip()}
    required = ["from_currency_code", "to_currency_code", "rate"]
    if any(r not in col for r in required):
        raise HTTPException(status_code=400,
                            detail="Missing required columns: from_currency_code, to_currency_code, rate")

    defined = set((await db.execute(select(Currency.code))).scalars().all())
    created, failed = 0, 0
    errors = []
    for row_idx, row in enumerate(data, start=2):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        try:
            from_code = str(row[col["from_currency_code"]]).strip()
            to_code = str(row[col["to_currency_code"]]).strip()
            if from_code not in defined or to_code not in defined:
                raise ValueError(f"عملة غير معرّفة: {from_code}/{to_code}")
            rate = float(row[col["rate"]])
            if rate <= 0:
                raise ValueError("سعر الصرف يجب أن يكون موجباً")
            effective_date = None
            if "effective_date" in col and row[col["effective_date"]]:
                try:
                    effective_date = datetime.fromisoformat(str(row[col["effective_date"]]).replace("Z", "+00:00"))
                except ValueError:
                    effective_date = datetime.strptime(str(row[col["effective_date"]]), "%Y-%m-%d")
            db.add(ExchangeRate(
                from_currency_code=from_code,
                to_currency_code=to_code,
                rate=rate,
                effective_date=effective_date or datetime.now(UTC).replace(tzinfo=None),
                is_active=True,
                created_by=current_user.id,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
            created += 1
        except Exception as e:
            failed += 1
            errors.append({"row": row_idx, "error": str(e)})
    await db.flush()
    await add_audit_log(db, "ExchangeRate", 0, "IMPORT", current_user,
                        {"imported": created, "failed": failed})
    return {"imported": created, "failed": failed, "errors": errors}


@router.post("/imports/cost-centers")
async def import_cost_centers(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    """Import cost centers. Columns: code, name (+ optional name_en, parent_code)."""
    raw = await file.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Empty file")
    try:
        headers, data = xlsx.parse_sheet(raw)
    except Exception:
        raise HTTPException(status_code=400, detail="Unreadable Excel file")

    col = {h.strip().lower(): i for i, h in enumerate(headers) if h.strip()}
    if "code" not in col or "name" not in col:
        raise HTTPException(status_code=400, detail="Missing required columns: code, name")

    existing = set((await db.execute(select(CostCenter.code))).scalars().all())
    created, failed = 0, 0
    errors = []
    for row_idx, row in enumerate(data, start=2):
        if not any(c is not None and str(c).strip() for c in row):
            continue
        try:
            code = str(row[col["code"]]).strip()
            name = str(row[col["name"]]).strip()
            if not code or not name:
                raise ValueError("code/name مطلوبة")
            if code in existing:
                raise ValueError(f"مركز التكلفة موجود: {code}")
            parent_id = None
            if "parent_code" in col and row[col["parent_code"]]:
                parent_code = str(row[col["parent_code"]]).strip()
                if parent_code:
                    parent = await db.execute(select(CostCenter).where(CostCenter.code == parent_code))
                    parent_cc = parent.scalar_one_or_none()
                    if not parent_cc:
                        raise ValueError(f"مركز التكلفة الأب غير موجود: {parent_code}")
                    parent_id = parent_cc.id
            db.add(CostCenter(
                code=code,
                name=name,
                name_en=str(row[col["name_en"]]).strip() if "name_en" in col and row[col["name_en"]] else None,
                parent_id=parent_id,
                is_active=True,
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
            existing.add(code)
            created += 1
        except Exception as e:
            failed += 1
            errors.append({"row": row_idx, "error": str(e)})
    await db.flush()
    await add_audit_log(db, "CostCenter", 0, "IMPORT", current_user,
                        {"imported": created, "failed": failed})
    return {"imported": created, "failed": failed, "errors": errors}