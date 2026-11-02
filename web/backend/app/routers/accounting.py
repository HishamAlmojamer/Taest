import math
import re
from datetime import UTC, datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, text, or_
from app.database import get_db
from app.models.accounting import Account, JournalEntry, JournalEntryLine, FiscalPeriod, CostCenter, RecurringJETemplate
from app.models.cost_allocation import CostCenterAllocationRule, CostCenterAllocationRuleLine
from app.models.user import User
from app.schemas.accounting import AccountCreate, AccountResponse, AccountTreeNode, JournalEntryCreate, CostCenterCreate, FiscalPeriodCreate
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log

router = APIRouter()

VALID_ACCOUNT_TYPES = {"asset", "liability", "equity", "revenue", "expense"}

# Canonical journal-entry statuses (single source of truth).
JE_STATUS_DRAFT = "Draft"
JE_STATUS_POSTED = "Posted"
JE_STATUS_VOIDED = "Voided"

# Statuses that enter the ledger. Voiding marks the original 'Voided' and posts
# an equal-and-opposite reversal, so BOTH must be aggregated for the pair to
# net to zero (otherwise a void would double-apply the reversal).
_LEDGER_STATUSES = (JE_STATUS_POSTED, JE_STATUS_VOIDED)

# Alias map used to normalize the `status` query filter (case-insensitive).
_JE_STATUS_ALIASES = {
    "draft": JE_STATUS_DRAFT,
    "posted": JE_STATUS_POSTED,
    "voided": JE_STATUS_VOIDED,
    "void": JE_STATUS_VOIDED,
    "reversed": JE_STATUS_VOIDED,
    "cancelled": JE_STATUS_VOIDED,
    "canceled": JE_STATUS_VOIDED,
    JE_STATUS_DRAFT.lower(): JE_STATUS_DRAFT,
    JE_STATUS_POSTED.lower(): JE_STATUS_POSTED,
    JE_STATUS_VOIDED.lower(): JE_STATUS_VOIDED,
}


# ── Helpers ──────────────────────────────────────────────────

async def _check_period_lock(db: AsyncSession, fiscal_period_id: int | None, entry_date: datetime | None = None):
    """Raise 400 if the target fiscal period is soft-closed, locked, or closed.

    Resolves the period explicitly by id, or by the covering period for
    ``entry_date`` when no id is provided (so postings into a closed period are
    rejected even when the caller did not pass a period id).
    """
    from app.services.fiscal_period_guard import check_period_open

    period = await check_period_open(db, entry_date or datetime.now(), fiscal_period_id)
    if period is None and fiscal_period_id is not None:
        raise HTTPException(status_code=400, detail="Fiscal period not found")

async def _compute_balance(db: AsyncSession, account_id: int) -> float:
    result = await db.execute(
        select(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntryLine.account_id == account_id, JournalEntry.status.in_(_LEDGER_STATUSES))
    )
    row = result.one_or_none()
    total_debit = float(row.total_debit) if row else 0
    total_credit = float(row.total_credit) if row else 0

    account_result = await db.execute(select(Account).where(Account.id == account_id))
    account = account_result.scalar_one_or_none()
    opening = float(account.opening_balance or 0) if account else 0

    account_type = (account.account_type or "").lower() if account else ""
    if account_type in ("asset", "expense"):
        return opening + total_debit - total_credit
    return opening + total_credit - total_debit


async def _compute_cumulative_balance(db: AsyncSession, account_id: int) -> float:
    """Balance of an account plus the balances of all its descendants."""
    balance = await _compute_balance(db, account_id)
    children_result = await db.execute(
        select(Account).where(Account.parent_id == account_id, Account.is_active == True)
    )
    for child in children_result.scalars().all():
        balance += await _compute_cumulative_balance(db, child.id)
    return balance


async def _get_descendant_ids(db: AsyncSession, account_id: int) -> set[int]:
    """Return all descendant account ids (excluding ``account_id`` itself).

    Used to prevent moving an account under one of its own descendants
    (which would create a cycle in the chart of accounts tree).
    """
    descendant_ids: set[int] = set()
    frontier = [account_id]
    while frontier:
        rows = await db.execute(select(Account.id).where(Account.parent_id.in_(frontier)))
        next_frontier = []
        for (child_id,) in rows.all():
            if child_id != account_id and child_id not in descendant_ids:
                descendant_ids.add(child_id)
                next_frontier.append(child_id)
        frontier = next_frontier
    return descendant_ids


async def _validate_journal_accounts(db: AsyncSession, account_ids: list[int]) -> None:
    """Validate accounts used in journal lines before any write.

    Enforces the chart-of-accounts posting rules:
      - the account must exist,
      - the account must be active,
      - the account must NOT be a control / group account (control accounts
        only aggregate their children and cannot receive direct postings).
    Raises HTTPException(400) on the first violation.
    """
    if not account_ids:
        raise HTTPException(status_code=400, detail="Journal entry must have at least one line")
    rows = await db.execute(select(Account).where(Account.id.in_(set(account_ids))))
    accounts = {a.id: a for a in rows.scalars().all()}
    for aid in account_ids:
        account = accounts.get(aid)
        if not account:
            raise HTTPException(status_code=400, detail=f"Account id {aid} not found")
        if not account.is_active:
            raise HTTPException(status_code=400, detail=f"Account '{account.account_code}' is inactive")
        if account.is_control:
            raise HTTPException(
                status_code=400,
                detail=f"Account '{account.account_code}' is a control (group) account and cannot receive postings. Use a leaf account instead.",
            )


def _line_amounts(line) -> tuple[float, float]:
    """Return (debit, credit) for a journal line given as dict or ORM object."""
    if isinstance(line, dict):
        return float(line.get("debit", 0) or 0), float(line.get("credit", 0) or 0)
    return float(getattr(line, "debit", 0) or 0), float(getattr(line, "credit", 0) or 0)


def _validate_journal_lines(lines) -> tuple[float, float]:
    """Validate double-entry lines and return (total_debit, total_credit).

    Raises HTTPException(400) when there are fewer than 2 lines, any line has a
    negative amount, both amounts zero, both amounts positive, or when the
    totals are not balanced (tolerance 0.01).
    """
    if not lines or len(lines) < 2:
        raise HTTPException(status_code=400, detail="Journal entry must have at least 2 lines")

    total_debit = 0.0
    total_credit = 0.0
    for idx, line in enumerate(lines, start=1):
        debit, credit = _line_amounts(line)
        if debit < 0 or credit < 0:
            raise HTTPException(status_code=400, detail=f"Line {idx}: Debit and Credit values must be >= 0")
        if debit == 0 and credit == 0:
            raise HTTPException(status_code=400, detail=f"Line {idx}: Either debit or credit must be > 0")
        if debit > 0 and credit > 0:
            raise HTTPException(status_code=400, detail=f"Line {idx}: Cannot have both debit and credit on the same line")
        total_debit += debit
        total_credit += credit

    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Journal entry is not balanced. Debits: {total_debit:.4f}, Credits: {total_credit:.4f}",
        )
    return total_debit, total_credit


async def _resolve_fiscal_period_id(db: AsyncSession, entry_date: datetime) -> Optional[int]:
    """Return the id of the narrowest fiscal period covering ``entry_date``.

    When several periods overlap the returned one is the one with the earliest
    end date (i.e. the most specific). Returns ``None`` when no period applies.
    """
    if entry_date is None:
        return None
    period_result = await db.execute(
        select(FiscalPeriod)
        .where(FiscalPeriod.start_date <= entry_date)
        .where(FiscalPeriod.end_date >= entry_date)
        .order_by(FiscalPeriod.end_date.asc())
        .limit(1)
    )
    period = period_result.scalar_one_or_none()
    return period.id if period else None


async def _enrich_journal_lines(db: AsyncSession, lines) -> list[dict]:
    """Serialize journal lines and attach account/cost-center lookup fields."""
    account_ids = {l.account_id for l in lines if l.account_id is not None}
    cost_center_ids = {l.cost_center_id for l in lines if l.cost_center_id is not None}

    accounts: dict[int, Account] = {}
    if account_ids:
        acc_result = await db.execute(select(Account).where(Account.id.in_(account_ids)))
        accounts = {a.id: a for a in acc_result.scalars().all()}

    cost_centers: dict[int, CostCenter] = {}
    if cost_center_ids:
        cc_result = await db.execute(select(CostCenter).where(CostCenter.id.in_(cost_center_ids)))
        cost_centers = {c.id: c for c in cc_result.scalars().all()}

    output = []
    for l in lines:
        account = accounts.get(l.account_id)
        cost_center = cost_centers.get(l.cost_center_id) if l.cost_center_id else None
        output.append({
            "id": l.id, "journal_entry_id": l.journal_entry_id, "account_id": l.account_id,
            "account_code": account.account_code if account else None,
            "account_name": account.account_name if account else None,
            "description": l.description, "debit": float(l.debit or 0), "credit": float(l.credit or 0),
            "currency_rate": l.currency_rate, "cost_center_id": l.cost_center_id,
            "cost_center_code": cost_center.code if cost_center else None,
            "cost_center_name": cost_center.name if cost_center else None,
        })
    return output


_ACCOUNT_CODE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/\-]*$")
_CODE_INDEX_READY = False


def _normalize_account_code(value: str) -> str:
    """Validate and normalize an account code (trim, enforce charset/length)."""
    code = (value or "").strip()
    if not code:
        raise HTTPException(status_code=400, detail="Account code is required")
    if len(code) > 100:
        raise HTTPException(status_code=400, detail="Account code must be at most 100 characters")
    if not _ACCOUNT_CODE_RE.match(code):
        raise HTTPException(
            status_code=400,
            detail="Account code may only contain letters, digits and the characters '.', '_', '/', '-' (no spaces)",
        )
    return code


def _normalize_account_name(value: Optional[str]) -> str:
    name = (value or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Account name is required")
    if len(name) > 200:
        raise HTTPException(status_code=400, detail="Account name must be at most 200 characters")
    return name


async def _account_code_exists(db: AsyncSession, code: str, exclude_id: Optional[int] = None) -> bool:
    """Case-insensitive, whitespace-insensitive uniqueness check."""
    stmt = select(func.count(Account.id)).where(
        func.lower(func.trim(Account.account_code)) == code.lower()
    )
    if exclude_id is not None:
        stmt = stmt.where(Account.id != exclude_id)
    return ((await db.execute(stmt)).scalar() or 0) > 0


async def _ensure_account_code_index(db: AsyncSession) -> None:
    """Idempotently create a case-insensitive unique index on account codes.

    This closes the race between the application-level duplicate check and the
    actual INSERT so two concurrent creators can never both succeed with
    codes that differ only by case/whitespace. Existing rows were verified to
    be unique under ``lower(trim(code))`` before this index is created.
    """
    global _CODE_INDEX_READY
    if _CODE_INDEX_READY:
        return
    try:
        await db.execute(text(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_accounts_code_ci "
            "ON accounts (lower(trim(account_code)))"
        ))
        await db.commit()
    except Exception:
        # Fresh multi-tenant DBs may not allow index creation mid-initialization;
        # the application-level check still protects writes.
        pass
    _CODE_INDEX_READY = True


async def _account_has_posted_lines(db: AsyncSession, account_id: int) -> bool:
    result = await db.execute(
        select(func.count(JournalEntryLine.id))
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntryLine.account_id == account_id, JournalEntry.status.in_(_LEDGER_STATUSES))
    )
    return (result.scalar() or 0) > 0


async def _account_has_lines(db: AsyncSession, account_id: int) -> bool:
    result = await db.execute(
        select(func.count(JournalEntryLine.id)).where(JournalEntryLine.account_id == account_id)
    )
    return (result.scalar() or 0) > 0


async def _account_active_child_count(db: AsyncSession, account_id: int) -> int:
    result = await db.execute(
        select(func.count(Account.id)).where(Account.parent_id == account_id, Account.is_active == True)
    )
    return result.scalar() or 0


async def _is_balance_account_type(account_type: str) -> bool:
    """Asset and expense accounts naturally carry debit balances."""
    return (account_type or "").lower() in ("asset", "expense")


def _build_tree(flat_accounts: list, balances: dict) -> list:
    account_map = {}
    for a in flat_accounts:
        node = AccountTreeNode(
            id=a.id,
            code=a.account_code,
            name=a.account_name,
            name_en=a.account_name_en,
            name_ar=a.account_name_ar,
            type=a.account_type,
            parent_id=a.parent_id,
            is_active=bool(a.is_active),
            is_control=bool(a.is_control),
            balance=balances.get(a.id, 0),
        )
        account_map[a.id] = node

    roots = []
    for a in flat_accounts:
        node = account_map[a.id]
        if a.parent_id and a.parent_id in account_map:
            account_map[a.parent_id].children.append(node)
        else:
            roots.append(node)

    type_order = {"asset": 0, "liability": 1, "equity": 2, "revenue": 3, "expense": 4}
    roots.sort(key=lambda x: (type_order.get(x.type, 99), x.code))
    for node in account_map.values():
        node.children.sort(key=lambda x: x.code)

    # post-order traversal computes self + all descendants
    def _accumulate(node) -> float:
        total = node.balance
        for child in node.children:
            total += _accumulate(child)
        node.cumulative_balance = total
        return total

    for root in roots:
        _accumulate(root)

    return roots


# ── Accounts CRUD ────────────────────────────────────────────

@router.get("/accounts", response_model=PaginationResponse)
async def list_accounts(
    page: int = Query(1, ge=1),
    per_page: int = Query(200, ge=1, le=500),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Account).where(Account.is_active == True)
    count_query = select(func.count(Account.id)).where(Account.is_active == True)
    # Company isolation: only show accounts belonging to the user's company
    # (or shared/general accounts with no company).
    if current_user.company_id:
        company_filter = (Account.company_id == current_user.company_id) | (Account.company_id.is_(None))
        query = query.where(company_filter)
        count_query = count_query.where(company_filter)
    if search:
        q = Account.account_code.ilike(f"%{search}%") | Account.account_name.ilike(f"%{search}%")
        query = query.where(q)
        count_query = count_query.where(q)
    if account_type:
        query = query.where(Account.account_type == account_type.lower())
        count_query = count_query.where(Account.account_type == account_type.lower())

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Account.account_code).offset(offset).limit(per_page)
    result = await db.execute(query)
    accounts = result.scalars().all()

    items = []
    for a in accounts:
        items.append({
            "id": a.id, "code": a.account_code, "name": a.account_name,
            "nameEn": a.account_name_en, "nameAr": a.account_name_ar,
            "type": a.account_type, "parentId": a.parent_id,
            "isActive": bool(a.is_active), "isControl": bool(a.is_control),
            "openingBalance": float(a.opening_balance or 0),
            "notes": a.notes,
        })

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=items,
    )


@router.get("/accounts/tree")
async def get_accounts_tree(
    account_type: Optional[str] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Account)
    if not include_inactive:
        query = query.where(Account.is_active == True)
    if account_type:
        query = query.where(Account.account_type == account_type.lower())
    query = query.order_by(Account.account_code)
    result = await db.execute(query)
    all_accounts = result.scalars().all()

    account_ids = [a.id for a in all_accounts]
    if account_ids:
        lines_result = await db.execute(
            select(
                JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id.in_(account_ids), JournalEntry.status.in_(_LEDGER_STATUSES))
            .group_by(JournalEntryLine.account_id)
        )
        journal_balances = {
            row[0]: {"debit": float(row[1]), "credit": float(row[2])}
            for row in lines_result.all()
        }
    else:
        journal_balances = {}

    balances = {}
    for a in all_accounts:
        opening = float(a.opening_balance or 0)
        jb = journal_balances.get(a.id, {"debit": 0, "credit": 0})
        account_type = (a.account_type or "").lower()
        if account_type in ("asset", "expense"):
            balances[a.id] = opening + jb["debit"] - jb["credit"]
        else:
            balances[a.id] = opening + jb["credit"] - jb["debit"]

    return _build_tree(all_accounts, balances)


@router.get("/accounts/flat")
async def get_accounts_flat(
    account_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Account).where(Account.is_active == True).order_by(Account.account_code)
    if account_type:
        query = query.where(Account.account_type == account_type.lower())
    result = await db.execute(query)
    accounts = result.scalars().all()

    account_ids = [a.id for a in accounts]
    journal_balances = {}
    if account_ids:
        lines_result = await db.execute(
            select(
                JournalEntryLine.account_id,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            ).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntryLine.account_id.in_(account_ids), JournalEntry.status.in_(_LEDGER_STATUSES))
            .group_by(JournalEntryLine.account_id)
        )
        journal_balances = {
            row[0]: {"debit": float(row[1]), "credit": float(row[2])}
            for row in lines_result.all()
        }

    result_list = []
    for a in accounts:
        opening = float(a.opening_balance or 0)
        jb = journal_balances.get(a.id, {"debit": 0, "credit": 0})
        account_type = (a.account_type or "").lower()
        if account_type in ("asset", "expense"):
            balance = opening + jb["debit"] - jb["credit"]
        else:
            balance = opening + jb["credit"] - jb["debit"]
        result_list.append({
            "id": a.id, "code": a.account_code, "name": a.account_name,
            "nameEn": a.account_name_en, "nameAr": a.account_name_ar,
            "type": a.account_type, "parentId": a.parent_id,
            "balance": balance,
            "isActive": bool(a.is_active),
            "isControl": bool(a.is_control),
        })
    return result_list


@router.get("/accounts/{account_id}")
async def get_account(account_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    balance = await _compute_balance(db, account.id)

    children_result = await db.execute(
        select(Account).where(Account.parent_id == account.id, Account.is_active == True).order_by(Account.account_code)
    )
    children = children_result.scalars().all()

    cumulative_balance = await _compute_cumulative_balance(db, account.id)

    return {
        "id": account.id, "code": account.account_code, "name": account.account_name,
        "nameEn": account.account_name_en, "nameAr": account.account_name_ar,
        "type": account.account_type, "parentId": account.parent_id,
        "isActive": bool(account.is_active), "isControl": bool(account.is_control),
        "openingBalance": float(account.opening_balance or 0),
        "balance": balance, "cumulativeBalance": cumulative_balance, "notes": account.notes,
        "createdAt": account.created_at.isoformat() if account.created_at else None,
        "children": [{"id": c.id, "code": c.account_code, "name": c.account_name} for c in children],
    }


@router.post("/accounts", response_model=dict)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    await _ensure_account_code_index(db)
    account_code = _normalize_account_code(data.account_code)
    account_name = _normalize_account_name(data.account_name)
    account_type = data.account_type.lower()

    if await _account_code_exists(db, account_code):
        raise HTTPException(status_code=400, detail=f"Account code '{account_code}' already exists")

    if data.parent_id:
        parent_result = await db.execute(select(Account).where(Account.id == data.parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent account not found")
        if not parent.is_active:
            raise HTTPException(status_code=400, detail="Parent account is inactive")
        if parent.account_type != account_type:
            raise HTTPException(
                status_code=400,
                detail=f"Account type '{account_type}' must match parent account type '{parent.account_type}'",
            )

    if data.is_control and data.opening_balance:
        raise HTTPException(status_code=400, detail="Control (group) accounts cannot carry an opening balance")

    account = Account(
        account_code=account_code, account_name=account_name,
        account_name_en=(data.account_name_en or "").strip() or None,
        account_name_ar=(data.account_name_ar or "").strip() or None,
        account_type=account_type, parent_id=data.parent_id,
        is_control=data.is_control, currency_id=data.currency_id,
        opening_balance=data.opening_balance or 0,
        opening_balance_date=data.opening_balance_date, notes=(data.notes or "").strip() or None,
        is_active=True, created_at=datetime.now(UTC).replace(tzinfo=None), updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(account)
    await db.flush()
    # A parent that receives children is a group/control account by definition:
    # ensure it is flagged so posting validations reject it.
    if data.parent_id:
        await db.execute(update(Account).where(Account.id == data.parent_id).values(
            is_control=True, updated_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    await add_audit_log(db, "Account", account.id, "CREATE", current_user,
                        {"code": account_code, "name": account_name, "type": account_type},
                        company_id=account.company_id)
    return {"id": account.id, "message": "Account created"}


@router.put("/accounts/{account_id}", response_model=dict)
async def update_account(account_id: int, data: AccountCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    await _ensure_account_code_index(db)
    account_code = _normalize_account_code(data.account_code)
    account_name = _normalize_account_name(data.account_name)
    account_type = data.account_type.lower()

    if data.account_code != account.account_code:
        if await _account_code_exists(db, account_code, exclude_id=account_id):
            raise HTTPException(status_code=400, detail=f"Account code '{account_code}' already exists")

    # ── Structural protections (must hold BEFORE any write) ──────────────
    # 1) Changing the type of an account that already has journal lines would
    #    silently flip the sign convention of its historical balances.
    if account_type != (account.account_type or "").lower():
        if await _account_has_lines(db, account.id):
            raise HTTPException(
                status_code=400,
                detail="Cannot change account type: the account already has journal entries. Create a new account instead.",
            )
        if await _account_active_child_count(db, account.id) > 0:
            raise HTTPException(
                status_code=400,
                detail="Cannot change the type of a group account that has children. Move or deactivate its children first.",
            )

    # 2) Changing the opening balance of an account with posted lines would
    #    silently rewrite history in every financial report.
    new_opening = data.opening_balance or 0
    if abs(new_opening - float(account.opening_balance or 0)) > 1e-9:
        if await _account_has_posted_lines(db, account.id):
            raise HTTPException(
                status_code=400,
                detail="Cannot change the opening balance: the account already has posted journal entries.",
            )

    # 3) Opening balances belong on leaf accounts only.
    if new_opening and (data.is_control or await _account_active_child_count(db, account.id) > 0):
        raise HTTPException(status_code=400, detail="Control (group) accounts cannot carry an opening balance")

    old_parent_id = account.parent_id

    if data.parent_id:
        if data.parent_id == account_id:
            raise HTTPException(status_code=400, detail="Account cannot be its own parent")
        descendants = await _get_descendant_ids(db, account_id)
        if data.parent_id in descendants:
            raise HTTPException(status_code=400, detail="Cannot move account under its own descendant (cycle detected)")
        parent_result = await db.execute(select(Account).where(Account.id == data.parent_id))
        parent = parent_result.scalar_one_or_none()
        if not parent:
            raise HTTPException(status_code=400, detail="Parent account not found")
        if not parent.is_active:
            raise HTTPException(status_code=400, detail="Parent account is inactive")
        if parent.account_type != account_type:
            raise HTTPException(
                status_code=400,
                detail=f"Account type '{account_type}' must match parent account type '{parent.account_type}'",
            )

    await db.execute(update(Account).where(Account.id == account_id).values(
        account_code=account_code, account_name=account_name,
        account_name_en=(data.account_name_en or "").strip() or None,
        account_name_ar=(data.account_name_ar or "").strip() or None,
        account_type=account_type, parent_id=data.parent_id,
        is_control=data.is_control, currency_id=data.currency_id,
        opening_balance=new_opening,
        opening_balance_date=data.opening_balance_date, notes=(data.notes or "").strip() or None,
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))

    # ── Tree reconciliation after a move ─────────────────────────────────
    # An account that gained/lost children must be flagged/def-flagged as a
    # control account. When the account moved under a NEW parent, that parent
    # must be flagged control too, and the OLD parent (if it lost its last
    # child) must become a plain leaf again.
    child_count = await _account_active_child_count(db, account_id)
    await db.execute(update(Account).where(Account.id == account_id).values(
        is_control=bool(child_count > 0 or data.is_control), updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    if data.parent_id and data.parent_id != old_parent_id:
        await db.execute(update(Account).where(Account.id == data.parent_id).values(
            is_control=True, updated_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    if old_parent_id and old_parent_id != data.parent_id:
        old_parent_children = await _account_active_child_count(db, old_parent_id)
        if old_parent_children == 0:
            await db.execute(update(Account).where(Account.id == old_parent_id).values(
                is_control=False, updated_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    await add_audit_log(db, "Account", account.id, "UPDATE", current_user,
                        {"code": account_code, "name": account_name})
    return {"message": "Account updated"}


@router.delete("/accounts/{account_id}", response_model=MessageResponse)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    children = await db.execute(select(func.count(Account.id)).where(Account.parent_id == account_id))
    if children.scalar() > 0:
        raise HTTPException(status_code=400, detail="Cannot delete account with children. Move or delete children first.")

    lines = await db.execute(select(func.count(JournalEntryLine.id)).where(JournalEntryLine.account_id == account_id))
    if lines.scalar() > 0:
        raise HTTPException(status_code=400, detail="Cannot delete account with journal entries. Deactivate instead.")

    if float(account.opening_balance or 0) != 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete an account that carries an opening balance. Set the opening balance to zero first."
            + " Deactivating it would drop its opening balance from the financial statements.",
        )

    await db.execute(update(Account).where(Account.id == account_id).values(is_active=False, updated_at=datetime.now(UTC).replace(tzinfo=None)))
    # If the parent just lost its last active child, it becomes a leaf again.
    if account.parent_id:
        parent_children = (await db.execute(
            select(func.count(Account.id)).where(
                Account.parent_id == account.parent_id,
                Account.is_active == True,
            )
        )).scalar() or 0
        if parent_children == 0:
            await db.execute(update(Account).where(Account.id == account.parent_id).values(
                is_control=False, updated_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    await add_audit_log(db, "Account", account.id, "DELETE", current_user,
                        {"code": account.account_code, "deactivated": True})
    return MessageResponse(message="Account deactivated")


# ── Journal Entries ───────────────────────────────────────────

@router.get("/journal-entries", response_model=PaginationResponse)
async def list_journal_entries(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JournalEntry)
    count_query = select(func.count(JournalEntry.id))
    if current_user.company_id:
        company_filter = (JournalEntry.company_id == current_user.company_id) | (JournalEntry.company_id.is_(None))
        query = query.where(company_filter)
        count_query = count_query.where(company_filter)
    if status:
        canonical = _JE_STATUS_ALIASES.get(status.strip().lower())
        if canonical:
            status = canonical
        query = query.where(JournalEntry.status == status)
        count_query = count_query.where(JournalEntry.status == status)
    if search and search.strip():
        q = search.strip()
        line_match = (
            select(JournalEntryLine.journal_entry_id)
            .join(Account, Account.id == JournalEntryLine.account_id)
            .where(or_(
                Account.account_code.ilike(f"%{q}%"),
                Account.account_name.ilike(f"%{q}%"),
            ))
        )
        search_filter = (
            JournalEntry.entry_number.ilike(f"%{q}%")
            | JournalEntry.description.ilike(f"%{q}%")
            | JournalEntry.id.in_(line_match)
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(JournalEntry.id.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    entries = result.scalars().all()

    items = []
    for entry in entries:
        lines_result = await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry.id))
        lines = lines_result.scalars().all()
        items.append({
            "id": entry.id, "entry_number": entry.entry_number, "entry_date": entry.entry_date,
            "fiscal_period_id": entry.fiscal_period_id, "reference_type": entry.reference_type,
            "reference_id": entry.reference_id, "description": entry.description,
            "status": entry.status, "created_by": entry.created_by,
            "posted_by": entry.posted_by, "posted_at": entry.posted_at,
            "voided_by": entry.voided_by, "voided_at": entry.voided_at, "void_reason": entry.void_reason,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "lines": await _enrich_journal_lines(db, lines),
        })

    return PaginationResponse(total=total, page=page, per_page=per_page,
                              pages=math.ceil(total / per_page) if total else 0, items=items)


@router.get("/journal-entries/{entry_id}")
async def get_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    lines_result = await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry.id))
    lines = lines_result.scalars().all()
    return {
        "id": entry.id, "entry_number": entry.entry_number, "entry_date": entry.entry_date,
        "fiscal_period_id": entry.fiscal_period_id, "reference_type": entry.reference_type,
        "reference_id": entry.reference_id, "description": entry.description,
        "status": entry.status, "created_by": entry.created_by,
        "posted_by": entry.posted_by, "posted_at": entry.posted_at,
        "voided_by": entry.voided_by, "voided_at": entry.voided_at, "void_reason": entry.void_reason,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "lines": await _enrich_journal_lines(db, lines),
    }


_SAFE_ENTRY_NUMBER_SQL = text(
    "SELECT setval('journal_entry_number_seq', GREATEST("
    "nextval('journal_entry_number_seq'), "
    "(SELECT COALESCE(MAX(NULLIF(regexp_replace(entry_number, '^.*-', '', 'g'), '')::bigint), 0) + 1 "
    "FROM journal_entries)), "
    "true) AS n"
)


async def _generate_entry_number(db: AsyncSession) -> str:
    """Generate a unique journal entry number (JE-YYYY-NNNNNN).

    Uses a self-healing sequence: the draw is forced to leapfrog the highest
    entry number already present in the table. This guarantees uniqueness even
    if the underlying sequence drifts below existing rows or is ever reset.
    """
    year = datetime.now().year
    try:
        seq_result = await db.execute(_SAFE_ENTRY_NUMBER_SQL)
    except Exception:
        # Sequence missing (fresh database): create it, then retry.
        await db.execute(text("CREATE SEQUENCE IF NOT EXISTS journal_entry_number_seq START 1"))
        seq_result = await db.execute(_SAFE_ENTRY_NUMBER_SQL)
    seq = int(seq_result.scalar() or 1)
    return f"JE-{year}-{seq:06d}"


@router.post("/journal-entries", response_model=dict)
async def create_journal_entry(data: JournalEntryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("CREATE_JOURNAL"))):
    try:
        entry_date = datetime.fromisoformat(data.entry_date.replace("Z", "+00:00"))
    except ValueError:
        entry_date = datetime.strptime(data.entry_date, "%Y-%m-%d")

    description = (data.description or "").strip()
    if not description:
        raise HTTPException(status_code=400, detail="Journal entry description is required")

    # Double-entry integrity is enforced even for drafts: an unbalanced draft
    # can never be posted and silently desynchronizes the books.
    _validate_journal_lines(data.lines)
    await _validate_journal_accounts(db, [line.account_id for line in data.lines])

    # Resolve the covering fiscal period when one was not provided, so every
    # entry is linked to a period (needed for period reporting).
    period_id = data.fiscal_period_id or await _resolve_fiscal_period_id(db, entry_date)
    await _check_period_lock(db, period_id, entry_date)
    entry_number = await _generate_entry_number(db)

    entry = JournalEntry(
        entry_number=entry_number, entry_date=entry_date,
        fiscal_period_id=period_id, reference_type=data.reference_type,
        reference_id=data.reference_id, description=description,
        status=JE_STATUS_DRAFT, created_by=current_user.id, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(entry)
    await db.flush()

    for line_data in data.lines:
        db.add(JournalEntryLine(
            journal_entry_id=entry.id, account_id=line_data.account_id,
            description=line_data.description, debit=line_data.debit,
            credit=line_data.credit, currency_id=line_data.currency_id,
            currency_rate=line_data.currency_rate, cost_center_id=line_data.cost_center_id,
            partner_id=line_data.partner_id, project_id=line_data.project_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    await db.flush()
    await add_audit_log(db, "JournalEntry", entry.id, "CREATE", current_user,
                        {"entry_number": entry_number, "description": description})
    return {"id": entry.id, "entry_number": entry_number, "fiscal_period_id": period_id,
            "message": "Journal entry created"}


@router.post("/journal-entries/{entry_id}/post", response_model=MessageResponse)
async def post_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("POST_JOURNAL"))):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != JE_STATUS_DRAFT:
        raise HTTPException(status_code=400, detail="Only draft entries can be posted")

    period_id = entry.fiscal_period_id or await _resolve_fiscal_period_id(db, entry.entry_date)
    await _check_period_lock(db, period_id, entry.entry_date)

    lines_result = await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry_id))
    lines = lines_result.scalars().all()
    await _validate_journal_accounts(db, [l.account_id for l in lines])
    total_debit = sum(float(l.debit or 0) for l in lines)
    total_credit = sum(float(l.credit or 0) for l in lines)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Debits ({total_debit}) != Credits ({total_credit})")

    # Lines must respect the posting rules before finalizing.
    for line in lines:
        if (float(line.debit or 0) <= 0) == (float(line.credit or 0) <= 0):
            raise HTTPException(status_code=400, detail="Each journal line must have either a debit or a credit amount")

    await db.execute(update(JournalEntry).where(JournalEntry.id == entry_id).values(
        status=JE_STATUS_POSTED, posted_by=current_user.id,
        posted_at=datetime.now(UTC).replace(tzinfo=None),
        **({"fiscal_period_id": period_id} if period_id else {}),
    ))
    await add_audit_log(db, "JournalEntry", entry.id, "POST", current_user,
                        {"entry_number": entry.entry_number})
    return MessageResponse(message="Journal entry posted")


@router.post("/journal-entries/{entry_id}/void", response_model=dict)
async def void_journal_entry(entry_id: int, reason: str = "", db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_JOURNAL"))):
    """Void a posted journal entry by creating an automatic reversing entry.

    Accounting logic: posted entries are IMMUTABLE. To correct/void one, we
    mark the original as 'Voided' and create a new posted reversing entry with
    swapped debits/credits. This preserves the double-entry audit trail.
    """
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != JE_STATUS_POSTED:
        raise HTTPException(status_code=400, detail="Only posted entries can be voided")
    if entry.reference_type == "JournalEntryReversal":
        raise HTTPException(status_code=400, detail="Cannot void a reversing entry")
    if not reason or not reason.strip():
        raise HTTPException(status_code=400, detail="A void reason is required")

    # The reversing entry is dated like the original so the void is netted
    # inside the same fiscal period instead of polluting a later one.
    period_id = entry.fiscal_period_id or await _resolve_fiscal_period_id(db, entry.entry_date)
    await _check_period_lock(db, period_id, entry.entry_date)

    lines_result = await db.execute(
        select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry_id)
    )
    lines = lines_result.scalars().all()
    if not lines:
        raise HTTPException(status_code=400, detail="Journal entry has no lines")

    # Mark original entry as Voided
    await db.execute(update(JournalEntry).where(JournalEntry.id == entry_id).values(
        status=JE_STATUS_VOIDED, voided_by=current_user.id,
        voided_at=datetime.now(UTC).replace(tzinfo=None), void_reason=reason,
    ))

    # Generate a unique entry number for the reversal using the sequence
    reversal_number = await _generate_entry_number(db)

    # Create reversing entry (swap debits/credits)
    reversal = JournalEntry(
        entry_number=reversal_number,
        entry_date=entry.entry_date,
        fiscal_period_id=entry.fiscal_period_id,
        reference_type="JournalEntryReversal",
        reference_id=entry_id,
        description=f"عكس القيد {entry.entry_number}: {reason}",
        status=JE_STATUS_POSTED, created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        posted_by=current_user.id, posted_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(reversal)
    await db.flush()

    for line in lines:
        db.add(JournalEntryLine(
            journal_entry_id=reversal.id,
            account_id=line.account_id,
            description=f"عكس: {(line.description or entry.description or '')}",
            debit=float(line.credit or 0),
            credit=float(line.debit or 0),
            currency_id=line.currency_id,
            currency_rate=line.currency_rate,
            cost_center_id=line.cost_center_id,
            partner_id=line.partner_id,
            project_id=line.project_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))

    await db.flush()
    await add_audit_log(db, "JournalEntry", entry.id, "VOID", current_user,
                        {"entry_number": entry.entry_number, "reason": reason,
                         "reversal_entry_number": reversal_number})
    return {"message": "Journal entry voided with reversing entry",
            "reversal_id": reversal.id, "reversal_entry_number": reversal_number}


# ── Trial Balance ─────────────────────────────────────────────

@router.get("/trial-balance")
async def trial_balance(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    fiscal_period_id: Optional[int] = None,
    date: Optional[str] = None,
    account_type: Optional[str] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts_query = select(Account).where(Account.is_active == True).order_by(Account.account_code)
    count_query = select(func.count(Account.id)).where(Account.is_active == True)
    # Company isolation: only accounts of the user's company (or shared general accounts).
    if current_user.company_id:
        company_filter = (Account.company_id == current_user.company_id) | (Account.company_id.is_(None))
        accounts_query = accounts_query.where(company_filter)
        count_query = count_query.where(company_filter)
    if account_type:
        accounts_query = accounts_query.where(Account.account_type == account_type.lower())
        count_query = count_query.where(Account.account_type == account_type.lower())
    if search:
        q = Account.account_code.ilike(f"%{search}%") | Account.account_name.ilike(f"%{search}%")
        accounts_query = accounts_query.where(q)
        count_query = count_query.where(q)
    total_accounts = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    accounts_result = await db.execute(accounts_query.offset(offset).limit(per_page))
    accounts = accounts_result.scalars().all()
    account_ids = [a.id for a in accounts]

    # Parse as-of date (inclusive): only include posted entries on/before the date.
    as_of: Optional[datetime] = None
    if date:
        try:
            as_of = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            as_of = datetime.strptime(date, "%Y-%m-%d")

    # Aggregate posted lines for the page's accounts (driver for totals AND display).
    balance_query = (
        select(
            JournalEntryLine.account_id,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
    )
    if fiscal_period_id:
        balance_query = balance_query.where(JournalEntry.fiscal_period_id == fiscal_period_id)
    if as_of is not None:
        balance_query = balance_query.where(JournalEntry.entry_date <= as_of)
    if account_ids:
        balance_query = balance_query.where(JournalEntryLine.account_id.in_(account_ids))
    balance_query = balance_query.group_by(JournalEntryLine.account_id)
    balances_result = await db.execute(balance_query)

    balances = {}
    for row in balances_result.all():
        balances[row.account_id] = {"debit": float(row.total_debit), "credit": float(row.total_credit)}

    # Global totals over ALL posted entries (independent of pagination) so that
    # is_balanced reflects the whole ledger, not just the current page.
    totals_query = (
        select(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntry.status.in_(_LEDGER_STATUSES))
    )
    if fiscal_period_id:
        totals_query = totals_query.where(JournalEntry.fiscal_period_id == fiscal_period_id)
    if as_of is not None:
        totals_query = totals_query.where(JournalEntry.entry_date <= as_of)
    grand_total_row = (await db.execute(totals_query)).one()
    total_debit = float(grand_total_row.total_debit)
    total_credit = float(grand_total_row.total_credit)

    trial = []
    for account in accounts:
        b = balances.get(account.id, {"debit": 0, "credit": 0})
        opening = float(account.opening_balance or 0)
        account_type = (account.account_type or "").lower()
        # Net balance depends on account type:
        #   Asset/Expense:  Opening + Dr - Cr
        #   Liability/Equity/Revenue: Opening + Cr - Dr
        if account_type in ("asset", "expense"):
            net = opening + b["debit"] - b["credit"]
        else:
            net = opening + b["credit"] - b["debit"]
        trial.append({
            "account_id": account.id, "account_code": account.account_code,
            "account_name": account.account_name, "account_type": account.account_type,
            "debit": b["debit"], "credit": b["credit"],
            "opening_balance": opening, "net_balance": net,
        })

    return {
        "total_debit": total_debit, "total_credit": total_credit,
        "is_balanced": abs(total_debit - total_credit) < 0.01,
        "page": page, "per_page": per_page, "total": total_accounts,
        "pages": math.ceil(total_accounts / per_page) if total_accounts else 0,
        "accounts": trial,
    }


# ── Fiscal Periods ────────────────────────────────────────────

@router.get("/fiscal-periods")
async def list_fiscal_periods(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(FiscalPeriod).order_by(FiscalPeriod.start_date.desc()))
    return [{"id": fp.id, "name": fp.name, "name_en": fp.name_en,
             "start_date": fp.start_date, "end_date": fp.end_date,
             "is_closed": fp.is_closed, "is_locked": fp.is_locked}
            for fp in result.scalars().all()]


@router.post("/fiscal-periods", response_model=dict)
async def create_fiscal_period(data: FiscalPeriodCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    try:
        start_date = datetime.fromisoformat(data.start_date.replace("Z", "+00:00"))
    except ValueError:
        start_date = datetime.strptime(data.start_date, "%Y-%m-%d")
    try:
        end_date = datetime.fromisoformat(data.end_date.replace("Z", "+00:00"))
    except ValueError:
        end_date = datetime.strptime(data.end_date, "%Y-%m-%d")
    if start_date >= end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")
    fp = FiscalPeriod(
        name=data.name, name_en=data.name_en,
        start_date=start_date, end_date=end_date,
        is_closed=False, is_locked=False,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(fp)
    await db.flush()
    await add_audit_log(db, "FiscalPeriod", fp.id, "CREATE", current_user,
                        {"name": data.name, "start": data.start_date, "end": data.end_date})
    return {"id": fp.id, "message": "Fiscal period created"}


# ── Cost Centers ──────────────────────────────────────────────

@router.get("/cost-centers")
async def list_cost_centers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CostCenter).where(CostCenter.is_active == True).order_by(CostCenter.name))
    return [{"id": cc.id, "code": cc.code, "name": cc.name, "name_en": cc.name_en, "parent_id": cc.parent_id}
            for cc in result.scalars().all()]


@router.post("/cost-centers", response_model=dict)
async def create_cost_center(data: CostCenterCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    existing = await db.execute(select(CostCenter).where(CostCenter.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Cost center code already exists")
    cc = CostCenter(code=data.code, name=data.name,
                    name_en=data.name_en, parent_id=data.parent_id,
                    is_active=True,
                    created_at=datetime.now(UTC).replace(tzinfo=None))
    db.add(cc)
    await db.flush()
    await add_audit_log(db, "CostCenter", cc.id, "CREATE", current_user,
                        {"code": data.code, "name": data.name})
    return {"id": cc.id, "message": "Cost center created"}


@router.get("/general-ledger")
async def general_ledger(
    account_id: int = Query(...),
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    partner_id: Optional[int] = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    acc_result = await db.execute(select(Account).where(Account.id == account_id))
    account = acc_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    if from_date:
        try:
            fd = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError:
            fd = datetime.strptime(from_date, "%Y-%m-%d")
    else:
        fd = datetime(datetime.now().year, 1, 1)
    if to_date:
        try:
            td = datetime.fromisoformat(to_date.replace("Z", "+00:00"))
        except ValueError:
            td = datetime.strptime(to_date, "%Y-%m-%d")
    else:
        td = datetime.now()

    is_balance_type = await _is_balance_account_type(account.account_type)
    # Net flow sign convention: asset/expense accounts accumulate debit − credit;
    # liability/equity/revenue accounts accumulate credit − debit.
    if is_balance_type:
        opening_sql = func.coalesce(func.sum(JournalEntryLine.debit), 0) - func.coalesce(func.sum(JournalEntryLine.credit), 0)
    else:
        opening_sql = func.coalesce(func.sum(JournalEntryLine.credit), 0) - func.coalesce(func.sum(JournalEntryLine.debit), 0)
    opening_query = select(opening_sql).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(
        JournalEntryLine.account_id == account_id,
        JournalEntry.status.in_(_LEDGER_STATUSES),
        JournalEntry.entry_date < fd,
    )
    opening_result = await db.execute(opening_query)
    opening_balance = float(opening_result.scalar() or 0) + float(account.opening_balance or 0)

    lines_filters = [
        JournalEntryLine.account_id == account_id,
        JournalEntry.status.in_(_LEDGER_STATUSES),
        JournalEntry.entry_date >= fd,
        JournalEntry.entry_date <= td,
    ]
    if partner_id is not None:
        lines_filters.append(JournalEntryLine.partner_id == partner_id)
    lines_query = (
        select(JournalEntryLine, JournalEntry)
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(*lines_filters)
        .order_by(JournalEntry.entry_date, JournalEntry.id)
    )
    total_count_result = await db.execute(select(func.count()).select_from(lines_query.subquery()))
    total = total_count_result.scalar() or 0
    offset = (page - 1) * per_page
    lines_result = await db.execute(lines_query.offset(offset).limit(per_page))
    rows = lines_result.all()

    transactions = []
    running = opening_balance
    for line, entry in rows:
        debit = float(line.debit or 0)
        credit = float(line.credit or 0)
        running += (debit - credit) if is_balance_type else (credit - debit)
        transactions.append({
            "id": line.id,
            "entry_number": entry.entry_number,
            "entry_date": entry.entry_date.isoformat() if hasattr(entry.entry_date, 'isoformat') else str(entry.entry_date),
            "description": line.description or entry.description or "",
            "reference": entry.reference_type or "",
            "partner_id": line.partner_id,
            "project_id": line.project_id,
            "debit": debit,
            "credit": credit,
            "running_balance": running,
            "status": entry.status,
        })

    return {
        "account": {
            "id": account.id,
            "code": account.account_code,
            "name": account.account_name,
            "name_en": account.account_name_en,
            "type": account.account_type,
            "opening_balance": float(account.opening_balance or 0),
        },
        "from_date": fd.isoformat() if hasattr(fd, 'isoformat') else str(fd),
        "to_date": td.isoformat() if hasattr(td, 'isoformat') else str(td),
        "opening_balance_for_period": opening_balance,
        "closing_balance": running,
        "total_debit": sum(t["debit"] for t in transactions),
        "total_credit": sum(t["credit"] for t in transactions),
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": math.ceil(total / per_page) if total else 0,
        "transactions": transactions,
    }


@router.put("/journal-entries/{entry_id}", response_model=dict)
async def update_journal_entry(
    entry_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("EDIT_JOURNAL")),
):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != JE_STATUS_DRAFT:
        raise HTTPException(status_code=400, detail="Only draft entries can be edited")

    # Apply date changes FIRST so the period guard validates the NEW date.
    new_entry_date = entry.entry_date
    if "entry_date" in data:
        try:
            new_entry_date = datetime.fromisoformat(data["entry_date"].replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            new_entry_date = datetime.strptime(data["entry_date"], "%Y-%m-%d")
    await _check_period_lock(db, data.get("fiscal_period_id"), new_entry_date)

    update_values = {}
    update_values["entry_date"] = new_entry_date
    if "description" in data:
        description = (data["description"] or "").strip()
        if not description:
            raise HTTPException(status_code=400, detail="Journal entry description is required")
        update_values["description"] = description
    if "fiscal_period_id" in data:
        update_values["fiscal_period_id"] = data["fiscal_period_id"]
    elif entry.fiscal_period_id is None:
        # Keep drafts linked to a covering period even when the date changes.
        resolved = await _resolve_fiscal_period_id(db, new_entry_date)
        if resolved:
            update_values["fiscal_period_id"] = resolved

    if update_values:
        await db.execute(update(JournalEntry).where(JournalEntry.id == entry_id).values(**update_values))

    if "lines" in data:
        new_lines = data["lines"]
        if not new_lines or len(new_lines) < 2:
            raise HTTPException(status_code=400, detail="Journal entry must have at least 2 lines")

        # Double-entry integrity is validated centrally (returns totals or 400).
        _validate_journal_lines(new_lines)
        await _validate_journal_accounts(db, [l.get("account_id") for l in new_lines])

        await db.execute(text("DELETE FROM journal_entry_lines WHERE journal_entry_id = :eid"), {"eid": entry_id})
        for line_data in new_lines:
            db.add(JournalEntryLine(
                journal_entry_id=entry_id,
                account_id=line_data["account_id"],
                description=line_data.get("description"),
                debit=line_data.get("debit", 0),
                credit=line_data.get("credit", 0),
                currency_id=line_data.get("currency_id"),
                currency_rate=line_data.get("currency_rate"),
                cost_center_id=line_data.get("cost_center_id"),
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    await db.flush()
    return {"message": "Journal entry updated"}


@router.delete("/journal-entries/{entry_id}", response_model=MessageResponse)
async def delete_journal_entry(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("DELETE_JOURNAL")),
):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != JE_STATUS_DRAFT:
        raise HTTPException(status_code=400, detail="Only draft entries can be deleted")
    await add_audit_log(db, "JournalEntry", entry.id, "DELETE", current_user,
                        {"entry_number": entry.entry_number})
    await db.execute(text("DELETE FROM journal_entry_lines WHERE journal_entry_id = :eid"), {"eid": entry_id})
    await db.execute(text("DELETE FROM journal_entries WHERE id = :eid"), {"eid": entry_id})
    return MessageResponse(message="Journal entry deleted")


# ── Cost Center Report ───────────────────────────────────────

async def _parse_date_or_none(value: Optional[str], field: str = "date") -> Optional[datetime]:
    """Parse a user-supplied date/datetime, tolerating several input formats.

    Bad input raises 422 (naming the field) instead of letting ValueError
    escape and turn the endpoint into a 500.
    """
    if not value:
        return None
    raw = value.strip()
    normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise HTTPException(status_code=422, detail=f"Invalid {field}: {value!r}")


@router.get("/cost-centers/report")
async def cost_center_report(
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    fiscal_period_id: Optional[int] = None,
    include_unallocated: bool = Query(True),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cost center activity report: posted lines grouped by cost center and
    account, with per-center totals and the unallocated remainder."""
    fd = await _parse_date_or_none(from_date, "from_date")
    td = await _parse_date_or_none(to_date, "to_date")
    if fiscal_period_id:
        period_result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == fiscal_period_id))
        period = period_result.scalar_one_or_none()
        if not period:
            raise HTTPException(status_code=404, detail="Fiscal period not found")
        fd = period.start_date
        td = period.end_date
    if not fd:
        fd = datetime(datetime.now().year, 1, 1)
    if not td:
        td = datetime.now()

    rows_result = await db.execute(
        select(
            JournalEntryLine.cost_center_id,
            JournalEntryLine.account_id,
            Account.account_code,
            Account.account_name,
            Account.account_type,
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .join(Account, JournalEntryLine.account_id == Account.id)
        .where(
            JournalEntry.status.in_(_LEDGER_STATUSES),
            JournalEntry.entry_date >= fd,
            JournalEntry.entry_date <= td,
        )
        .group_by(JournalEntryLine.cost_center_id, JournalEntryLine.account_id,
                  Account.account_code, Account.account_name, Account.account_type)
        .order_by(JournalEntryLine.cost_center_id, Account.account_code)
    )
    rows = rows_result.all()

    center_map: dict[int, dict] = {}
    unallocated: dict = {"total_debit": 0.0, "total_credit": 0.0, "net": 0.0, "accounts": []}
    grand = {"total_debit": 0.0, "total_credit": 0.0, "net": 0.0}

    def _bucket(target, account_id, code, name, acc_type, dr, cr):
        if acc_type in ("asset", "expense"):
            net = dr - cr
        else:
            net = cr - dr
        lines = target.setdefault("accounts", [])
        existing = next((l for l in lines if l["account_id"] == account_id), None)
        if existing:
            existing["debit"] += dr
            existing["credit"] += cr
            existing["net"] += net
        else:
            lines.append({"account_id": account_id, "account_code": code,
                           "account_name": name, "debit": dr, "credit": cr, "net": net})
        target["total_debit"] += dr
        target["total_credit"] += cr
        target["net"] += net

    for row in rows:
        dr = float(row.total_debit or 0)
        cr = float(row.total_credit or 0)
        grand["total_debit"] += dr
        grand["total_credit"] += cr
        grand["net"] += (dr - cr) if row.account_type in ("asset", "expense") else (cr - dr)
        if row.cost_center_id is None:
            _bucket(unallocated, row.account_id, row.account_code, row.account_name,
                    row.account_type, dr, cr)
            continue
        cc = center_map.get(row.cost_center_id)
        if cc is None:
            cc_result = await db.execute(select(CostCenter).where(CostCenter.id == row.cost_center_id))
            cc_obj = cc_result.scalar_one_or_none()
            center_map[row.cost_center_id] = cc = {
                "cost_center_id": row.cost_center_id,
                "code": cc_obj.code if cc_obj else str(row.cost_center_id),
                "name": cc_obj.name if cc_obj else f"مركز #{row.cost_center_id}",
                "total_debit": 0.0, "total_credit": 0.0, "net": 0.0, "accounts": [],
            }
        _bucket(cc, row.account_id, row.account_code, row.account_name, row.account_type, dr, cr)

    for cc in center_map.values():
        cc["total_debit"] = round(cc["total_debit"], 4)
        cc["total_credit"] = round(cc["total_credit"], 4)
        cc["net"] = round(cc["net"], 4)
        cc["accounts"] = [dict(a, debit=round(a["debit"], 4), credit=round(a["credit"], 4),
                               net=round(a["net"], 4)) for a in cc["accounts"]]
    result = {
        "period": {"from": fd.date().isoformat(), "to": td.date().isoformat()},
        "centers": list(center_map.values()),
        "grand_total": {k: round(v, 4) for k, v in grand.items()},
    }
    if include_unallocated:
        result["unallocated"] = {
            "total_debit": round(unallocated.get("total_debit", 0), 4),
            "total_credit": round(unallocated.get("total_credit", 0), 4),
            "net": round(unallocated.get("net", 0), 4),
            "accounts": [dict(a, debit=round(a["debit"], 4), credit=round(a["credit"], 4),
                              net=round(a["net"], 4)) for a in unallocated.get("accounts", [])],
        }
    return result


# ── Cost Center Allocation Rules ─────────────────────────────

def _serialize_rule(rule: CostCenterAllocationRule, lines: list) -> dict:
    return {
        "id": rule.id, "name": rule.name, "name_en": rule.name_en,
        "description": rule.description, "source_account_id": rule.source_account_id,
        "target_account_id": rule.target_account_id,
        "frequency": rule.frequency, "is_active": bool(rule.is_active),
        "allocation_date": rule.allocation_date.isoformat() if rule.allocation_date else None,
        "lines": [{"cost_center_id": l.cost_center_id, "percentage": float(l.percentage)}
                  for l in lines],
    }


@router.get("/cost-centers/allocation-rules")
async def list_allocation_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(CostCenterAllocationRule).order_by(CostCenterAllocationRule.id.desc())
    )
    rules = []
    for rule in result.scalars().all():
        lines_result = await db.execute(
            select(CostCenterAllocationRuleLine).where(CostCenterAllocationRuleLine.rule_id == rule.id)
        )
        rules.append(_serialize_rule(rule, lines_result.scalars().all()))
    return rules


@router.get("/cost-centers/allocation-rules/{rule_id}")
async def get_allocation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(CostCenterAllocationRule).where(CostCenterAllocationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Allocation rule not found")
    lines_result = await db.execute(
        select(CostCenterAllocationRuleLine).where(CostCenterAllocationRuleLine.rule_id == rule.id)
    )
    return _serialize_rule(rule, lines_result.scalars().all())


@router.post("/cost-centers/allocation-rules", response_model=dict)
async def create_allocation_rule(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    lines = data.get("lines") or []
    if not lines:
        raise HTTPException(status_code=400, detail="يجب إضافة سطر توزيع واحد على الأقل")
    total_pct = sum(float(l.get("percentage", 0)) for l in lines)
    if abs(total_pct - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"مجموع النسب يجب أن يكون 100% (الآن {total_pct}%)")
    source = await db.execute(select(Account).where(Account.id == data.get("source_account_id")))
    if not source.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Source account not found")
    rule = CostCenterAllocationRule(
        name=data["name"], name_en=data.get("name_en"),
        description=data.get("description"),
        source_account_id=data["source_account_id"],
        target_account_id=data.get("target_account_id"),
        frequency=data.get("frequency", "ONCE"),
        is_active=data.get("is_active", True),
        created_by=current_user.id, created_at=datetime.now(UTC).replace(tzinfo=None),
        updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(rule)
    await db.flush()
    for l in lines:
        db.add(CostCenterAllocationRuleLine(
            rule_id=rule.id, cost_center_id=l["cost_center_id"],
            percentage=float(l.get("percentage", 0)),
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))
    await add_audit_log(db, "CostCenterAllocationRule", rule.id, "CREATE", current_user,
                        {"name": data["name"]})
    return {"id": rule.id, "message": "Allocation rule created"}


@router.put("/cost-centers/allocation-rules/{rule_id}", response_model=dict)
async def update_allocation_rule(
    rule_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    result = await db.execute(select(CostCenterAllocationRule).where(CostCenterAllocationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Allocation rule not found")
    if "lines" in data and data["lines"] is not None:
        lines = data["lines"]
        total_pct = sum(float(l.get("percentage", 0)) for l in lines)
        if abs(total_pct - 100.0) > 0.01:
            raise HTTPException(status_code=400,
                                detail=f"مجموع النسب يجب أن يكون 100% (الآن {total_pct}%)")
    for key in ("name", "name_en", "description", "source_account_id",
                "target_account_id", "frequency", "is_active"):
        if key in data:
            setattr(rule, key, data[key])
    rule.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    if "lines" in data and data["lines"] is not None:
        await db.execute(text("DELETE FROM cost_center_allocation_rule_lines WHERE rule_id = :rid"),
                         {"rid": rule_id})
        for l in data["lines"]:
            db.add(CostCenterAllocationRuleLine(
                rule_id=rule_id, cost_center_id=l["cost_center_id"],
                percentage=float(l.get("percentage", 0)),
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
    await add_audit_log(db, "CostCenterAllocationRule", rule.id, "UPDATE", current_user,
                        {"changes": list(data.keys())})
    return {"message": "Allocation rule updated"}


@router.delete("/cost-centers/allocation-rules/{rule_id}", response_model=MessageResponse)
async def delete_allocation_rule(
    rule_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("MANAGE_SETTINGS")),
):
    result = await db.execute(select(CostCenterAllocationRule).where(CostCenterAllocationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Allocation rule not found")
    await db.execute(text("DELETE FROM cost_center_allocation_rule_lines WHERE rule_id = :rid"),
                     {"rid": rule_id})
    await db.execute(text("DELETE FROM cost_center_allocation_rules WHERE id = :rid"),
                     {"rid": rule_id})
    await add_audit_log(db, "CostCenterAllocationRule", rule_id, "DELETE", current_user,
                        {"name": rule.name})
    return MessageResponse(message="Allocation rule deleted")


async def _allocation_window(db: AsyncSession, data: dict):
    """Resolve (from, to) for an allocation rule run."""
    fiscal_period_id = data.get("fiscal_period_id")
    if fiscal_period_id:
        period_result = await db.execute(select(FiscalPeriod).where(FiscalPeriod.id == fiscal_period_id))
        period = period_result.scalar_one_or_none()
        if not period:
            raise HTTPException(status_code=404, detail="Fiscal period not found")
        return period.start_date, period.end_date
    fd = await _parse_date_or_none(data.get("from_date"), "from_date")
    td = await _parse_date_or_none(data.get("to_date"), "to_date")
    if not fd or not td:
        raise HTTPException(status_code=400,
                            detail="حدد الفترة: fiscal_period_id أو from_date و to_date")
    if fd >= td:
        raise HTTPException(status_code=400, detail="from_date يجب أن يكون قبل to_date")
    return fd, td


async def _rule_with_lines(db: AsyncSession, rule_id: int):
    result = await db.execute(select(CostCenterAllocationRule).where(CostCenterAllocationRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Allocation rule not found")
    if not rule.is_active:
        raise HTTPException(status_code=400, detail="Allocation rule is inactive")
    lines_result = await db.execute(
        select(CostCenterAllocationRuleLine).where(CostCenterAllocationRuleLine.rule_id == rule_id)
    )
    lines = lines_result.scalars().all()
    if not lines:
        raise HTTPException(status_code=400, detail="Allocation rule has no lines")
    return rule, lines


async def _source_account_balance(db: AsyncSession, account_id: int, fd, td) -> float:
    """Period net balance of the source account (positive = debit-side balance)."""
    acc_result = await db.execute(select(Account).where(Account.id == account_id))
    account = acc_result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Source account not found")
    bal_result = await db.execute(
        select(
            func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
        )
        .join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id)
        .where(JournalEntryLine.account_id == account_id,
               JournalEntry.status.in_(_LEDGER_STATUSES),
               JournalEntry.entry_date >= fd,
               JournalEntry.entry_date <= td)
    )
    row = bal_result.one()
    dr = float(row.total_debit or 0)
    cr = float(row.total_credit or 0)
    if account.account_type in ("asset", "expense"):
        return dr - cr
    return cr - dr


@router.post("/cost-centers/allocation-rules/{rule_id}/preview")
async def preview_allocation_rule(
    rule_id: int,
    data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Preview the distribution of a rule over a period without posting."""
    rule, lines = await _rule_with_lines(db, rule_id)
    fd, td = await _allocation_window(db, data)
    balance = await _source_account_balance(db, rule.source_account_id, fd, td)
    breakdown = []
    for line in lines:
        pct = float(line.percentage or 0)
        amount = round(balance * pct / 100.0, 4)
        cc_result = await db.execute(select(CostCenter).where(CostCenter.id == line.cost_center_id))
        cc = cc_result.scalar_one_or_none()
        breakdown.append({
            "cost_center_id": line.cost_center_id,
            "cost_center_code": cc.code if cc else None,
            "cost_center_name": cc.name if cc else "?",
            "percentage": pct,
            "amount": amount,
        })
    target = await db.execute(select(Account).where(Account.id == (rule.target_account_id or rule.source_account_id)))
    target_acc = target.scalar_one_or_none()
    return {
        "rule_id": rule.id, "rule_name": rule.name,
        "source_account_id": rule.source_account_id,
        "source_account_code": (await _account_code(db, rule.source_account_id)),
        "target_account_code": (await _account_code(db, target_acc.id)) if target_acc else None,
        "period": {"from": fd.date().isoformat(), "to": td.date().isoformat()},
        "balance": round(balance, 4),
        "breakdown": breakdown,
        "total": round(sum(b["amount"] for b in breakdown), 4),
    }


async def _account_code(db: AsyncSession, account_id: int) -> Optional[str]:
    result = await db.execute(select(Account.account_code).where(Account.id == account_id))
    return result.scalar_one_or_none()


@router.post("/cost-centers/allocation-rules/{rule_id}/apply", response_model=dict)
async def apply_allocation_rule(
    rule_id: int,
    data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission("POST_JOURNAL")),
):
    """Apply an allocation rule: post a balanced reclassification entry.

    Dr  target account (or source when no target is set)   balance * pct  [per cost center]
    Cr  source account                                     total balance
    Cost-center dimension is carried on every debit line.
    """
    rule, lines = await _rule_with_lines(db, rule_id)
    fd, td = await _allocation_window(db, data)
    balance = await _source_account_balance(db, rule.source_account_id, fd, td)
    if balance <= 0.01:
        raise HTTPException(status_code=400,
                            detail=f"رصيد حساب المصدر خلال الفترة غير موجب للترحيل ({balance:.2f})")

    entry_number = await _generate_entry_number(db)
    target_account_id = rule.target_account_id or rule.source_account_id
    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=td,
        fiscal_period_id=data.get("fiscal_period_id"),
        reference_type="CostCenterAllocation",
        reference_id=rule.id,
        description=f"توزيع مراكز تكلفة: {rule.name}",
        status="Posted",
        created_by=current_user.id,
        created_at=datetime.now(UTC).replace(tzinfo=None),
        posted_by=current_user.id,
        posted_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(entry)
    await db.flush()
    total_dr = 0.0
    for line in lines:
        amount = round(balance * float(line.percentage or 0) / 100.0, 4)
        if abs(amount) < 0.005:
            continue
        db.add(JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=target_account_id,
            description=f"{rule.name} - مركز تكلفة",
            debit=amount, credit=0.0,
            cost_center_id=line.cost_center_id,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        ))
        total_dr += amount
    db.add(JournalEntryLine(
        journal_entry_id=entry.id,
        account_id=rule.source_account_id,
        description=f"تسوية توزيع: {rule.name}",
        debit=0.0, credit=round(balance, 4),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    await db.flush()
    await add_audit_log(db, "CostCenterAllocationRule", rule.id, "APPLY", current_user,
                        {"entry_number": entry_number, "amount": round(balance, 4),
                         "from": fd.date().isoformat(), "to": td.date().isoformat()})
    return {
        "message": "تم ترحيل توزيع مراكز التكلفة",
        "entry_number": entry_number,
        "entry_id": entry.id,
        "total_debit": round(total_dr, 4),
        "total_credit": round(balance, 4),
        "lines": len(lines),
    }


@router.get("/cost-centers/{cc_id}")
async def get_cost_center(cc_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CostCenter).where(CostCenter.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    return {"id": cc.id, "code": cc.code, "name": cc.name, "name_en": cc.name_en,
            "parent_id": cc.parent_id, "is_active": bool(cc.is_active),
            "created_at": cc.created_at.isoformat() if cc.created_at else None}

@router.put("/cost-centers/{cc_id}", response_model=dict)
async def update_cost_center(cc_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(CostCenter).where(CostCenter.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    if data.get("code") and data["code"] != cc.code:
        dup = await db.execute(select(CostCenter).where(CostCenter.code == data["code"], CostCenter.id != cc_id))
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Cost center code already exists")
    await db.execute(update(CostCenter).where(CostCenter.id == cc_id).values(
        code=data.get("code", cc.code), name=data.get("name", cc.name),
        name_en=data.get("name_en", cc.name_en), parent_id=data.get("parent_id", cc.parent_id),
    ))
    await add_audit_log(db, "CostCenter", cc.id, "UPDATE", current_user,
                        {"changes": list(data.keys())})
    return {"message": "Cost center updated"}

@router.delete("/cost-centers/{cc_id}", response_model=MessageResponse)
async def delete_cost_center(cc_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(CostCenter).where(CostCenter.id == cc_id))
    cc = result.scalar_one_or_none()
    if not cc:
        raise HTTPException(status_code=404, detail="Cost center not found")
    await db.execute(update(CostCenter).where(CostCenter.id == cc_id).values(is_active=False))
    await add_audit_log(db, "CostCenter", cc.id, "DELETE", current_user,
                        {"code": cc.code, "deactivated": True})
    return MessageResponse(message="Cost center deactivated")


@router.get("/recurring-je-templates")
async def list_recurring_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    from app.models.accounting import RecurringJETemplate
    query = select(RecurringJETemplate)
    if current_user.company_id:
        query = query.where(
            (RecurringJETemplate.company_id == current_user.company_id)
            | (RecurringJETemplate.company_id.is_(None))
        )
    result = await db.execute(query.order_by(RecurringJETemplate.id.desc()))
    templates = result.scalars().all()
    return [{
        "id": t.id, "name": t.name, "name_en": t.name_en, "description": t.description,
        "frequency": t.frequency, "next_run_date": str(t.next_run_date) if t.next_run_date else None,
        "last_run_date": str(t.last_run_date) if t.last_run_date else None,
        "is_active": bool(t.is_active), "template_data": t.template_data,
        "created_at": t.created_at.isoformat() if t.created_at else None,
    } for t in templates]


def _serialize_template(t) -> dict:
    return {
        "id": t.id, "name": t.name, "name_en": t.name_en, "description": t.description,
        "frequency": t.frequency, "next_run_date": str(t.next_run_date) if t.next_run_date else None,
        "last_run_date": str(t.last_run_date) if t.last_run_date else None,
        "is_active": bool(t.is_active), "template_data": t.template_data,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }


@router.get("/recurring-je-templates/{template_id}", response_model=dict)
async def get_recurring_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models.accounting import RecurringJETemplate
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _serialize_template(template)


@router.post("/recurring-je-templates", response_model=dict)
async def create_recurring_template(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_JOURNAL"))):
    from app.services.recurring_je import normalize_frequency
    from app.models.accounting import RecurringJETemplate
    import json
    company_id = getattr(current_user, "company_id", None)
    if "template_data" in data and data["template_data"]:
        plan = json.loads(json.dumps(data["template_data"]))
        if not (plan.get("lines") or []):
            raise HTTPException(status_code=400, detail="Template must contain at least one journal line")
    template = RecurringJETemplate(
        name=data.get("name", ""), name_en=data.get("name_en"),
        description=data.get("description"), frequency=normalize_frequency(data.get("frequency")),
        next_run_date=data.get("next_run_date"), is_active=data.get("is_active", True),
        template_data=json.dumps(data.get("template_data")) if isinstance(data.get("template_data"), (dict, list)) else (data.get("template_data") or None),
        created_by=current_user.id, company_id=company_id,
        created_at=datetime.now(UTC).replace(tzinfo=None), updated_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(template)
    await db.flush()
    return {"id": template.id, "message": "Template created"}

@router.put("/recurring-je-templates/{template_id}", response_model=dict)
async def update_recurring_template(template_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_JOURNAL"))):
    from app.services.recurring_je import normalize_frequency
    from app.models.accounting import RecurringJETemplate
    import json
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    update_vals = {}
    for field in ["name", "name_en", "description", "next_run_date", "is_active"]:
        if field in data:
            update_vals[field] = data[field]
    if "frequency" in data:
        update_vals["frequency"] = normalize_frequency(data["frequency"])
    if "template_data" in data:
        if data["template_data"] is not None:
            plan = json.loads(json.dumps(data["template_data"]))
            if not (plan.get("lines") or []):
                raise HTTPException(status_code=400, detail="Template must contain at least one journal line")
        update_vals["template_data"] = json.dumps(data["template_data"]) if data["template_data"] else None
    update_vals["updated_at"] = datetime.now(UTC).replace(tzinfo=None)
    await db.execute(update(RecurringJETemplate).where(RecurringJETemplate.id == template_id).values(**update_vals))
    return {"message": "Template updated"}

@router.delete("/recurring-je-templates/{template_id}", response_model=MessageResponse)
async def delete_recurring_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_JOURNAL"))):
    from app.models.accounting import RecurringJETemplate
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.execute(update(RecurringJETemplate).where(RecurringJETemplate.id == template_id).values(is_active=False, updated_at=datetime.now(UTC).replace(tzinfo=None)))
    return MessageResponse(message="Template deleted")

@router.post("/recurring-je-templates/{template_id}/toggle", response_model=dict)
async def toggle_recurring_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("EDIT_JOURNAL"))):
    """Enable or disable automatic scheduling for a template."""
    from app.models.accounting import RecurringJETemplate
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    new_state = not bool(template.is_active)
    await db.execute(update(RecurringJETemplate).where(RecurringJETemplate.id == template_id).values(
        is_active=new_state, updated_at=datetime.now(UTC).replace(tzinfo=None),
    ))
    return {"id": template_id, "is_active": new_state, "message": "Template active" if new_state else "Template paused"}

@router.post("/recurring-je-templates/{template_id}/preview", response_model=dict)
async def preview_recurring_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Preview the journal entry that would be generated WITHOUT persisting anything."""
    from app.services.recurring_je import compute_run_plan
    from app.models.accounting import RecurringJETemplate
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    plan = compute_run_plan(template)
    if plan is None:
        raise HTTPException(status_code=400, detail="Template has no journal lines defined")
    entry_date = datetime.now(UTC).replace(tzinfo=None)
    return {
        "template_id": template.id,
        "name": template.name,
        "entry_number": "PREVIEW",
        "entry_date": entry_date.isoformat(),
        "description": plan["description"],
        "lines": plan["lines"],
        "total_debit": plan["total_debit"],
        "total_credit": plan["total_credit"],
        "balanced": plan["balanced"],
        "next_run_date": str(template.next_run_date) if template.next_run_date else None,
    }

@router.post("/recurring-je-templates/{template_id}/run", response_model=dict)
async def run_recurring_template(template_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("POST_JOURNAL"))):
    from app.services.recurring_je import run_template
    from app.models.accounting import RecurringJETemplate
    result = await db.execute(select(RecurringJETemplate).where(RecurringJETemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    try:
        entry = await run_template(
            db, template,
            company_id=getattr(current_user, "company_id", None),
            actor_user_id=current_user.id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await add_audit_log(db, "JournalEntry", entry.id, "POST", current_user,
                        {"entry_number": entry.entry_number, "source": "recurring_template_manual"})
    return {"id": entry.id, "entry_number": entry.entry_number, "status": "Posted", "message": "Journal entry created and posted from template"}
