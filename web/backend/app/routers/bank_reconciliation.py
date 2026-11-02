"""
Bank Reconciliation endpoints for matching bank transactions with journal entries.
"""

from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.bank_reconciliation import BankReconciliation, BankReconciliationItem, BankStatementImport
from app.models.payments import Bank, BankTransaction
from app.utils.deps import get_current_user, require_permission
from app.utils.validation import require_fields, parse_date_value

router = APIRouter()


@router.get("/reconciliations")
async def list_reconciliations(
    bank_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all bank reconciliations"""
    query = select(BankReconciliation).order_by(BankReconciliation.created_at.desc())
    if bank_id:
        query = query.where(BankReconciliation.bank_id == bank_id)
    if status:
        query = query.where(BankReconciliation.status == status)
    result = await db.execute(query)
    reconciliations = result.scalars().all()
    return [{"id": r.id, "bankId": r.bank_id, "reconciliationDate": str(r.reconciliation_date),
             "statementDate": str(r.statement_date) if r.statement_date else None,
             "statementBalance": float(r.statement_balance), "bookBalance": float(r.book_balance),
             "difference": float(r.difference), "status": r.status, "notes": r.notes,
             "createdAt": str(r.created_at) if r.created_at else None} for r in reconciliations]


@router.post("/reconciliations")
async def create_reconciliation(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("RECONCILE_BANK")),
):
    """Create a new bank reconciliation"""
    require_fields(data, ["bank_id"])
    # Get current bank balance
    bank_result = await db.execute(select(Bank).where(Bank.id == data["bank_id"]))
    bank = bank_result.scalar_one_or_none()
    if not bank:
        raise HTTPException(status_code=404, detail="Bank not found")

    reconciliation = BankReconciliation(
        bank_id=data["bank_id"],
        reconciliation_date=datetime.now(),
        statement_date=parse_date_value(data.get("statement_date"), "statement_date") or datetime.now(),
        statement_balance=data.get("statement_balance", 0.0),
        book_balance=bank.current_balance or 0.0,
        difference=data.get("statement_balance", 0.0) - (bank.current_balance or 0.0),
        status="DRAFT",
        notes=data.get("notes"),
        company_id=data.get("company_id"),
        created_at=datetime.now(),
    )
    db.add(reconciliation)
    await db.commit()
    await db.refresh(reconciliation)
    return {"id": reconciliation.id, "message": "Reconciliation created"}


@router.get("/reconciliations/{reconciliation_id}")
async def get_reconciliation(
    reconciliation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific reconciliation with its items"""
    result = await db.execute(select(BankReconciliation).where(BankReconciliation.id == reconciliation_id))
    reconciliation = result.scalar_one_or_none()
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    # Get items
    items_result = await db.execute(
        select(BankReconciliationItem)
        .where(BankReconciliationItem.reconciliation_id == reconciliation_id)
    )
    items = items_result.scalars().all()

    return {
        "id": reconciliation.id,
        "bank_id": reconciliation.bank_id,
        "reconciliation_date": str(reconciliation.reconciliation_date),
        "statement_date": str(reconciliation.statement_date) if reconciliation.statement_date else None,
        "statement_balance": float(reconciliation.statement_balance),
        "book_balance": float(reconciliation.book_balance),
        "difference": float(reconciliation.difference),
        "status": reconciliation.status,
        "notes": reconciliation.notes,
        "items": [{"id": i.id, "bank_transaction_id": i.bank_transaction_id,
                   "journal_entry_id": i.journal_entry_id, "amount": float(i.amount),
                   "description": i.description, "reconciled": i.reconciled,
                   "status": "MATCHED" if i.reconciled else "UNMATCHED",
                   "transaction_date": str(i.reconciled_at) if i.reconciled_at else None} for i in items],
    }


@router.get("/reconciliations/{reconciliation_id}/unmatched")
async def get_unmatched_transactions(
    reconciliation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get unmatched bank transactions for reconciliation"""
    # Get reconciliation
    rec_result = await db.execute(select(BankReconciliation).where(BankReconciliation.id == reconciliation_id))
    reconciliation = rec_result.scalar_one_or_none()
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")

    # Get already matched transaction IDs
    matched_result = await db.execute(
        select(BankReconciliationItem.bank_transaction_id)
        .where(BankReconciliationItem.reconciliation_id == reconciliation_id)
    )
    matched_ids = [r[0] for r in matched_result.all()]

    # Get unmatched bank transactions
    conditions = [BankTransaction.bank_id == reconciliation.bank_id, BankTransaction.reconciled == False]
    if matched_ids:
        conditions.append(BankTransaction.id.notin_(matched_ids))

    transactions_result = await db.execute(
        select(BankTransaction)
        .where(and_(*conditions))
        .order_by(BankTransaction.transaction_date)
    )
    transactions = transactions_result.scalars().all()

    return [{"id": t.id, "transaction_type": t.transaction_type, "amount": t.amount,
             "transaction_date": str(t.transaction_date), "description": t.description,
             "reference_number": t.reference_number, "reconciled": t.reconciled,
             "journal_entry_id": t.journal_entry_id} for t in transactions]


@router.post("/reconciliations/{reconciliation_id}/match")
async def match_transactions(
    reconciliation_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("RECONCILE_BANK")),
):
    """
    Match a bank transaction with a journal entry.
    Request body: { "bank_transaction_id": int, "journal_entry_id": int, "amount": float, "description": str }
    """
    # Get reconciliation
    rec_result = await db.execute(select(BankReconciliation).where(BankReconciliation.id == reconciliation_id))
    reconciliation = rec_result.scalar_one_or_none()
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    if reconciliation.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Can only match transactions in DRAFT status")

    # Check if transaction already matched
    existing = await db.execute(
        select(BankReconciliationItem)
        .where(BankReconciliationItem.reconciliation_id == reconciliation_id)
        .where(BankReconciliationItem.bank_transaction_id == data["bank_transaction_id"])
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Transaction already matched")

    # Create match item
    item = BankReconciliationItem(
        reconciliation_id=reconciliation_id,
        bank_transaction_id=data["bank_transaction_id"],
        journal_entry_id=data.get("journal_entry_id"),
        amount=data["amount"],
        description=data.get("description"),
        reconciled=True,
        reconciled_at=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(item)

    # Update bank transaction as reconciled
    await db.execute(
        BankTransaction.__table__.update()
        .where(BankTransaction.id == data["bank_transaction_id"])
        .values(reconciled=True, reconciliation_date=datetime.now())
    )

    # Update book balance: DEPOSIT adds, WITHDRAWAL subtracts
    txn_type = data.get("transaction_type", "DEPOSIT")
    if txn_type == "WITHDRAWAL":
        reconciliation.book_balance -= data["amount"]
    else:
        reconciliation.book_balance += data["amount"]
    reconciliation.difference = reconciliation.statement_balance - reconciliation.book_balance

    await db.commit()
    return {"success": True, "message": "Transaction matched"}


@router.post("/reconciliations/{reconciliation_id}/unmatch")
async def unmatch_transaction(
    reconciliation_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("RECONCILE_BANK")),
):
    """Unmatch a previously matched transaction"""
    item_id = data.get("item_id")
    if not item_id:
        raise HTTPException(status_code=400, detail="item_id is required")

    # Get item
    item_result = await db.execute(
        select(BankReconciliationItem)
        .where(BankReconciliationItem.id == item_id)
        .where(BankReconciliationItem.reconciliation_id == reconciliation_id)
    )
    item = item_result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Match item not found")

    # Get reconciliation
    rec_result = await db.execute(select(BankReconciliation).where(BankReconciliation.id == reconciliation_id))
    reconciliation = rec_result.scalar_one_or_none()
    if reconciliation.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Can only unmatch in DRAFT status")

    # Update bank transaction
    await db.execute(
        BankTransaction.__table__.update()
        .where(BankTransaction.id == item.bank_transaction_id)
        .values(reconciled=False, reconciliation_date=None)
    )

    # Get transaction type to reverse balance correctly
    txn_result = await db.execute(select(BankTransaction).where(BankTransaction.id == item.bank_transaction_id))
    txn = txn_result.scalar_one_or_none()
    txn_type = txn.transaction_type if txn else "DEPOSIT"

    # Reverse book balance: DEPOSIT was added, so subtract; WITHDRAWAL was subtracted, so add
    if txn_type == "WITHDRAWAL":
        reconciliation.book_balance += item.amount
    else:
        reconciliation.book_balance -= item.amount
    reconciliation.difference = reconciliation.statement_balance - reconciliation.book_balance

    # Delete the match item
    await db.delete(item)
    await db.commit()
    return {"success": True, "message": "Transaction unmatched"}


@router.post("/reconciliations/{reconciliation_id}/complete")
async def complete_reconciliation(
    reconciliation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("RECONCILE_BANK")),
):
    """Complete a bank reconciliation"""
    result = await db.execute(select(BankReconciliation).where(BankReconciliation.id == reconciliation_id))
    reconciliation = result.scalar_one_or_none()
    if not reconciliation:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
    if reconciliation.status != "DRAFT":
        raise HTTPException(status_code=400, detail="Reconciliation is not in DRAFT status")
    if abs(reconciliation.difference) > 0.01:
        raise HTTPException(status_code=400, detail=f"Reconciliation is not balanced. Difference: {reconciliation.difference}")

    reconciliation.status = "COMPLETED"
    reconciliation.reconciled_by = current_user.id if hasattr(current_user, "id") else None
    reconciliation.completed_at = datetime.now()

    await db.commit()
    return {"success": True, "message": "Reconciliation completed"}


@router.get("/unreconciled-transactions")
async def get_unreconciled_transactions(
    bank_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get all unreconciled transactions for a bank"""
    result = await db.execute(
        select(BankTransaction)
        .where(BankTransaction.bank_id == bank_id)
        .where(BankTransaction.reconciled == False)
        .order_by(BankTransaction.transaction_date)
    )
    transactions = result.scalars().all()
    return [{"id": t.id, "transaction_type": t.transaction_type, "amount": t.amount,
             "transaction_date": str(t.transaction_date), "description": t.description,
             "reference_number": t.reference_number} for t in transactions]
