"""
Fixed Assets management endpoints with depreciation calculation.
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.fixed_assets import AssetCategory, FixedAsset, DepreciationEntry
from app.utils.deps import get_current_active_user

router = APIRouter()


# =============================================================================
# Asset Category Endpoints
# =============================================================================

@router.get("/categories")
async def list_asset_categories(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """List all asset categories"""
    result = await db.execute(select(AssetCategory).order_by(AssetCategory.code))
    categories = result.scalars().all()
    return [{"id": c.id, "code": c.code, "name": c.name, "name_ar": c.name_ar,
             "depreciation_rate": c.depreciation_rate, "depreciation_method": c.depreciation_method,
             "useful_life_months": c.useful_life_months, "is_active": c.is_active} for c in categories]


@router.post("/categories")
async def create_asset_category(
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new asset category"""
    existing = await db.execute(select(AssetCategory).where(AssetCategory.code == data.get("code")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Category code already exists")

    category = AssetCategory(
        code=data["code"],
        name=data["name"],
        name_ar=data.get("name_ar"),
        depreciation_rate=data.get("depreciation_rate", 0.0),
        depreciation_method=data.get("depreciation_method", "STRAIGHT_LINE"),
        useful_life_months=data.get("useful_life_months"),
        gl_account_id=data.get("gl_account_id"),
        depreciation_expense_account_id=data.get("depreciation_expense_account_id"),
        accumulated_depreciation_account_id=data.get("accumulated_depreciation_account_id"),
        description=data.get("description"),
        created_at=datetime.now(),
    )
    db.add(category)
    await db.commit()
    await db.refresh(category)
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
    current_user=Depends(get_current_active_user),
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
    current_user=Depends(get_current_active_user),
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


@router.get("/{asset_id}")
async def get_fixed_asset(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """Create a new fixed asset"""
    existing = await db.execute(select(FixedAsset).where(FixedAsset.code == data.get("code")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Asset code already exists")

    asset = FixedAsset(
        code=data["code"],
        name=data["name"],
        name_ar=data.get("name_ar"),
        category_id=data["category_id"],
        description=data.get("description"),
        purchase_date=datetime.fromisoformat(data["purchase_date"]) if isinstance(data.get("purchase_date"), str) else data.get("purchase_date"),
        purchase_cost=data["purchase_cost"],
        salvage_value=data.get("salvage_value", 0.0),
        useful_life_months=data["useful_life_months"],
        depreciation_method=data.get("depreciation_method", "STRAIGHT_LINE"),
        accumulated_depreciation=0.0,
        current_value=data["purchase_cost"],
        status="ACTIVE",
        location=data.get("location"),
        serial_number=data.get("serial_number"),
        supplier_name=data.get("supplier_name"),
        invoice_number=data.get("invoice_number"),
        company_id=data.get("company_id"),
        branch_id=data.get("branch_id"),
        created_at=datetime.now(),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return {"id": asset.id, "code": asset.code, "message": "Fixed asset created"}


@router.put("/{asset_id}")
async def update_fixed_asset(
    asset_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
    return {"success": True, "message": "Fixed asset updated"}


@router.post("/{asset_id}/depreciate")
async def calculate_monthly_depreciation(
    asset_id: int,
    data: dict = {},
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Calculate and post monthly depreciation for an asset.
    Request body: { "month": int, "year": int }
    """
    result = await db.execute(select(FixedAsset).where(FixedAsset.id == asset_id))
    asset = result.scalar_one_or_none()
    if not asset:
        raise HTTPException(status_code=404, detail="Fixed asset not found")
    if asset.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="Asset is not active")

    month = data.get("month", datetime.now().month)
    year = data.get("year", datetime.now().year)

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
        monthly_depreciation = depreciable_amount / asset.useful_life_months
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
        status="DRAFT",
        company_id=asset.company_id,
        created_at=datetime.now(),
    )
    db.add(dep_entry)

    # Update asset
    asset.accumulated_depreciation = round(new_accumulated, 4)
    asset.current_value = round(new_book_value, 4)

    # Check if fully depreciated
    if abs(new_accumulated - depreciable_amount) < 0.01:
        asset.status = "FULLY_DEPRECIATED"

    await db.commit()
    await db.refresh(dep_entry)

    return {
        "id": dep_entry.id,
        "depreciation_amount": dep_entry.depreciation_amount,
        "accumulated_depreciation": dep_entry.accumulated_depreciation,
        "book_value": dep_entry.book_value,
        "message": "Depreciation calculated",
    }


@router.post("/{asset_id}/dispose")
async def dispose_fixed_asset(
    asset_id: int,
    data: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
):
    """
    Dispose of a fixed asset.
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

    # Calculate gain/loss
    gain_loss = disposal_amount - asset.current_value

    asset.status = "DISPOSED"
    asset.disposal_date = datetime.fromisoformat(disposal_date) if isinstance(disposal_date, str) else datetime.now()
    asset.disposal_amount = disposal_amount
    asset.updated_at = datetime.now()

    await db.commit()

    return {
        "asset_code": asset.code,
        "book_value_at_disposal": asset.current_value,
        "disposal_amount": disposal_amount,
        "gain_or_loss": round(gain_loss, 4),
        "message": "Asset disposed",
    }


@router.get("/depreciation-schedule/{asset_id}")
async def get_depreciation_schedule(
    asset_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_user),
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
