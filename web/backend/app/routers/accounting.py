import math
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.models.accounting import Account, JournalEntry, JournalEntryLine, FiscalPeriod, CostCenter
from app.models.user import User
from app.schemas.accounting import AccountCreate, AccountResponse, JournalEntryCreate
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user

router = APIRouter()


# ── Accounts ──────────────────────────────────────────────────

@router.get("/accounts", response_model=PaginationResponse)
async def list_accounts(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Account)
    count_query = select(func.count(Account.id))
    if search:
        q = Account.account_code.ilike(f"%{search}%") | Account.account_name.ilike(f"%{search}%")
        query = query.where(q)
        count_query = count_query.where(q)
    if account_type:
        query = query.where(Account.account_type == account_type)
        count_query = count_query.where(Account.account_type == account_type)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(Account.account_code).offset(offset).limit(per_page)
    result = await db.execute(query)
    accounts = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[AccountResponse.model_validate(a).model_dump() for a in accounts],
    )


@router.get("/accounts/{account_id}", response_model=AccountResponse)
async def get_account(account_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return AccountResponse.model_validate(account)


@router.post("/accounts", response_model=dict)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    account = Account(
        account_code=data.account_code, account_name=data.account_name,
        account_name_en=data.account_name_en, account_type=data.account_type,
        parent_id=data.parent_id, is_control=data.is_control,
        currency_id=data.currency_id, opening_balance=data.opening_balance,
        opening_balance_date=data.opening_balance_date, notes=data.notes,
        created_at=datetime.utcnow(),
    )
    db.add(account)
    await db.flush()
    return {"id": account.id, "message": "Account created"}


@router.put("/accounts/{account_id}", response_model=dict)
async def update_account(account_id: int, data: AccountCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Account).where(Account.id == account_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Account not found")
    await db.execute(update(Account).where(Account.id == account_id).values(
        account_code=data.account_code, account_name=data.account_name,
        account_name_en=data.account_name_en, account_type=data.account_type,
        parent_id=data.parent_id, is_control=data.is_control,
        currency_id=data.currency_id, opening_balance=data.opening_balance,
        opening_balance_date=data.opening_balance_date, notes=data.notes,
    ))
    return {"message": "Account updated"}


@router.delete("/accounts/{account_id}", response_model=MessageResponse)
async def delete_account(account_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(update(Account).where(Account.id == account_id).values(is_active=False))
    return MessageResponse(message="Account deactivated")


# ── Journal Entries ───────────────────────────────────────────

@router.get("/journal-entries", response_model=PaginationResponse)
async def list_journal_entries(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(JournalEntry)
    count_query = select(func.count(JournalEntry.id))
    if status:
        query = query.where(JournalEntry.status == status)
        count_query = count_query.where(JournalEntry.status == status)

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
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
            "lines": [{"id": l.id, "journal_entry_id": l.journal_entry_id, "account_id": l.account_id,
                        "description": l.description, "debit": l.debit, "credit": l.credit,
                        "currency_rate": l.currency_rate, "cost_center_id": l.cost_center_id}
                       for l in lines],
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
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "lines": [{"id": l.id, "journal_entry_id": l.journal_entry_id, "account_id": l.account_id,
                    "description": l.description, "debit": l.debit, "credit": l.credit,
                    "currency_rate": l.currency_rate, "cost_center_id": l.cost_center_id}
                   for l in lines],
    }


@router.post("/journal-entries", response_model=dict)
async def create_journal_entry(data: JournalEntryCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    entry_count = (await db.execute(select(func.count(JournalEntry.id)))).scalar() or 0
    entry_number = f"JE-{datetime.now().year}-{entry_count + 1:06d}"

    entry = JournalEntry(
        entry_number=entry_number, entry_date=data.entry_date,
        fiscal_period_id=data.fiscal_period_id, reference_type=data.reference_type,
        reference_id=data.reference_id, description=data.description,
        status="draft", created_by=current_user.id, created_at=datetime.utcnow(),
    )
    db.add(entry)
    await db.flush()

    for line_data in data.lines:
        db.add(JournalEntryLine(
            journal_entry_id=entry.id, account_id=line_data.account_id,
            description=line_data.description, debit=line_data.debit,
            credit=line_data.credit, currency_id=line_data.currency_id,
            currency_rate=line_data.currency_rate, cost_center_id=line_data.cost_center_id,
            created_at=datetime.utcnow(),
        ))
    await db.flush()
    return {"id": entry.id, "entry_number": entry_number, "message": "Journal entry created"}


@router.post("/journal-entries/{entry_id}/post", response_model=MessageResponse)
async def post_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft entries can be posted")

    lines_result = await db.execute(select(JournalEntryLine).where(JournalEntryLine.journal_entry_id == entry_id))
    lines = lines_result.scalars().all()
    total_debit = sum(l.debit for l in lines)
    total_credit = sum(l.credit for l in lines)
    if abs(total_debit - total_credit) > 0.01:
        raise HTTPException(status_code=400, detail=f"Debits ({total_debit}) != Credits ({total_credit})")

    await db.execute(update(JournalEntry).where(JournalEntry.id == entry_id).values(
        status="posted", posted_by=current_user.id, posted_at=datetime.utcnow(),
    ))
    return MessageResponse(message="Journal entry posted")


@router.post("/journal-entries/{entry_id}/void", response_model=MessageResponse)
async def void_journal_entry(entry_id: int, reason: str = "", db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(JournalEntry).where(JournalEntry.id == entry_id))
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    if entry.status != "posted":
        raise HTTPException(status_code=400, detail="Only posted entries can be voided")
    await db.execute(update(JournalEntry).where(JournalEntry.id == entry_id).values(
        status="voided", voided_by=current_user.id,
        voided_at=datetime.utcnow(), void_reason=reason,
    ))
    return MessageResponse(message="Journal entry voided")


# ── Trial Balance ─────────────────────────────────────────────

@router.get("/trial-balance")
async def trial_balance(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    fiscal_period_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    accounts_query = select(Account).where(Account.is_active == True).order_by(Account.account_code)
    total_accounts = (await db.execute(select(func.count(Account.id)).where(Account.is_active == True))).scalar() or 0
    offset = (page - 1) * per_page
    accounts_result = await db.execute(accounts_query.offset(offset).limit(per_page))
    accounts = accounts_result.scalars().all()

    lines_query = select(JournalEntryLine).join(JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id).where(JournalEntry.status == "posted")
    lines_result = await db.execute(lines_query)
    lines = lines_result.scalars().all()

    balances = {}
    for line in lines:
        if line.account_id not in balances:
            balances[line.account_id] = {"debit": 0, "credit": 0}
        balances[line.account_id]["debit"] += line.debit
        balances[line.account_id]["credit"] += line.credit

    trial = []
    total_debit = 0
    total_credit = 0
    for account in accounts:
        b = balances.get(account.id, {"debit": 0, "credit": 0})
        net = b["debit"] - b["credit"] + account.opening_balance
        trial.append({
            "account_id": account.id, "account_code": account.account_code,
            "account_name": account.account_name, "account_type": account.account_type,
            "debit": b["debit"], "credit": b["credit"],
            "opening_balance": account.opening_balance, "net_balance": net,
        })
        total_debit += b["debit"]
        total_credit += b["credit"]

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
async def create_fiscal_period(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    fp = FiscalPeriod(
        name=data.get("name", ""), name_en=data.get("name_en"),
        start_date=data.get("start_date", ""), end_date=data.get("end_date", ""),
        is_closed=data.get("is_closed", False), is_locked=data.get("is_locked", False),
    )
    db.add(fp)
    await db.flush()
    return {"id": fp.id, "message": "Fiscal period created"}


# ── Cost Centers ──────────────────────────────────────────────

@router.get("/cost-centers")
async def list_cost_centers(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(CostCenter).where(CostCenter.is_active == True).order_by(CostCenter.name))
    return [{"id": cc.id, "code": cc.code, "name": cc.name, "name_en": cc.name_en, "parent_id": cc.parent_id}
            for cc in result.scalars().all()]


@router.post("/cost-centers", response_model=dict)
async def create_cost_center(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    cc = CostCenter(code=data.get("code"), name=data.get("name", ""),
                    name_en=data.get("name_en"), parent_id=data.get("parent_id"),
                    created_at=datetime.utcnow())
    db.add(cc)
    await db.flush()
    return {"id": cc.id, "message": "Cost center created"}
