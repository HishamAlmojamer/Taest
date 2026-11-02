import math
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func, or_
from app.database import get_db
from app.models.user import User
from app.models.core import Company, Branch, WorkflowRule
from app.models.numbering import DocumentNumbering
from app.models.rbac import Role, Permission, role_permissions
from app.schemas.auth import UserResponse
from app.schemas.rbac import RoleResponse, RoleCreate, RoleUpdate, PermissionResponse
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.security import hash_password, verify_password
from app.utils.deps import get_current_user, require_permission
from app.utils.validation import require_fields
from app.services.settings_service import list_settings, set_settings
from app.services.numbering_service import get_numbering, render_number, reset_counter

router = APIRouter()


async def _get_user_or_404(db: AsyncSession, user_id: int) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def _ensure_not_last_admin(db: AsyncSession, user: User) -> None:
    if user.role != "admin" or not user.is_active:
        return
    result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True, User.role == "admin")
    )
    active_admins = result.scalar() or 0
    if active_admins <= 1:
        raise HTTPException(status_code=400, detail="لا يمكن تعطيل آخر مدير نشط في النظام")


def _user_dict(u: User) -> dict:
    return {
        "id": u.id, "username": u.username, "full_name": u.full_name,
        "role": u.role, "role_id": u.role_id, "is_active": u.is_active, "email": u.email,
        "phone": u.phone,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


# ── General settings (key-value) ──────────────────────────────

@router.get("/general")
async def get_general_settings(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    items = await list_settings(db)
    return {"items": items, "total": len(items), "values": {i["key"]: i["value"] for i in items}}


@router.put("/general", response_model=dict)
async def update_general_settings(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    if not data:
        raise HTTPException(status_code=400, detail="No settings provided")
    count = await set_settings(db, data)
    return {"message": f"Settings updated ({count})"}


# ── Users ─────────────────────────────────────────────────────

@router.get("/users", response_model=PaginationResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", ge=1, le=100),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(User)
    count_query = select(func.count(User.id))
    if search:
        like = f"%{search}%"
        condition = or_(User.username.ilike(like), User.full_name.ilike(like), User.email.ilike(like))
        query = query.where(condition)
        count_query = count_query.where(condition)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(User.id).offset(offset).limit(page_size))
    users = result.scalars().all()
    return PaginationResponse(
        total=total, page=page, per_page=page_size,
        pages=math.ceil(total / page_size) if total else 0,
        items=[_user_dict(u) for u in users],
    )


@router.get("/users/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = await _get_user_or_404(db, user_id)
    return _user_dict(user)


@router.post("/users", response_model=dict)
async def create_user(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_USERS"))):
    existing = await db.execute(select(User).where(User.username == data.get("username", "")))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Username already exists")

    role_id = data.get("role_id")
    user = User(
        username=data.get("username", ""),
        password=hash_password(data.get("password", "password123")),
        full_name=data.get("full_name", ""),
        role=data.get("role", "user"),
        role_id=role_id,
        is_active=data.get("is_active", True),
        email=data.get("email"), phone=data.get("phone"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(user)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="بيانات المستخدم مكررة (اسم المستخدم)")
    return {"id": user.id, "message": "User created"}


@router.put("/users/{user_id}", response_model=dict)
async def update_user(user_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_USERS"))):
    user = await _get_user_or_404(db, user_id)
    values = {}
    for field in ["full_name", "role", "role_id", "email", "phone", "is_active"]:
        if field in data:
            values[field] = data[field]
    if "password" in data and data["password"]:
        values["password"] = hash_password(data["password"])
    if values:
        await db.execute(update(User).where(User.id == user_id).values(**values))
    return {"message": "User updated"}


@router.post("/users/{user_id}/deactivate", response_model=MessageResponse)
async def deactivate_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_USERS"))):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="لا يمكن تعطيل حسابك الحالي")
    user = await _get_user_or_404(db, user_id)
    await _ensure_not_last_admin(db, user)
    await db.execute(update(User).where(User.id == user_id).values(is_active=False))
    return MessageResponse(message="User deactivated")


@router.post("/users/{user_id}/activate", response_model=MessageResponse)
async def activate_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_USERS"))):
    await _get_user_or_404(db, user_id)
    await db.execute(update(User).where(User.id == user_id).values(is_active=True))
    return MessageResponse(message="User activated")


@router.delete("/users/{user_id}", response_model=MessageResponse)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_USERS"))):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = await _get_user_or_404(db, user_id)
    await _ensure_not_last_admin(db, user)
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
             "website": c.website, "logo": c.logo_path,
             "default_currency": c.default_currency, "fiscal_year_start": c.fiscal_year_start,
             "date_format": c.date_format}
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
            "address": company.address, "website": company.website,
            "logo": company.logo_path,
            "default_currency": company.default_currency,
            "fiscal_year_start": company.fiscal_year_start,
            "date_format": company.date_format}


@router.post("/companies", response_model=dict)
async def create_company(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    require_fields(data, ["code", "name"])
    company = Company(
        code=data["code"], name=data["name"],
        name_en=data.get("name_en"), tax_id=data.get("tax_id"),
        phone=data.get("phone"), email=data.get("email"), address=data.get("address"),
        website=data.get("website"), registration_no=data.get("registration_no"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
        is_active=True,
    )
    db.add(company)
    await db.flush()
    return {"id": company.id, "message": "Company created"}


@router.put("/companies/{company_id}", response_model=dict)
async def update_company(company_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Company).where(Company.id == company_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Company not found")
    allowed = ['code', 'name', 'name_en', 'tax_id', 'registration_no', 'phone', 'email', 'address', 'website',
               'logo_path', 'default_currency', 'fiscal_year_start', 'date_format']
    values = {}
    for k in allowed:
        if k in data:
            values[k] = data[k]
    if values:
        await db.execute(update(Company).where(Company.id == company_id).values(**values))
    return {"message": "Company updated"}


@router.put("/company", response_model=dict)
async def update_company_single(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Company).where(Company.is_active == True).order_by(Company.id).limit(1))
    company = result.scalar_one_or_none()
    if not company:
        company = Company(code="COMP-001", name=data.get("name", ""), created_at=datetime.now(UTC).replace(tzinfo=None), is_active=True)
        db.add(company)
        await db.flush()
        return {"message": "Company created"}
    allowed_map = {
        'name': 'name', 'name_ar': 'name_en', 'tax_number': 'tax_id',
        'commercial_register': 'registration_no', 'phone': 'phone',
        'email': 'email', 'address': 'address', 'website': 'website',
        'logo': 'logo_path', 'default_currency': 'default_currency',
        'fiscal_year_start': 'fiscal_year_start', 'date_format': 'date_format',
    }
    values = {}
    for frontend_key, db_key in allowed_map.items():
        if frontend_key in data:
            values[db_key] = data[frontend_key]
    if values:
        await db.execute(update(Company).where(Company.id == company.id).values(**values))
    return {"message": "Company updated"}


# ── Branches ──────────────────────────────────────────────────

def _branch_dict(b: Branch) -> dict:
    return {"id": b.id, "company_id": b.company_id, "code": b.code,
            "name": b.name, "name_en": b.name_en, "address": b.address,
            "phone": b.phone, "email": b.email, "manager": b.manager,
            "is_active": b.is_active}


@router.get("/branches")
async def list_branches(
    company_id: Optional[int] = None,
    include_inactive: bool = False,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(Branch)
    if not include_inactive:
        query = query.where(Branch.is_active == True)
    if company_id:
        query = query.where(Branch.company_id == company_id)
    query = query.order_by(Branch.name)
    result = await db.execute(query)
    items = [_branch_dict(b) for b in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/branches/{branch_id}")
async def get_branch(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    branch = result.scalar_one_or_none()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return _branch_dict(branch)


@router.post("/branches", response_model=dict)
async def create_branch(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    company_id = data.get("company_id")
    if company_id is None:
        result = await db.execute(select(Company).where(Company.is_active == True).order_by(Company.id).limit(1))
        company = result.scalar_one_or_none()
        if company:
            company_id = company.id
    branch = Branch(
        company_id=company_id, code=data.get("code"),
        name=data.get("name", ""), name_en=data.get("name_en"),
        address=data.get("address"), phone=data.get("phone"),
        email=data.get("email"), manager=data.get("manager"),
        is_active=data.get("is_active", True),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(branch)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="كود الفرع مستخدم مسبقاً لهذه الشركة")
    return {"id": branch.id, "message": "Branch created"}


@router.put("/branches/{branch_id}", response_model=dict)
async def update_branch(branch_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Branch not found")
    allowed = ['company_id', 'code', 'name', 'name_en', 'address', 'phone', 'email', 'manager', 'is_active']
    values = {k: data[k] for k in allowed if k in data}
    if values:
        await db.execute(update(Branch).where(Branch.id == branch_id).values(**values))
    return {"message": "Branch updated"}


@router.post("/branches/{branch_id}/restore", response_model=MessageResponse)
async def restore_branch(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Branch not found")
    await db.execute(update(Branch).where(Branch.id == branch_id).values(is_active=True))
    return MessageResponse(message="Branch restored")


@router.delete("/branches/{branch_id}", response_model=MessageResponse)
async def delete_branch(branch_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Branch).where(Branch.id == branch_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Branch not found")
    await db.execute(update(Branch).where(Branch.id == branch_id).values(is_active=False))
    return MessageResponse(message="Branch deleted")


# ── Workflow Rules ────────────────────────────────────────────

def _workflow_dict(w: WorkflowRule) -> dict:
    return {"id": str(w.id), "name": w.name, "nameAr": w.name_ar,
            "module": w.module, "action": w.action,
            "condition": w.condition, "approverRole": w.approver_role,
            "isActive": w.is_active, "createdAt": w.created_at}


@router.get("/workflow")
async def list_workflow_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, alias="pageSize", ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(WorkflowRule.id)))).scalar() or 0
    offset = (page - 1) * page_size
    result = await db.execute(select(WorkflowRule).order_by(WorkflowRule.id).offset(offset).limit(page_size))
    items = [_workflow_dict(w) for w in result.scalars().all()]
    return {"items": items, "total": total, "page": page, "per_page": page_size,
            "pages": math.ceil(total / page_size) if total else 0}


@router.post("/workflow", response_model=dict)
async def create_workflow_rule(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    rule = WorkflowRule(
        name=data.get("name", ""),
        name_ar=data.get("name_ar") or data.get("nameAr"),
        module=data.get("module", ""),
        action=data.get("action", ""),
        condition=data.get("condition"),
        approver_role=data.get("approver_role") or data.get("approverRole") or "",
        is_active=data.get("is_active", data.get("isActive", True)),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(rule)
    await db.flush()
    return {"id": rule.id, "message": "Workflow rule created"}


@router.put("/workflow/{rule_id}", response_model=dict)
async def update_workflow_rule(rule_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(WorkflowRule).where(WorkflowRule.id == rule_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    pairs = [
        ('name', 'name'), ('name_ar', 'nameAr'), ('module', 'module'), ('action', 'action'),
        ('condition', 'condition'), ('approver_role', 'approverRole'), ('is_active', 'isActive'),
    ]
    values = {}
    for snake, camel in pairs:
        if snake in data:
            values[snake] = data[snake]
        elif camel in data:
            values[snake] = data[camel]
    if values:
        await db.execute(update(WorkflowRule).where(WorkflowRule.id == rule_id).values(**values))
    return {"message": "Workflow rule updated"}


@router.post("/workflow/{rule_id}/activate", response_model=MessageResponse)
async def activate_workflow_rule(rule_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(WorkflowRule).where(WorkflowRule.id == rule_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    await db.execute(update(WorkflowRule).where(WorkflowRule.id == rule_id).values(is_active=True))
    return MessageResponse(message="Workflow rule activated")


@router.delete("/workflow/{rule_id}", response_model=MessageResponse)
async def delete_workflow_rule(rule_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(WorkflowRule).where(WorkflowRule.id == rule_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    await db.execute(update(WorkflowRule).where(WorkflowRule.id == rule_id).values(is_active=False))
    return MessageResponse(message="Workflow rule deleted")


# ── Document Numbering ────────────────────────────────────────

def _numbering_dict(n: DocumentNumbering) -> dict:
    return {
        "id": n.id, "docType": n.doc_type, "name": n.name, "nameAr": n.name_ar,
        "prefix": n.prefix, "suffix": n.suffix, "zeroPadding": n.zero_padding,
        "includeYear": n.include_year, "separator": n.separator, "period": n.period,
        "nextValue": n.next_value, "isActive": n.is_active,
        "preview": render_number(n),
    }


@router.get("/numbering")
async def list_numbering(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(DocumentNumbering).order_by(DocumentNumbering.doc_type))
    items = [_numbering_dict(n) for n in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.get("/numbering/{doc_type}/preview")
async def preview_numbering(doc_type: str, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    numbering = await get_numbering(db, doc_type)
    if not numbering:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return _numbering_dict(numbering)


@router.put("/numbering/{doc_type}", response_model=dict)
async def update_numbering(doc_type: str, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    numbering = await get_numbering(db, doc_type)
    if not numbering:
        raise HTTPException(status_code=404, detail="Sequence not found")
    allowed = ['prefix', 'suffix', 'zero_padding', 'include_year', 'separator', 'period', 'is_active']
    for field in allowed:
        if field in data:
            setattr(numbering, field, data[field])
    if 'next_value' in data:
        numbering.next_value = max(1, int(data['next_value']))
    numbering.updated_at = datetime.now(UTC).replace(tzinfo=None)
    await db.flush()
    return {"message": "Sequence updated", "preview": render_number(numbering)}


@router.post("/numbering/{doc_type}/reset", response_model=dict)
async def reset_document_numbering(doc_type: str, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    numbering = await reset_counter(db, doc_type, data.get("next_value", 1))
    if not numbering:
        raise HTTPException(status_code=404, detail="Sequence not found")
    return {"message": "Sequence reset", "preview": render_number(numbering)}


# ── Permissions ──────────────────────────────────────────────

@router.get("/permissions")
async def list_permissions(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Permission).order_by(Permission.module, Permission.code))
    permissions = result.scalars().all()
    return {"items": [PermissionResponse.model_validate(p) for p in permissions], "total": len(permissions)}


# ── Roles ────────────────────────────────────────────────────

@router.get("/roles")
async def list_roles(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    return {"items": [RoleResponse.model_validate(r) for r in roles], "total": len(roles)}


@router.get("/roles/{role_id}")
async def get_role(role_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    return RoleResponse.model_validate(role)


@router.post("/roles", response_model=dict)
async def create_role(data: RoleCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="اسم الدور مستخدم مسبقاً")

    role = Role(
        name=data.name,
        name_en=data.name_en,
        description=data.description,
        is_active=data.is_active,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(role)
    await db.flush()

    if data.permission_ids:
        perm_result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
        perms = perm_result.scalars().all()
        role.permissions = perms
        await db.flush()

    return {"id": role.id, "message": "Role created"}


@router.put("/roles/{role_id}", response_model=dict)
async def update_role(role_id: int, data: RoleUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check name uniqueness if changing
    if data.name and data.name != role.name:
        existing = await db.execute(select(Role).where(Role.name == data.name, Role.id != role_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="اسم الدور مستخدم مسبقاً")

    values = {}
    for field in ["name", "name_en", "description", "is_active"]:
        val = getattr(data, field, None)
        if val is not None:
            values[field] = val
    if values:
        await db.execute(update(Role).where(Role.id == role_id).values(**values))

    if data.permission_ids is not None:
        perm_result = await db.execute(select(Permission).where(Permission.id.in_(data.permission_ids)))
        perms = perm_result.scalars().all()
        role.permissions = perms
        await db.flush()

    return {"message": "Role updated"}


@router.delete("/roles/{role_id}", response_model=MessageResponse)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_SETTINGS"))):
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")

    # Check if any users are assigned to this role
    users_result = await db.execute(select(func.count(User.id)).where(User.role_id == role_id, User.is_active == True))
    count = users_result.scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail=f"لا يمكن حذف الدور: يوجد {count} مستخدمين مرتبطين به")

    # Clear permissions then delete
    role.permissions = []
    await db.flush()
    await db.delete(role)
    return MessageResponse(message="Role deleted")
