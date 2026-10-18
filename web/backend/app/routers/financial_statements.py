"""
Financial Statements: Balance Sheet, Income Statement (P&L), Cash Flow Statement.
"""

from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.utils.deps import get_current_active_user

router = APIRouter()


@router.get("/balance-sheet")
async def get_balance_sheet(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate Balance Sheet (Statement of Financial Position)
    Assets = Liabilities + Equity
    """
    if not as_of_date:
        as_of_date = date.today()

    # Build conditions
    conditions = [
        Account.is_active == True,
        Account.account_type.in_(["Asset", "Liability", "Equity"]),
    ]
    if company_id:
        conditions.append(Account.company_id == company_id)

    # Get account balances
    query = select(
        Account.id,
        Account.account_code,
        Account.account_name,
        Account.account_type,
        Account.opening_balance,
        func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
        func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
    ).outerjoin(
        JournalEntryLine, Account.id == JournalEntryLine.account_id
    ).outerjoin(
        JournalEntry, and_(
            JournalEntryLine.journal_entry_id == JournalEntry.id,
            JournalEntry.status == "Posted",
            JournalEntry.entry_date <= as_of_date,
        )
    ).where(
        and_(*conditions)
    ).group_by(
        Account.id, Account.account_code, Account.account_name, Account.account_type, Account.opening_balance
    ).order_by(Account.account_code)

    result = await db.execute(query)
    accounts = result.all()

    # Categorize accounts
    assets = []
    liabilities = []
    equity = []
    total_assets = 0.0
    total_liabilities = 0.0
    total_equity = 0.0

    for acc in accounts:
        opening = float(acc.opening_balance or 0)
        debit = float(acc.total_debit or 0)
        credit = float(acc.total_credit or 0)

        # Balance calculation based on type
        if acc.account_type == "Asset":
            balance = opening + debit - credit
        else:  # Liability or Equity
            balance = opening + credit - debit

        balance = round(balance, 4)
        account_data = {
            "id": acc.id,
            "code": acc.account_code,
            "name": acc.account_name,
            "type": acc.account_type,
            "balance": balance,
        }

        if acc.account_type == "Asset":
            assets.append(account_data)
            total_assets += balance
        elif acc.account_type == "Liability":
            liabilities.append(account_data)
            total_liabilities += balance
        elif acc.account_type == "Equity":
            equity.append(account_data)
            total_equity += balance

    return {
        "as_of_date": str(as_of_date),
        "assets": {
            "accounts": assets,
            "total": round(total_assets, 4),
        },
        "liabilities": {
            "accounts": liabilities,
            "total": round(total_liabilities, 4),
        },
        "equity": {
            "accounts": equity,
            "total": round(total_equity, 4),
        },
        "total_liabilities_and_equity": round(total_liabilities + total_equity, 4),
        "is_balanced": abs(total_assets - (total_liabilities + total_equity)) < 0.01,
    }


@router.get("/income-statement")
async def get_income_statement(
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate Income Statement (Profit & Loss)
    Revenue - Expenses = Net Income
    """
    if not period_start:
        period_start = date(date.today().year, 1, 1)
    if not period_end:
        period_end = date.today()

    # Build conditions
    conditions = [
        Account.is_active == True,
        Account.account_type.in_(["Revenue", "Expense"]),
    ]
    if company_id:
        conditions.append(Account.company_id == company_id)

    query = select(
        Account.id,
        Account.account_code,
        Account.account_name,
        Account.account_type,
        Account.opening_balance,
        func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
        func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
    ).outerjoin(
        JournalEntryLine, Account.id == JournalEntryLine.account_id
    ).outerjoin(
        JournalEntry, and_(
            JournalEntryLine.journal_entry_id == JournalEntry.id,
            JournalEntry.status == "Posted",
            JournalEntry.entry_date >= period_start,
            JournalEntry.entry_date <= period_end,
        )
    ).where(
        and_(*conditions)
    ).group_by(
        Account.id, Account.account_code, Account.account_name, Account.account_type, Account.opening_balance
    ).order_by(Account.account_code)

    result = await db.execute(query)
    accounts = result.all()

    revenue_accounts = []
    expense_accounts = []
    total_revenue = 0.0
    total_expenses = 0.0

    for acc in accounts:
        opening = float(acc.opening_balance or 0)
        debit = float(acc.total_debit or 0)
        credit = float(acc.total_credit or 0)

        # For the period, we only care about activity (not opening balance for P&L)
        if acc.account_type == "Revenue":
            balance = credit - debit  # Revenue increases with credit
            total_revenue += balance
            revenue_accounts.append({
                "id": acc.id,
                "code": acc.account_code,
                "name": acc.account_name,
                "balance": round(balance, 4),
            })
        else:  # Expense
            balance = debit - credit  # Expense increases with debit
            total_expenses += balance
            expense_accounts.append({
                "id": acc.id,
                "code": acc.account_code,
                "name": acc.account_name,
                "balance": round(balance, 4),
            })

    net_income = total_revenue - total_expenses

    return {
        "period_start": str(period_start),
        "period_end": str(period_end),
        "revenue": {
            "accounts": revenue_accounts,
            "total": round(total_revenue, 4),
        },
        "expenses": {
            "accounts": expense_accounts,
            "total": round(total_expenses, 4),
        },
        "net_income": round(net_income, 4),
        "is_profit": net_income > 0,
    }


@router.get("/cash-flow-statement")
async def get_cash_flow_statement(
    period_start: Optional[date] = Query(None),
    period_end: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Generate Cash Flow Statement (Simplified)
    Categories: Operating, Investing, Financing
    """
    if not period_start:
        period_start = date(date.today().year, 1, 1)
    if not period_end:
        period_end = date.today()

    # Get all posted journal entries in period
    conditions = [
        JournalEntry.status == "Posted",
        JournalEntry.entry_date >= period_start,
        JournalEntry.entry_date <= period_end,
    ]
    if company_id:
        conditions.append(JournalEntry.company_id == company_id)

    # Get journal items with account info
    query = select(
        JournalEntryLine.account_id,
        Account.account_code,
        Account.account_name,
        Account.account_type,
        func.sum(JournalEntryLine.debit).label("total_debit"),
        func.sum(JournalEntryLine.credit).label("total_credit"),
    ).join(
        JournalEntry, JournalEntryLine.journal_entry_id == JournalEntry.id
    ).join(
        Account, JournalEntryLine.account_id == Account.id
    ).where(
        and_(*conditions)
    ).group_by(
        JournalEntryLine.account_id, Account.account_code, Account.account_name, Account.account_type
    )

    result = await db.execute(query)
    items = result.all()

    # Categorize cash flows (simplified)
    operating_inflows = 0.0
    operating_outflows = 0.0
    investing_inflows = 0.0
    investing_outflows = 0.0
    financing_inflows = 0.0
    financing_outflows = 0.0

    for item in items:
        debit = float(item.total_debit or 0)
        credit = float(item.total_credit or 0)
        code = item.account_code

        # Operating Activities (1xxx current assets, 2xxx current liabilities, 4xxx revenue, 5xxx expenses)
        if code.startswith("11"):  # Current assets (cash, AR, inventory)
            if item.account_type == "Asset":
                operating_outflows += debit
                operating_inflows += credit
        elif code.startswith("21"):  # Current liabilities (AP, accruals)
            if item.account_type == "Liability":
                operating_inflows += credit
                operating_outflows += debit
        elif code.startswith("4"):  # Revenue
            operating_inflows += credit
        elif code.startswith("5"):  # Expenses
            operating_outflows += debit

        # Investing Activities (12xx non-current assets)
        elif code.startswith("12") and not code.startswith("121"):  # Non-current assets (excluding inventory)
            if item.account_type == "Asset":
                investing_outflows += debit
                investing_inflows += credit

        # Financing Activities (22xx non-current liabilities, 3xxx equity)
        elif code.startswith("22") or code.startswith("3"):
            if item.account_type == "Liability":
                financing_inflows += credit
                financing_outflows += debit
            elif item.account_type == "Equity":
                financing_inflows += credit
                financing_outflows += debit

    net_operating = operating_inflows - operating_outflows
    net_investing = investing_inflows - investing_outflows
    net_financing = financing_inflows - financing_outflows
    net_cash_flow = net_operating + net_investing + net_financing

    return {
        "period_start": str(period_start),
        "period_end": str(period_end),
        "operating_activities": {
            "inflows": round(operating_inflows, 4),
            "outflows": round(operating_outflows, 4),
            "net": round(net_operating, 4),
        },
        "investing_activities": {
            "inflows": round(investing_inflows, 4),
            "outflows": round(investing_outflows, 4),
            "net": round(net_investing, 4),
        },
        "financing_activities": {
            "inflows": round(financing_inflows, 4),
            "outflows": round(financing_outflows, 4),
            "net": round(net_financing, 4),
        },
        "net_cash_flow": round(net_cash_flow, 4),
    }


@router.get("/trial-balance-detailed")
async def get_trial_balance_detailed(
    as_of_date: Optional[date] = Query(None),
    company_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Detailed Trial Balance with account groupings and subtotals.
    """
    if not as_of_date:
        as_of_date = date.today()

    conditions = [Account.is_active == True]
    if company_id:
        conditions.append(Account.company_id == company_id)

    query = select(
        Account.id,
        Account.account_code,
        Account.account_name,
        Account.account_type,
        Account.opening_balance,
        func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
        func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
    ).outerjoin(
        JournalEntryLine, Account.id == JournalEntryLine.account_id
    ).outerjoin(
        JournalEntry, and_(
            JournalEntryLine.journal_entry_id == JournalEntry.id,
            JournalEntry.status == "Posted",
            JournalEntry.entry_date <= as_of_date,
        )
    ).where(
        and_(*conditions)
    ).group_by(
        Account.id, Account.account_code, Account.account_name, Account.account_type, Account.opening_balance
    ).order_by(Account.account_code)

    result = await db.execute(query)
    accounts = result.all()

    grouped = {
        "Asset": [],
        "Liability": [],
        "Equity": [],
        "Revenue": [],
        "Expense": [],
    }
    totals = {
        "Asset": {"debit": 0, "credit": 0, "balance": 0},
        "Liability": {"debit": 0, "credit": 0, "balance": 0},
        "Equity": {"debit": 0, "credit": 0, "balance": 0},
        "Revenue": {"debit": 0, "credit": 0, "balance": 0},
        "Expense": {"debit": 0, "credit": 0, "balance": 0},
    }

    grand_total_debit = 0.0
    grand_total_credit = 0.0

    for acc in accounts:
        opening = float(acc.opening_balance or 0)
        debit = float(acc.total_debit or 0)
        credit = float(acc.total_credit or 0)

        if acc.account_type in ["Asset", "Expense"]:
            balance = opening + debit - credit
        else:
            balance = opening + credit - debit

        account_data = {
            "id": acc.id,
            "code": acc.account_code,
            "name": acc.account_name,
            "opening_balance": round(opening, 4),
            "debit": round(debit, 4),
            "credit": round(credit, 4),
            "balance": round(balance, 4),
        }

        grouped[acc.account_type].append(account_data)
        totals[acc.account_type]["debit"] += debit
        totals[acc.account_type]["credit"] += credit
        totals[acc.account_type]["balance"] += balance

        grand_total_debit += debit
        grand_total_credit += credit

    return {
        "as_of_date": str(as_of_date),
        "groups": grouped,
        "totals": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in totals.items()},
        "grand_total_debit": round(grand_total_debit, 4),
        "grand_total_credit": round(grand_total_credit, 4),
        "is_balanced": abs(grand_total_debit - grand_total_credit) < 0.01,
    }
