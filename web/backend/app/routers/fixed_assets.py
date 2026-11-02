"""
Fixed Assets management endpoints with depreciation calculation.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.fixed_assets import AssetCategory, FixedAsset, DepreciationEntry
from app.models.accounting import Account, JournalEntry, JournalEntryLine
from app.schemas.fixed_assets import FixedAssetCreate, AssetCategoryCreate
from app.utils.deps import get_current_user, require_permission
from app.utils.audit import add_audit_log

router = APIRouter()


async def _resolve_account_by_code(db: AsyncSession, code: str, name: str = "", account_type: str = "asset") -> Account:
    """Resolve an account by its code. Creates a placeholder if missing."""
    result = await db.execute(select(Account).where(Account.account_code == code).limit(1))
    account = result.scalar_one_or_none()
    if account:
        return account
    account = Account(
        account_code=code,
        account_name=name or f"Account {code}",
        account_type=account_type,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(account)
    await db.flush()
    return account


async def _generate_entry_number(db: AsyncSession, prefix: str = "JE") -> str:
    # Delegate to the shared self-healing sequence-based generator. A local
    # max-based generator would race the sequence-based writers (gateway +
    # other backend routers) and could hand out a number already taken.
    from app.routers.accounting import _generate_entry_number as _shared
    number = await _shared(db)
    if prefix == "JE":
        return number
    year = datetime.now().year
    result = await db.execute(
        text(
            "SELECT COALESCE(MAX(NULLIF(regexp_replace(entry_number, '^.*-', '', 'g'), '')::bigint), 0) "
            "FROM journal_entries WHERE entry_number LIKE :prefix"
        ),
        {"prefix": f"{prefix}-{year}-%"},
    )
    max_seq = int(result.scalar() or 0)
    return f"{prefix}-{year}-{max_seq + 1:06d}"


async def _generate_asset_code(db: AsyncSession, prefix: str = "FA") -> str:
    """Auto-generate a unique asset code like FA-2026-0001 when none is supplied."""
    year = datetime.now().year
    result = await db.execute(
        text(
            "SELECT COALESCE(MAX(NULLIF(regexp_replace(code, '^.*-', '', 'g'), '')::bigint), 0) "
            "FROM fixed_assets WHERE code LIKE :prefix"
        ),
        {"prefix": f"{prefix}-{year}-%"},
    )
    max_seq = int(result.scalar() or 0)
    return f"{prefix}-{year}-{max_seq + 1:04d}"


async def _post_journal_entry(
    db: AsyncSession,
    entry_number: str,
    entry_date: datetime,
    description: str,
    lines: list,
    posted_by: int | None,
    company_id: int | None,
) -> JournalEntry:
    """Create + post a balanced journal entry."""
    entry = JournalEntry(
        entry_number=entry_number,
        entry_date=entry_date,
        description=description,
        status="Posted",
        created_by=posted_by,
        posted_by=posted_by,
        posted_at=datetime.now(),
        company_id=company_id,
        created_at=datetime.now(),
    )
    db.add(entry)
    await db.flush()
    for line in lines:
        db.add(JournalEntryLine(
            journal_entry_id=entry.id,
            account_id=line["account_id"],
            description=line.get("description"),
            debit=line.get("debit", 0.0),
            credit=line.get("credit", 0.0),
            created_at=datetime.now(),
        ))
    await db.flush()
    return entry


# =============================================================================
# Asset Category Endpoints
# =============================================================================

@router.get("/categories")
async def list_asset_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all asset categories"""
    result = await db.execute(select(AssetCategory).order_by(AssetCategory.code))
    categories = result.scalars().all()
    return [{"id": c.id, "code": c.code, "name": c.name, "name_ar": c.name_ar,
             "depreciation_rate": c.depreciation_rate, "depreciation_method": c.depreciation_method,
             "useful_life_months": c.useful_life_months, "is_active": c.is_active} for c in categories]


@router.post("/categories")
async def create_asset_category(
    data: AssetCategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_ASSETS")),
):
    """Create a new asset category"""
    existing = await db.execute(select(AssetCategory).where(AssetCategory.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category code already exists")

    category = AssetCategory(
        code=data.code,
        name=data.name,
        name_ar=data.name_ar,
        depreciation_rate=data.depreciation_rate,
        depreciation_method=data.depreciation_method,
        useful_life_months=data.useful_life_months,
        gl_account_id=data.gl_account_id,
        depreciation_expense_account_id=data.depreciation_expense_account_id,
        accumulated_depreciation_account_id=data.accumulated_depreciation_account_id,
        description=data.description,
        created_at=datetime.now(),
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
    await add_audit_log(db, "AssetCategory", category.id, "CREATE", current_user,
                        {"code": category.code, "name": category.name})
    await db.commit()
    return {"id": category.id, "code": category.code, "message": "Asset category created"}


# =============================================================================
# Fixed Asset Endpoints
# =============================================================================

@router.get("/")
async def list_fixed_assets(
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all fixed assets"""
    query = select(FixedAsset).order_by(FixedAsset.code)
    if category_id:
        query = query.where(FixedAsset.category_id == category_id)
    if status:
        query = query.where(FixedAsset.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    assets = result.scalars().all()
    return [{"id": a.id, "code": a.code, "name": a.name, "category_id": a.category_id,
             "purchase_date": str(a.purchase_date), "purchase_cost": a.purchase_cost,
             "salvage_value": a.salvage_value, "useful_life_months": a.useful_life_months,
             "accumulated_depreciation": a.accumulated_depreciation, "current_value": a.current_value,
             "status": a.status, "location": a.location} for a in assets]


@router.get("/summary")
async def get_fixed_assets_summary(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get fixed assets summary with totals"""
    result = await db.execute(
        select(
            func.count(FixedAsset.id).label("total_count"),
            func.coalesce(func.sum(FixedAsset.purchase_cost), 0).label("total_cost"),
            func.coalesce(func.sum(FixedAsset.accumulated_depreciation), 0).label("total_depreciation"),
            func.coalesce(func.sum(FixedAsset.current_value), 0).label("total_value"),
        ).where(FixedAsset.status.in_(["ACTIVE", "FULLY_DEPRECIATED"]))
    )
    summary = result.one_or_none()
    return {
        "total_assets": summary.total_count if summary else 0,
        "total_cost": round(float(summary.total_cost if summary else 0), 4),
        "total_accumulated_depreciation": round(float(summary.total_depreciation if summary else 0), 4),
        "total_book_value": round(float(summary.total_value if summary else 0), 4),
    }


@router.get("/depreciation-schedule/{asset_id}")
async def get_depreciation_schedule(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get depreciation schedule for an asset"""
    result = await db.execute(
        select(DepreciationEntry)
        .where(DepreciationEntry.asset_id == asset_id)
        .order_by(DepreciationEntry.period_year, DepreciationEntry.period_month)
    )
    entries = result.scalars().all()
    return [{"id": e.id, "period_month": e.period_month, "period_year": e.period_year,
             "depreciation_amount": e.depreciation_amount,
             "accumulated_depreciation": e.accumulated_depreciation,
             "book_value": e.book_value, "status": e.status} for e in entries]


@router.get("/{asset_id}")
async def get_fixed_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get a specific fixed asset"""
    result = await db.execute(select(FixedAsset).where(FixedAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    return {"id": asset.id, "code": asset.code, "name": asset.name, "name_ar": asset.name_ar,
            "category_id": asset.category_id, "description": asset.description,
            "purchase_date": str(asset.purchase_date), "purchase_cost": asset.purchase_cost,
            "salvage_value": asset.salvage_value, "useful_life_months": asset.useful_life_months,
            "depreciation_method": asset.depreciation_method,
            "accumulated_depreciation": asset.accumulated_depreciation,
            "current_value": asset.current_value, "status": asset.status,
            "location": asset.location, "serial_number": asset.serial_number,
            "supplier_name": asset.supplier_name, "invoice_number": asset.invoice_number}


@router.post("/")
async def create_fixed_asset(
    data: FixedAssetCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_ASSETS")),
):
    """Create a new fixed asset"""
    if not data.code or not data.code.strip():
        # Auto-number the asset when no code is supplied (FA-YYYY-NNNN)
        data.code = await _generate_asset_code(db, prefix="FA")

    existing = await db.execute(select(FixedAsset).where(FixedAsset.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Asset code already exists")

    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == data.category_id))
    category = cat_result.scalar_one_or_none()
    if not category:
        raise HTTPException(status_code=400, detail="Asset category not found")

    purchase_date = data.purchase_date
    if purchase_date and isinstance(purchase_date, str):
        try:
            purchase_date = datetime.fromisoformat(purchase_date)
        except ValueError:
            purchase_date = datetime.strptime(purchase_date, "%Y-%m-%d")
    elif not purchase_date:
        purchase_date = datetime.now()

    asset = FixedAsset(
        code=data.code,
        asset_code=data.code,
        name=data.name,
        name_ar=data.name_ar,
        category_id=data.category_id,
        description=data.description,
        purchase_date=purchase_date,
        purchase_cost=data.purchase_cost,
        salvage_value=data.salvage_value,
        useful_life_months=data.useful_life_months,
        depreciation_method=data.depreciation_method,
        accumulated_depreciation=0.0,
        current_value=data.purchase_cost,
        status="ACTIVE",
        location=data.location,
        serial_number=data.serial_number,
        supplier_name=data.supplier_name,
        invoice_number=data.invoice_number,
        company_id=data.company_id,
        branch_id=data.branch_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    db.add(asset)
    await db.flush()

    # Post acquisition journal entry: Dr Fixed Asset / Cr Accounts Payable (2111)
    gl_account = await _resolve_account_by_code(
        db, str(category.gl_account_id) if category.gl_account_id else "1530",
        name=f"Fixed Assets ({category.name})",
    )
    if data.purchase_cost > 0:
        entry = await _post_journal_entry(
            db,
            entry_number=await _generate_entry_number(db),
            entry_date=purchase_date,
            description=f"Acquisition of fixed asset {data.code} - {data.name}",
            lines=[
                {"account_id": gl_account.id, "debit": data.purchase_cost,
                 "description": f"Capitalize cost of asset {data.code}"},
                {"account_id": (await _resolve_account_by_code(db, "2111", name="حسابات الموردين", account_type="liability")).id,
                 "credit": data.purchase_cost, "description": f"Payable for asset {data.code}"},
            ],
            posted_by=current_user.id if hasattr(current_user, "id") else None,
            company_id=data.company_id,
        )
        asset.journal_entry_id = entry.id

    await db.commit()
    await db.refresh(asset)
    await add_audit_log(db, "FixedAsset", asset.id, "CREATE", current_user,
                        {"code": asset.code, "name": asset.name, "cost": asset.purchase_cost})
    await db.commit()
    return {"id": asset.id, "code": asset.code, "message": "Fixed asset created"}


@router.put("/{asset_id}")
async def update_fixed_asset(
    asset_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_ASSETS")),
):
    """Update a fixed asset"""
    result = await db.execute(select(FixedAsset).where(FixedAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    if asset.status == "DISPOSED":
        raise HTTPException(status_code=400, detail="Cannot update disposed asset")

    for key, value in data.items():
        if hasattr(asset, key) and key not in ["id", "code", "created_at", "accumulated_depreciation", "current_value"]:
            setattr(asset, key, value)
    asset.updated_at = datetime.now()
    await db.commit()
    await add_audit_log(db, "FixedAsset", asset.id, "UPDATE", current_user,
                        {"changes": list(data.keys())})
    await db.commit()
    return {"success": True, "message": "Fixed asset updated"}


@router.post("/{asset_id}/depreciate")
async def calculate_monthly_depreciation(
    asset_id: int,
    data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_ASSETS")),
):
    """
    Calculate and post monthly depreciation for an asset.
    Request body: { "month": int, "year": int }
    Posts a journal entry: Dr Depreciation Expense / Cr Accumulated Depreciation.
    """
    result = await db.execute(select(FixedAsset).where(FixedAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    if asset.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Asset is not active")

    month = data.get("month", datetime.now().month)
    year = data.get("year", datetime.now().year)

    # Ensure the fiscal period for the posting is open
    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, datetime(year, month, 1), None)

    # Check if depreciation already posted for this period
    existing = await db.execute(
        select(DepreciationEntry)
        .where(DepreciationEntry.asset_id == asset_id)
        .where(DepreciationEntry.period_month == month)
        .where(DepreciationEntry.period_year == year)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Depreciation already posted for this period")

    # Calculate depreciation
    depreciable_amount = asset.purchase_cost - asset.salvage_value
    monthly_depreciation = 0.0

    if asset.depreciation_method == "STRAIGHT_LINE":
        monthly_depreciation = depreciable_amount / asset.useful_life_months if asset.useful_life_months else 0
    elif asset.depreciation_method == "DECLINING_BALANCE":
        # Get category for rate
        cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == asset.category_id))
        category = cat_result.scalar_one_or_none()
        if category:
            annual_rate = category.depreciation_rate / 100
            monthly_rate = annual_rate / 12
            monthly_depreciation = asset.current_value * monthly_rate

    # Check if this would exceed depreciable amount
    remaining_depreciable = depreciable_amount - asset.accumulated_depreciation
    if monthly_depreciation > remaining_depreciable:
        monthly_depreciation = remaining_depreciable

    if monthly_depreciation <= 0:
        raise HTTPException(status_code=400, detail="Asset is fully depreciated")

    # Create depreciation entry
    new_accumulated = asset.accumulated_depreciation + monthly_depreciation
    new_book_value = asset.current_value - monthly_depreciation

    dep_entry = DepreciationEntry(
        asset_id=asset_id,
        asset_code=asset.code,
        asset_name=asset.name,
        period_month=month,
        period_year=year,
        depreciation_amount=round(monthly_depreciation, 4),
        accumulated_depreciation=round(new_accumulated, 4),
        book_value=round(new_book_value, 4),
        status="POSTED",
        company_id=asset.company_id,
        posted_by=current_user.id if hasattr(current_user, "id") else None,
        posted_at=datetime.now(),
        created_at=datetime.now(),
    )
    db.add(dep_entry)
    await db.flush()

    # Post GL entry: Dr Depreciation Expense / Cr Accumulated Depreciation
    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == asset.category_id))
    category = cat_result.scalar_one_or_none()

    expense_account_id = None
    accum_account_id = None
    if category:
        if category.depreciation_expense_account_id:
            expense_account_id = await _resolve_account_by_code(
                db, str(category.depreciation_expense_account_id),
                name=f"Depreciation Expense ({category.name})",
            )
        if category.accumulated_depreciation_account_id:
            accum_account_id = await _resolve_account_by_code(
                db, str(category.accumulated_depreciation_account_id),
                name=f"Accumulated Depreciation ({category.name})",
            )
    if not expense_account_id:
        expense_account_id = await _resolve_account_by_code(db, "5610", name="إهلاك مباني", account_type="expense")
    if not accum_account_id:
        accum_account_id = await _resolve_account_by_code(db, "1610", name="مجمع إهلاك المباني")

    entry = await _post_journal_entry(
        db,
        entry_number=await _generate_entry_number(db),
        entry_date=datetime(year, month, 1),
        description=f"Depreciation for asset {asset.code} - {asset.name} ({month}/{year})",
        lines=[
            {"account_id": expense_account_id.id, "debit": round(monthly_depreciation, 4),
             "description": f"Monthly depreciation for {asset.code}"},
            {"account_id": accum_account_id.id, "credit": round(monthly_depreciation, 4),
             "description": f"Accumulated depreciation for {asset.code}"},
        ],
        posted_by=current_user.id if hasattr(current_user, "id") else None,
        company_id=asset.company_id,
    )
    dep_entry.journal_entry_id = entry.id

    # Update asset
    asset.accumulated_depreciation = round(new_accumulated, 4)
    asset.current_value = round(new_book_value, 4)

    # Check if fully depreciated
    if abs(new_accumulated - depreciable_amount) < 0.01:
        asset.status = "FULLY_DEPRECIATED"

    await db.commit()
    await db.refresh(dep_entry)
    await add_audit_log(db, "DepreciationEntry", dep_entry.id, "CREATE", current_user,
                        {"asset_code": asset.code, "amount": dep_entry.depreciation_amount, "entry_id": entry.id})
    await db.commit()

    return {
        "id": dep_entry.id,
        "depreciation_amount": dep_entry.depreciation_amount,
        "accumulated_depreciation": dep_entry.accumulated_depreciation,
        "book_value": dep_entry.book_value,
        "journal_entry_id": entry.id,
        "message": "Depreciation calculated and posted",
    }


@router.post("/{asset_id}/dispose")
async def dispose_fixed_asset(
    asset_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("MANAGE_ASSETS")),
):
    """
    Dispose of a fixed asset and post the disposal journal entry.
    Request body: { "disposal_date": str, "disposal_amount": float, "reason": str }
    """
    result = await db.execute(select(FixedAsset).where(FixedAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    if asset.status == "DISPOSED":
        raise HTTPException(status_code=400, detail="Asset is already disposed")

    disposal_amount = data.get("disposal_amount", 0.0)
    disposal_date = data.get("disposal_date")
    reason = data.get("reason", "")

    disposal_datetime = None
    if isinstance(disposal_date, str):
        try:
            disposal_datetime = datetime.fromisoformat(disposal_date)
        except ValueError:
            disposal_datetime = datetime.strptime(disposal_date, "%Y-%m-%d")
    else:
        disposal_datetime = datetime.now()

    # Ensure the fiscal period for the posting is open
    from app.services.fiscal_period_guard import check_period_open
    await check_period_open(db, disposal_datetime, None)

    # Calculate gain/loss
    book_value = asset.current_value
    gain_loss = float(disposal_amount) - float(book_value)

    # Resolve accounts
    cat_result = await db.execute(select(AssetCategory).where(AssetCategory.id == asset.category_id))
    category = cat_result.scalar_one_or_none()

    asset_account = None
    accum_account = None
    if category:
        if category.gl_account_id:
            asset_account = await _resolve_account_by_code(db, str(category.gl_account_id), name=f"Fixed Assets ({category.name})")
        if category.accumulated_depreciation_account_id:
            accum_account = await _resolve_account_by_code(db, str(category.accumulated_depreciation_account_id), name=f"Accumulated Depreciation ({category.name})")
    if not asset_account:
        asset_account = await _resolve_account_by_code(db, "1530", name="آلات ومعدات")
    if not accum_account:
        accum_account = await _resolve_account_by_code(db, "1610", name="مجمع إهلاك المباني")

    bank_account = await _resolve_account_by_code(db, "1121", name="بنك الأهلي السعودي")
    gain_account = await _resolve_account_by_code(db, "4420", name="أرباح بيع أصول", account_type="revenue")
    loss_account = await _resolve_account_by_code(db, "5710", name="مصروفات مختلفة", account_type="expense")

    lines = [
        {"account_id": accum_account.id, "debit": float(asset.accumulated_depreciation or 0),
         "description": f"Remove accumulated depreciation on disposal of {asset.code}"},
        {"account_id": bank_account.id, "debit": float(disposal_amount),
         "description": f"Disposal proceeds for {asset.code}"},
        {"account_id": asset_account.id, "credit": float(asset.purchase_cost),
         "description": f"Remove asset cost on disposal of {asset.code}"},
    ]
    if abs(gain_loss) > 0.01:
        if gain_loss > 0:
            lines.append({"account_id": gain_account.id, "credit": round(gain_loss, 4),
                          "description": f"Gain on disposal of {asset.code}"})
        else:
            lines.append({"account_id": loss_account.id, "debit": round(abs(gain_loss), 4),
                          "description": f"Loss on disposal of {asset.code}"})

    entry = await _post_journal_entry(
        db,
        entry_number=await _generate_entry_number(db),
        entry_date=disposal_datetime,
        description=f"Disposal of fixed asset {asset.code} - {asset.name} ({reason})".strip(),
        lines=lines,
        posted_by=current_user.id if hasattr(current_user, "id") else None,
        company_id=asset.company_id,
    )

    asset.status = "DISPOSED"
    asset.disposal_date = disposal_datetime
    asset.disposal_amount = disposal_amount
    asset.journal_entry_id = entry.id
    asset.updated_at = datetime.now()

    await db.commit()
    await add_audit_log(db, "FixedAsset", asset.id, "DISPOSE", current_user,
                        {"asset_code": asset.code, "amount": disposal_amount,
                         "gain_loss": round(gain_loss, 4), "entry_id": entry.id})
    await db.commit()

    return {
        "asset_code": asset.code,
        "book_value_at_disposal": book_value,
        "disposal_amount": disposal_amount,
        "gain_or_loss": round(gain_loss, 4),
        "journal_entry_id": entry.id,
        "message": "Asset disposed",
    }
