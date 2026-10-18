from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from app.database import get_db
from app.models.user import User
from app.models.core import Company, Branch, WorkflowRule
from app.schemas.auth import UserResponse
from app.schemas.common import MessageResponse
from app.utils.security import hash_password, verify_password
from app.utils.deps import get_current_user

router = APIRouter()


# ── Users ─────────────────────────────────────────────────────

@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).order_by(User.id))
    items = [{"id": u.id, "username": u.username, "full_name": u.full_name,
             "role": u.role, "is_active": u.is_active, "email": u.email,
             "phone": u.phone, "last_login_at": str(u.last_login_at) if u.last_login_at else None,
             "created_at": str(u.created_at) if u.created_at else None}
            for u in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/users", response_model=dict)
async def create_user(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    existing = await db.execute(select(User).where(User.username == data.get("username", "")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=data.get("username", ""),
        password=hash_password(data.get("password", "password123")),
        full_name=data.get("full_name", ""),
        role=data.get("role", "user"),
        email=data.get("email"), phone=data.get("phone"),
        created_at=datetime.utcnow(),
    )
    db.add(user)
    await db.flush()
    return {"id": user.id, "message": "User created"}


@router.put("/users/{user_id}", response_model=dict)
async def update_user(user_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(User).where(User.id == user_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="User not found")
    values = {}
    for field in ["full_name", "role", "email", "phone", "is_active"]:
        if field in data:
            values[field] = data[field]
    if "password" in data and data["password"]:
        values["password"] = hash_password(data["password"])
    if values:
        await db.execute(update(User).where(User.id == user_id).values(**values))
    return {"message": "User updated"}


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    await db.execute(update(User).where(User.id == user_id).values(is_active=False))
    return MessageResponse(message="User deactivated")


# ── Companies ─────────────────────────────────────────────────

@router.get("/companies")
async def list_companies(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Company).where(Company.is_active == True).order_by(Company.name))
    items = [{"id": c.id, "code": c.code, "name": c.name, "name_en": c.name_en,
             "nameAr": c.name_en, "taxNumber": c.tax_id, "tax_id": c.tax_id,
             "commercialRegister": c.registration_no, "registration_no": c.registration_no,
             "phone": c.phone, "email": c.email, "address": c.address,
             "website": c.website, "logo": c.logo_path}
            for c in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/company")
async def get_company(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Company).where(Company.is_active == True).order_by(Company.id).limit(1))
    company = result.scalar_one_or_none()
    if not company:
        return {"id": None}
    return {"id": company.id, "code": company.code, "name": company.name,
            "nameAr": company.name_en, "taxNumber": company.tax_id,
            "commercialRegister": company.registration_no,
            "phone": company.phone, "email": company.email,
            "address": company.address, "website": company.website}


@router.post("/companies", response_model=dict)
async def create_company(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    company = Company(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), tax_id=data.get("tax_id"),
        phone=data.get("phone"), email=data.get("email"), address=data.get("address"),
        website=data.get("website"), registration_no=data.get("registration_no"),
        created_at=datetime.utcnow(),
    )
    db.add(company)
    await db.flush()
    return {"id": company.id, "message": "Company created"}


@router.put("/companies/{company_id}", response_model=dict)
async def update_company(company_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Company).where(Company.id == company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")
    allowed = ['code', 'name', 'name_en', 'tax_id', 'registration_no', 'phone', 'email', 'address', 'website']
    values = {}
    for k in allowed:
        if k in data:
            values[k] = data[k]
    if values:
        await db.execute(update(Company).where(Company.id == company_id).values(**values))
    return {"message": "Company updated"}


@router.put("/company", response_model=dict)
async def update_company_single(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Company).where(Company.is_active == True).order_by(Company.id).limit(1))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(code="COMP-001", name=data.get("name", ""), created_at=datetime.utcnow())
        db.add(company)
        await db.flush()
        return {"message": "Company created"}
    allowed_map = {
        'name': 'name', 'nameAr': 'name_en', 'taxNumber': 'tax_id',
        'commercialRegister': 'registration_no', 'phone': 'phone',
        'email': 'email', 'address': 'address', 'website': 'website',
    }
    values = {}
    for frontend_key, db_key in allowed_map.items():
        if frontend_key in data:
            values[db_key] = data[frontend_key]
    if values:
        await db.execute(update(Company).where(Company.id == company.id).values(**values))
    return {"message": "Company updated"}


# ── Branches ──────────────────────────────────────────────────

@router.get("/branches")
async def list_branches(company_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(Branch).where(Branch.is_active == True)
    if company_id:
        query = query.where(Branch.company_id == company_id)
    query = query.order_by(Branch.name)
    result = await db.execute(query)
    items = [{"id": b.id, "company_id": b.company_id, "code": b.code,
             "name": b.name, "name_en": b.name_en, "address": b.address, "phone": b.phone}
            for b in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/branches", response_model=dict)
async def create_branch(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    branch = Branch(
        company_id=data.get("company_id"), code=data.get("code"),
        name=data.get("name", ""), name_en=data.get("name_en"),
        address=data.get("address"), phone=data.get("phone"),
        created_at=datetime.utcnow(),
    )
    db.add(branch)
    await db.flush()
    return {"id": branch.id, "message": "Branch created"}


@router.put("/branches/{branch_id}", response_model=dict)
async def update_branch(branch_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Branch not found")
    allowed = ['company_id', 'code', 'name', 'name_en', 'address', 'phone']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Branch).where(Branch.id == branch_id).values(**values))
    return {"message": "Branch updated"}


@router.delete("/branches/{branch_id}", response_model=MessageResponse)
async def delete_branch(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(update(Branch).where(Branch.id == branch_id).values(is_active=False))
    return MessageResponse(message="Branch deleted")


# ── Workflow Rules ────────────────────────────────────────────

@router.get("/workflow")
async def list_workflow_rules(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(WorkflowRule).where(WorkflowRule.is_active == True).order_by(WorkflowRule.id))
    items = [{"id": str(w.id), "name": w.name, "nameAr": w.name_ar,
             "module": w.module, "action": w.action,
             "condition": w.condition, "approverRole": w.approver_role,
             "isActive": w.is_active, "createdAt": w.created_at}
            for w in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/workflow", response_model=dict)
async def create_workflow_rule(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    rule = WorkflowRule(
        name=data.get("name", ""),
        name_ar=data.get("nameAr"),
        module=data.get("module", ""),
        action=data.get("action", ""),
        condition=data.get("condition"),
        approver_role=data.get("approverRole", ""),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    db.add(rule)
    await db.flush()
    return {"id": rule.id, "message": "Workflow rule created"}
