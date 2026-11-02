import math
import logging
from datetime import UTC, datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.hr import (
    HREmployee, HRDepartment, HRPosition,
    HRAttendance, HRLeave, HRPayroll, HRAdvance,
    HRShift, HRLeaveType, HRLeaveBalance,
    HROvertime, HRBonus, HRPerformanceReview, HRContract,
    HRResignation, HRJobPosting, HRCandidate, HRTraining,
    HREmployeeDocument, HRHoliday,
)
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user, require_permission
from app.utils.event_emitter import (
    emit_payroll_approved,
    emit_payroll_settled,
    emit_payroll_voided,
    emit_advance_granted,
    emit_advance_voided,
)
from app.utils.validation import require_fields

logger = logging.getLogger(__name__)

router = APIRouter()


def _require_update_fields(data: dict, fields: tuple[str, ...]) -> None:
    """Validate only the mandatory fields actually sent, but reject an empty body."""
    if not isinstance(data, dict) or not data:
        raise HTTPException(status_code=422, detail="No fields to update")
    require_fields(data, [name for name in fields if name in data])


def _extract_entry_id_from_event(event_result) -> Optional[int]:
    """Extract the first journal entry id from a gateway emit response.

    Used to persist journal_entry_id on the operational row inside the same
    transaction (replacing the old cross-connection UPDATE that caused
    PostgreSQL deadlocks when the operational row was mid-transaction).
    """
    try:
        results = (event_result.get("data") or {}).get("results") or []
        for r in results:
            if isinstance(r, dict) and r.get("entryId"):
                return int(r["entryId"])
    except Exception:
        pass
    return None


async def _get_active_advance_deduction(db: AsyncSession, employee_id: int, period_from: Optional[str] = None) -> float:
    """Sum the monthly installment of active (approved) employee advances.

    These installments are deducted from the employee's net salary each payroll period.
    """
    result = await db.execute(
        select(HRAdvance).where(
            HRAdvance.employee_id == employee_id,
            HRAdvance.status == "approved",
            HRAdvance.monthly_deduction.isnot(None),
            HRAdvance.monthly_deduction > 0,
        )
    )
    advances = result.scalars().all()
    return float(sum(a.monthly_deduction or 0 for a in advances))


def _parse_period(period_from: Optional[str]) -> tuple[int, int]:
    try:
        d = datetime.strptime(period_from, "%Y-%m-%d") if period_from else datetime.now()
        return d.month, d.year
    except (ValueError, TypeError):
        return datetime.now().month, datetime.now().year


async def _emp_names(db: AsyncSession, ids) -> dict[int, str]:
    """Map employee ids to full names for list endpoints."""
    ids = list(ids)
    if not ids:
        return {}
    result = await db.execute(select(HREmployee.id, HREmployee.full_name).where(HREmployee.id.in_(ids)))
    return {row.id: row.full_name for row in result.all()}


async def _sync_leave_balance(db: AsyncSession, employee_id: int, leave_type_code: str, days: float, year: int) -> None:
    """Ensure a leave balance row exists for (employee, type, year) and bump days_used.

    Called when a leave request is approved so balances stay in sync.
    """
    type_result = await db.execute(select(HRLeaveType).where(HRLeaveType.code == leave_type_code))
    leave_type = type_result.scalar_one_or_none()

    balance_result = await db.execute(
        select(HRLeaveBalance).where(
            HRLeaveBalance.employee_id == employee_id,
            HRLeaveBalance.leave_type_id == (leave_type.id if leave_type else 0),
            HRLeaveBalance.year == year,
        )
    )
    balance = balance_result.scalar_one_or_none()
    if not balance:
        balance = HRLeaveBalance(
            employee_id=employee_id,
            leave_type_id=leave_type.id if leave_type else 0,
            year=year,
            days_entitled=float(leave_type.days_per_year or 0) if leave_type else 0,
            days_used=0,
            days_remaining=0,
            created_at=datetime.now(UTC).replace(tzinfo=None),
        )
        db.add(balance)
        await db.flush()

    days_used = float(balance.days_used or 0) + days
    entitled = float(balance.days_entitled or 0)
    await db.execute(update(HRLeaveBalance).where(HRLeaveBalance.id == balance.id).values(
        days_used=days_used,
        days_remaining=max(entitled - days_used, 0),
    ))


async def _period_extra_items(db: AsyncSession, employee_id: int, period_from: str, period_to: str) -> tuple[float, float, float]:
    """Sum approved overtime, bonuses and deductions that fall inside a payroll period.

    Returns (overtime_total, bonus_total, deduction_total).
    """
    ot_total = 0.0
    bonus_total = 0.0
    deduction_total = 0.0

    ot_result = await db.execute(
        select(HROvertime).where(
            HROvertime.employee_id == employee_id,
            HROvertime.status == "approved",
            HROvertime.date.isnot(None),
            HROvertime.date >= period_from,
            HROvertime.date <= period_to,
        )
    )
    for o in ot_result.scalars().all():
        ot_total += float(o.amount or 0)

    period_label = ""
    try:
        d = datetime.strptime(period_from, "%Y-%m-%d") if period_from else None
        if d:
            period_label = f"{d.year:04d}-{d.month:02d}"
    except (ValueError, TypeError):
        pass

    b_result = await db.execute(
        select(HRBonus).where(HRBonus.employee_id == employee_id, HRBonus.status == "approved")
    )
    for b in b_result.scalars().all():
        p = (b.period or "").strip()
        if p and period_label and not p.startswith(period_label):
            continue
        if b.bonus_type == "deduction":
            deduction_total += float(b.amount or 0)
        else:
            bonus_total += float(b.amount or 0)

    return ot_total, bonus_total, deduction_total



@router.get("/departments/tree")
async def get_department_tree(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    dept_result = await db.execute(
        select(HRDepartment).where(HRDepartment.is_active == True).order_by(HRDepartment.name)
    )
    all_depts = dept_result.scalars().all()

    emp_result = await db.execute(
        select(HREmployee.department_id, func.count(HREmployee.id).label("cnt"))
        .where(HREmployee.is_active == True)
        .group_by(HREmployee.department_id)
    )
    emp_counts = {row.department_id: row.cnt for row in emp_result.all()}

    manager_ids = list({d.manager_id for d in all_depts if d.manager_id})
    manager_map = {}
    if manager_ids:
        mgr_result = await db.execute(
            select(HREmployee.id, HREmployee.full_name).where(HREmployee.id.in_(manager_ids))
        )
        for row in mgr_result.all():
            manager_map[row.id] = row.full_name

    dept_map = {}
    for d in all_depts:
        dept_map[d.id] = {
            "id": d.id,
            "code": d.code,
            "name": d.name,
            "name_en": d.name_en,
            "description": d.description,
            "manager_id": d.manager_id,
            "managerName": manager_map.get(d.manager_id),
            "parent_id": d.parent_id,
            "employeeCount": emp_counts.get(d.id, 0),
            "children": [],
        }

    roots = []
    for d in all_depts:
        node = dept_map[d.id]
        if d.parent_id and d.parent_id in dept_map:
            dept_map[d.parent_id]["children"].append(node)
        else:
            roots.append(node)

    return {"items": roots, "total": len(all_depts)}


@router.get("/departments")
async def list_departments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRDepartment).where(HRDepartment.is_active == True).order_by(HRDepartment.name))
    items = [{"id": d.id, "code": d.code, "name": d.name, "name_en": d.name_en,
             "description": d.description, "manager_id": d.manager_id, "managerName": None,
             "parent_id": d.parent_id, "employeeCount": 0}
            for d in result.scalars().all()]
    return {"items": items, "total": len(items)}


# ── Validation: required fields mirror the NOT NULL columns of the HR models ──

@router.post("/departments", response_model=dict)
async def create_department(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["code", "name"])
    dept = HRDepartment(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), description=data.get("description"),
        manager_id=data.get("manager_id"), parent_id=data.get("parent_id"),
        is_active=True, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(dept)
    await db.flush()
    return {"id": dept.id, "message": "Department created"}


@router.put("/departments/{dept_id}", response_model=dict)
async def update_department(dept_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("code", "name"))
    result = await db.execute(select(HRDepartment).where(HRDepartment.id == dept_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Department not found")
    await db.execute(update(HRDepartment).where(HRDepartment.id == dept_id).values(**{
        k: data[k] for k in
        ("code", "name", "name_en", "description", "manager_id", "parent_id") if k in data
    }))
    return {"message": "Department updated"}


@router.delete("/departments/{dept_id}", response_model=MessageResponse)
async def delete_department(dept_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(update(HRDepartment).where(HRDepartment.id == dept_id).values(is_active=False))
    return MessageResponse(message="Department deleted")


# ── Positions ─────────────────────────────────────────────────

@router.get("/positions")
async def list_positions(department_id: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(HRPosition).where(HRPosition.is_active == True)
    if department_id:
        query = query.where(HRPosition.department_id == department_id)
    query = query.order_by(HRPosition.name)
    result = await db.execute(query)
    items = [{"id": p.id, "code": p.code, "name": p.name, "name_en": p.name_en,
             "department_id": p.department_id, "description": p.description,
             "min_salary": p.min_salary, "max_salary": p.max_salary}
            for p in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/positions", response_model=dict)
async def create_position(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["code", "name"])
    pos = HRPosition(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), department_id=data.get("department_id"),
        description=data.get("description"), min_salary=data.get("min_salary", 0),
        max_salary=data.get("max_salary", 0), is_active=True, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(pos)
    await db.flush()
    return {"id": pos.id, "message": "Position created"}


@router.put("/positions/{pos_id}", response_model=dict)
async def update_position(pos_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("code", "name"))
    result = await db.execute(select(HRPosition).where(HRPosition.id == pos_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Position not found")
    await db.execute(update(HRPosition).where(HRPosition.id == pos_id).values(**{
        k: data[k] for k in
        ("code", "name", "name_en", "department_id", "description", "min_salary", "max_salary")
        if k in data
    }))
    return {"message": "Position updated"}


@router.delete("/positions/{pos_id}", response_model=MessageResponse)
async def delete_position(pos_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(update(HRPosition).where(HRPosition.id == pos_id).values(is_active=False))
    return MessageResponse(message="Position deleted")


# ── Employees ─────────────────────────────────────────────────

@router.get("/employees", response_model=PaginationResponse)
async def list_employees(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    page_size: Optional[int] = Query(None, ge=1, le=100),
    search: Optional[str] = None,
    department_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if page_size:
        per_page = page_size
    query = select(HREmployee).where(HREmployee.is_active == True)
    count_query = select(func.count(HREmployee.id)).where(HREmployee.is_active == True)
    if search:
        q = HREmployee.full_name.ilike(f"%{search}%") | HREmployee.code.ilike(f"%{search}%")
        query = query.where(q)
        count_query = count_query.where(q)
    if department_id:
        query = query.where(HREmployee.department_id == department_id)
        count_query = count_query.where(HREmployee.department_id == department_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HREmployee.full_name).offset(offset).limit(per_page)
    result = await db.execute(query)
    employees = result.scalars().all()

    return PaginationResponse(
        total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        items=[{
            "id": e.id, "code": e.code, "full_name": e.full_name, "full_name_en": e.full_name_en,
            "email": e.email, "phone": e.phone, "mobile": e.mobile, "gender": e.gender,
            "department_id": e.department_id, "position_id": e.position_id,
            "hire_date": e.hire_date, "employment_status": e.employment_status,
            "total_salary": e.total_salary,
        } for e in employees],
    )


@router.get("/employees/{emp_id}")
async def get_employee(emp_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HREmployee).where(HREmployee.id == emp_id))
    emp = result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return {
        "id": emp.id, "code": emp.code, "full_name": emp.full_name,
        "full_name_en": emp.full_name_en, "email": emp.email,
        "phone": emp.phone, "mobile": emp.mobile, "address": emp.address,
        "gender": emp.gender, "birth_date": emp.birth_date,
        "nationality": emp.nationality, "marital_status": emp.marital_status,
        "department_id": emp.department_id, "position_id": emp.position_id,
        "manager_id": emp.manager_id, "hire_date": emp.hire_date,
        "employment_status": emp.employment_status, "salary_type": emp.salary_type,
        "basic_salary": emp.basic_salary, "housing_allowance": emp.housing_allowance,
        "transportation_allowance": emp.transportation_allowance,
        "other_allowances": emp.other_allowances, "total_salary": emp.total_salary,
        "bank_name": emp.bank_name, "bank_account": emp.bank_account, "iban": emp.iban,
        "id_type": emp.id_type, "id_number": emp.id_number, "id_expiry": emp.id_expiry,
        "passport_number": emp.passport_number, "passport_expiry": emp.passport_expiry,
        "emergency_contact_name": emp.emergency_contact_name,
        "emergency_contact_phone": emp.emergency_contact_phone,
        "health_insurance_provider": emp.health_insurance_provider,
        "health_insurance_number": emp.health_insurance_number,
        "notes": emp.notes, "is_active": emp.is_active,
    }


@router.post("/employees", response_model=dict)
async def create_employee(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["code", "full_name"])
    emp = HREmployee(
        code=data.get("code"), full_name=data.get("full_name", ""),
        full_name_en=data.get("full_name_en"), email=data.get("email"),
        phone=data.get("phone"), mobile=data.get("mobile"), address=data.get("address"),
        gender=data.get("gender", "ذكر"), birth_date=data.get("birth_date"),
        nationality=data.get("nationality"), marital_status=data.get("marital_status", "أعزب"),
        department_id=data.get("department_id"), position_id=data.get("position_id"),
        manager_id=data.get("manager_id"), hire_date=data.get("hire_date"),
        employment_status=data.get("employment_status", "نشط"),
        salary_type=data.get("salary_type", "شهري"),
        basic_salary=float(data.get("basic_salary", 0)),
        housing_allowance=float(data.get("housing_allowance", 0)),
        transportation_allowance=float(data.get("transportation_allowance", 0)),
        other_allowances=float(data.get("other_allowances", 0)),
        total_salary=float(data.get("total_salary", 0)),
        bank_name=data.get("bank_name"), bank_account=data.get("bank_account"),
        iban=data.get("iban"), id_type=data.get("id_type", "هوية وطنية"),
        id_number=data.get("id_number"), id_expiry=data.get("id_expiry"),
        passport_number=data.get("passport_number"), passport_expiry=data.get("passport_expiry"),
        emergency_contact_name=data.get("emergency_contact_name"),
        emergency_contact_phone=data.get("emergency_contact_phone"),
        health_insurance_provider=data.get("health_insurance_provider"),
        health_insurance_number=data.get("health_insurance_number"),
        notes=data.get("notes"), is_active=True, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(emp)
    await db.flush()
    return {"id": emp.id, "message": "Employee created"}


@router.put("/employees/{emp_id}", response_model=dict)
async def update_employee(emp_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("full_name",))
    result = await db.execute(select(HREmployee).where(HREmployee.id == emp_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")
    allowed_fields = [
        'full_name', 'full_name_en', 'email', 'phone', 'mobile', 'address',
        'gender', 'birth_date', 'nationality', 'marital_status',
        'department_id', 'position_id', 'manager_id', 'hire_date',
        'employment_status', 'salary_type', 'basic_salary', 'housing_allowance',
        'transportation_allowance', 'other_allowances', 'total_salary',
        'bank_name', 'bank_account', 'iban', 'id_type', 'id_number', 'id_expiry',
        'passport_number', 'passport_expiry', 'emergency_contact_name',
        'emergency_contact_phone', 'health_insurance_provider',
        'health_insurance_number', 'notes',
    ]
    values = {}
    for f in allowed_fields:
        if f in data:
            values[f] = data[f]
    if values:
        await db.execute(update(HREmployee).where(HREmployee.id == emp_id).values(**values))
    return {"message": "Employee updated"}


@router.delete("/employees/{emp_id}", response_model=MessageResponse)
async def delete_employee(emp_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(update(HREmployee).where(HREmployee.id == emp_id).values(is_active=False))
    return MessageResponse(message="Employee deleted")


# ── Attendance ────────────────────────────────────────────────

@router.get("/attendance", response_model=PaginationResponse)
async def list_attendance(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRAttendance)
    count_query = select(func.count(HRAttendance.id))
    if employee_id:
        query = query.where(HRAttendance.employee_id == employee_id)
        count_query = count_query.where(HRAttendance.employee_id == employee_id)
    if date:
        query = query.where(HRAttendance.date == date)
        count_query = count_query.where(HRAttendance.date == date)
    if from_date:
        query = query.where(HRAttendance.date >= from_date)
        count_query = count_query.where(HRAttendance.date >= from_date)
    if to_date:
        query = query.where(HRAttendance.date <= to_date)
        count_query = count_query.where(HRAttendance.date <= to_date)
    if status:
        query = query.where(HRAttendance.status == status)
        count_query = count_query.where(HRAttendance.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRAttendance.date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    attendance_records = result.scalars().all()

    emp_ids = list({a.employee_id for a in attendance_records})
    emp_map = {}
    if emp_ids:
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id.in_(emp_ids)))
        for e in emp_result.scalars().all():
            emp_map[e.id] = e.full_name

    items = [{"id": a.id, "employee_id": a.employee_id, "employeeName": emp_map.get(a.employee_id, f"موظف #{a.employee_id}"),
             "date": a.date, "check_in": a.check_in, "check_out": a.check_out,
             "status": a.status, "notes": a.notes}
            for a in attendance_records]

    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/attendance", response_model=dict)
async def create_attendance(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id", "date"])
    att = HRAttendance(
        employee_id=data.get("employee_id"), date=data.get("date", ""),
        check_in=data.get("check_in"), check_out=data.get("check_out"),
        status=data.get("status", "present"), notes=data.get("notes"),
    )
    db.add(att)
    await db.flush()
    return {"id": att.id, "message": "Attendance recorded"}


@router.put("/attendance/{att_id}", response_model=dict)
async def update_attendance(att_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("date",))
    result = await db.execute(select(HRAttendance).where(HRAttendance.id == att_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Attendance record not found")
    values = {k: data[k] for k in ("check_in", "check_out", "status", "notes", "date") if k in data}
    if values:
        await db.execute(update(HRAttendance).where(HRAttendance.id == att_id).values(**values))
    return {"message": "Attendance updated"}


@router.delete("/attendance/{att_id}", response_model=MessageResponse)
async def delete_attendance(att_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRAttendance).where(HRAttendance.id == att_id))
    return MessageResponse(message="Attendance deleted")


# ── Leaves ────────────────────────────────────────────────────

@router.get("/leaves", response_model=PaginationResponse)
async def list_leaves(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRLeave)
    count_query = select(func.count(HRLeave.id))
    if employee_id:
        query = query.where(HRLeave.employee_id == employee_id)
        count_query = count_query.where(HRLeave.employee_id == employee_id)
    if status:
        query = query.where(HRLeave.status == status)
        count_query = count_query.where(HRLeave.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRLeave.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    leaves = result.scalars().all()
    items = [{"id": l.id, "employeeId": l.employee_id, "leaveType": l.leave_type,
             "startDate": l.start_date, "endDate": l.end_date,
             "daysCount": l.days_count, "reason": l.reason,
             "status": l.status, "approvedBy": l.approved_by}
            for l in leaves]

    emp_ids = list({l.employee_id for l in leaves})
    emp_map = {}
    if emp_ids:
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id.in_(emp_ids)))
        for e in emp_result.scalars().all():
            emp_map[e.id] = e.full_name
    for item in items:
        item["employeeName"] = emp_map.get(item["employeeId"], f"موظف #{item['employeeId']}")

    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/leaves", response_model=dict)
async def create_leave(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id", "leave_type", "start_date", "end_date", "days_count"])
    leave = HRLeave(
        employee_id=data.get("employee_id"), leave_type=data.get("leave_type", ""),
        start_date=data.get("start_date", ""), end_date=data.get("end_date", ""),
        days_count=data.get("days_count", 0), reason=data.get("reason"),
        status=data.get("status", "pending"),
    )
    db.add(leave)
    await db.flush()
    return {"id": leave.id, "message": "Leave request created"}


@router.put("/leaves/{leave_id}/status", response_model=MessageResponse)
async def update_leave_status(leave_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRLeave).where(HRLeave.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    new_status = data.get("status", "pending")
    await db.execute(update(HRLeave).where(HRLeave.id == leave_id).values(
        status=new_status, approved_by=current_user.id,
    ))
    # Keep the employee's annual leave balance in sync when approved
    if new_status == "approved" and leave.start_date:
        try:
            year = int(leave.start_date[:4])
            await _sync_leave_balance(db, leave.employee_id, leave.leave_type, float(leave.days_count or 0), year)
        except (ValueError, TypeError):
            pass
    return MessageResponse(message="Leave status updated")


@router.delete("/leaves/{leave_id}", response_model=MessageResponse)
async def delete_leave(leave_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRLeave).where(HRLeave.id == leave_id))
    return MessageResponse(message="Leave deleted")


# ── Payroll ───────────────────────────────────────────────────

@router.get("/payroll", response_model=PaginationResponse)
async def list_payroll(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRPayroll)
    count_query = select(func.count(HRPayroll.id))
    if employee_id:
        query = query.where(HRPayroll.employee_id == employee_id)
        count_query = count_query.where(HRPayroll.employee_id == employee_id)
    if period_from:
        query = query.where(HRPayroll.period_from >= period_from)
        count_query = count_query.where(HRPayroll.period_from >= period_from)
    if period_to:
        query = query.where(HRPayroll.period_to <= period_to)
        count_query = count_query.where(HRPayroll.period_to <= period_to)
    if status:
        query = query.where(HRPayroll.status == status)
        count_query = count_query.where(HRPayroll.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRPayroll.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    payroll_records = result.scalars().all()

    emp_ids = list({p.employee_id for p in payroll_records})
    emp_map = {}
    if emp_ids:
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id.in_(emp_ids)))
        for e in emp_result.scalars().all():
            emp_map[e.id] = e.full_name

    items = [{"id": p.id, "employeeId": p.employee_id, "employeeName": emp_map.get(p.employee_id, f"موظف #{p.employee_id}"),
             "period": p.period_from, "periodFrom": p.period_from, "periodTo": p.period_to,
             "basicSalary": p.basic_salary, "allowances": p.total_allowances,
             "overtime": p.overtime, "bonus": p.bonus,
             "deductions": p.deductions, "netSalary": p.net_salary,
             "status": p.status, "paymentDate": p.payment_date,
             "advanceDeduction": float(p.advance_deduction or 0),
             "journalEntryId": p.journal_entry_id}
            for p in payroll_records]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/payroll/calculate", response_model=dict)
async def calculate_payroll(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    emp_id = data.get("employee_id")
    emp_result = await db.execute(select(HREmployee).where(HREmployee.id == emp_id))
    emp = emp_result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    basic = float(emp.basic_salary or 0)
    housing = float(emp.housing_allowance or 0)
    transport = float(emp.transportation_allowance or 0)
    other = float(emp.other_allowances or 0)
    total_allow = housing + transport + other
    period_from = data.get("period_from", "")
    period_to = data.get("period_to", "")
    ot_auto, bonus_auto, ded_auto = await _period_extra_items(db, emp_id, period_from, period_to)
    overtime = float(data["overtime"]) if "overtime" in data else float(ot_auto or 0)
    bonus = float(data["bonus"]) if "bonus" in data else float(bonus_auto or 0)
    deductions = float(data["deductions"]) if "deductions" in data else float(ded_auto or 0)
    advance_deduction = float(await _get_active_advance_deduction(db, emp_id, period_from) or 0)
    total_deductions = deductions + advance_deduction
    net = basic + total_allow + overtime + bonus - total_deductions

    payroll = HRPayroll(
        employee_id=emp_id, period_from=period_from,
        period_to=period_to,
        basic_salary=basic, housing_allowance=housing,
        transportation_allowance=transport, other_allowances=other,
        total_allowances=total_allow, overtime=overtime,
        bonus=bonus, deductions=total_deductions,
        advance_deduction=advance_deduction, net_salary=net,
        notes=data.get("notes"), status="draft",
    )
    db.add(payroll)
    await db.flush()
    return {"id": payroll.id, "net_salary": net, "message": "Payroll calculated"}


@router.post("/payroll/calculate-bulk", response_model=dict)
async def calculate_payroll_bulk(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    period_from = data.get("period_from", "")
    period_to = data.get("period_to", "")
    department_id = data.get("department_id")

    query = select(HREmployee).where(HREmployee.is_active == True)
    if department_id:
        query = query.where(HREmployee.department_id == department_id)
    result = await db.execute(query)
    employees = result.scalars().all()

    created = []
    for emp in employees:
        basic = float(emp.basic_salary or 0)
        housing = float(emp.housing_allowance or 0)
        transport = float(emp.transportation_allowance or 0)
        other = float(emp.other_allowances or 0)
        total_allow = housing + transport + other
        ot_auto, bonus_auto, ded_auto = await _period_extra_items(db, emp.id, period_from, period_to)
        advance_deduction = await _get_active_advance_deduction(db, emp.id, period_from)
        total_deductions = ded_auto + advance_deduction
        net = basic + total_allow + ot_auto + bonus_auto - total_deductions

        payroll = HRPayroll(
            employee_id=emp.id, period_from=period_from, period_to=period_to,
            basic_salary=basic, housing_allowance=housing,
            transportation_allowance=transport, other_allowances=other,
            total_allowances=total_allow, overtime=ot_auto, bonus=bonus_auto,
            deductions=total_deductions, advance_deduction=advance_deduction,
            net_salary=net, status="draft",
        )
        db.add(payroll)
        created.append({"employee_id": emp.id, "employee_name": emp.full_name, "net_salary": net})

    await db.flush()
    return {"message": f"Calculated payroll for {len(created)} employees", "items": created}


@router.put("/payroll/{payroll_id}/status", response_model=MessageResponse)
async def update_payroll_status(payroll_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    """
    Update payroll status.

    Accounting Logic (per ERP_INSTRUCTIONS.md):
      When payroll is approved:
        1. Updates the payroll record status to 'approved'
        2. Emits 'payroll.approved' event to the Ledger Engine
        3. Ledger Engine creates a balanced journal entry:
           Dr. Salary Expense (5210)       basicSalary
           Dr. Allowance Expense (5230)    totalAllowances
           Dr. Bonus Expense (5220)        bonus
           Cr. Salaries Payable (2130)     netSalary
           Cr. Deductions (2140)           deductions
    """
    result = await db.execute(select(HRPayroll).where(HRPayroll.id == payroll_id))
    payroll = result.scalar_one_or_none()
    if not payroll:
        raise HTTPException(status_code=404, detail="Payroll record not found")

    new_status = data.get("status", "draft")

    # ── Transition guards ──────────────────────────────────────
    if new_status == "paid" and payroll.status not in ("approved", "paid"):
        raise HTTPException(status_code=400, detail="Payroll must be approved before it can be paid")

    values = {"status": new_status}
    if "payment_date" in data:
        values["payment_date"] = data["payment_date"]
    if "payment_method" in data:
        values["payment_method"] = data["payment_method"]
    await db.execute(update(HRPayroll).where(HRPayroll.id == payroll_id).values(**values))

    # Fetch employee + period once (used by several transitions)
    emp_result = await db.execute(select(HREmployee).where(HREmployee.id == payroll.employee_id))
    employee = emp_result.scalar_one_or_none()
    period_month, period_year = _parse_period(payroll.period_from)

    # ── Emit payroll.approved when status changes to 'approved' ──
    if new_status == "approved":
        if employee:
            dept_name = "Unknown Department"
            if employee.department_id:
                dept_result = await db.execute(select(HRDepartment).where(HRDepartment.id == employee.department_id))
                dept = dept_result.scalar_one_or_none()
                if dept:
                    dept_name = dept.name

            entry_result = await emit_payroll_approved(
                payroll_id=payroll.id,
                employee_id=payroll.employee_id,
                employee_name=employee.full_name,
                employee_code=employee.code,
                department_id=employee.department_id or 0,
                department_name=dept_name,
                period_month=period_month,
                period_year=period_year,
                basic_salary=float(payroll.basic_salary or 0),
                housing_allowance=float(payroll.housing_allowance or 0),
                transportation_allowance=float(payroll.transportation_allowance or 0),
                other_allowances=float(payroll.other_allowances or 0),
                total_allowances=float(payroll.total_allowances or 0),
                overtime=float(payroll.overtime or 0),
                bonus=float(payroll.bonus or 0),
                deductions=float(payroll.deductions or 0),
                advance_deduction=float(payroll.advance_deduction or 0),
                net_salary=float(payroll.net_salary or 0),
                user_id=current_user.id,
            )
            payroll.journal_entry_id = _extract_entry_id_from_event(entry_result) or payroll.journal_entry_id
            await db.flush()
            logger.info(f"HR: emitted payroll.approved event for payroll {payroll_id}")

    # ── Emit payroll.settled when status changes to 'paid' ─────
    elif new_status == "paid":
        if employee:
            payment_method = data.get("payment_method") or payroll.payment_method or "BANK"
            payment_date = data.get("payment_date") or payroll.payment_date

            entry_result = await emit_payroll_settled(
                payroll_id=payroll.id,
                employee_id=payroll.employee_id,
                employee_name=employee.full_name,
                period_month=period_month,
                period_year=period_year,
                net_salary=float(payroll.net_salary or 0),
                payment_method=payment_method,
                bank_account_id=data.get("bank_account_id"),
                bank_account_name=data.get("bank_account_name"),
                payment_date=payment_date,
                user_id=current_user.id,
            )
            payroll.journal_entry_id = _extract_entry_id_from_event(entry_result) or payroll.journal_entry_id
            await db.flush()
            logger.info(f"HR: emitted payroll.settled event for payroll {payroll_id}")

    # ── Emit payroll.voided when status changes to 'voided' ────
    elif new_status == "voided":
        reason = data.get("reason", "Voided from HR")
        await emit_payroll_voided(
            payroll_id=payroll.id,
            employee_id=payroll.employee_id,
            original_entry_id=payroll.journal_entry_id,
            reason=reason,
            user_id=current_user.id,
        )
        logger.info(f"HR: emitted payroll.voided event for payroll {payroll_id}")

    return MessageResponse(message="Payroll status updated")


# ── Employee Advances (السلف) ───────────────────────────────

@router.get("/advances", response_model=PaginationResponse)
async def list_advances(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRAdvance)
    count_query = select(func.count(HRAdvance.id))
    if employee_id:
        query = query.where(HRAdvance.employee_id == employee_id)
        count_query = count_query.where(HRAdvance.employee_id == employee_id)
    if status:
        query = query.where(HRAdvance.status == status)
        count_query = count_query.where(HRAdvance.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRAdvance.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    advances = result.scalars().all()

    emp_ids = list({a.employee_id for a in advances})
    emp_map = {}
    if emp_ids:
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id.in_(emp_ids)))
        for e in emp_result.scalars().all():
            emp_map[e.id] = e.full_name

    items = [{
        "id": a.id, "employeeId": a.employee_id,
        "employeeName": emp_map.get(a.employee_id, f"موظف #{a.employee_id}"),
        "advanceType": a.advance_type, "amount": float(a.amount or 0),
        "installments": a.installments, "monthlyDeduction": float(a.monthly_deduction or 0),
        "requestDate": a.request_date, "reason": a.reason,
        "status": a.status, "approvedBy": a.approved_by,
        "paymentMethod": a.payment_method, "paymentDate": a.payment_date,
        "journalEntryId": a.journal_entry_id, "notes": a.notes,
        "createdAt": a.created_at,
    } for a in advances]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/advances", response_model=dict)
async def create_advance(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    employee_id = data.get("employee_id")
    emp_result = await db.execute(select(HREmployee).where(HREmployee.id == employee_id))
    if not emp_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Employee not found")

    amount = float(data.get("amount", 0))
    installments = int(data.get("installments", 1) or 1)
    if installments <= 0:
        raise HTTPException(status_code=400, detail="Installments must be a positive number")
    monthly_deduction = float(data.get("monthly_deduction", 0) or 0)
    if monthly_deduction <= 0:
        monthly_deduction = round(amount / installments, 4)

    advance = HRAdvance(
        employee_id=employee_id,
        advance_type=data.get("advance_type", "advance"),
        amount=amount,
        installments=installments,
        monthly_deduction=monthly_deduction,
        request_date=data.get("request_date"),
        reason=data.get("reason"),
        status=data.get("status", "pending"),
        payment_method=data.get("payment_method", "BANK"),
        notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(advance)
    await db.flush()
    return {"id": advance.id, "monthly_deduction": monthly_deduction, "message": "Advance created"}


@router.put("/advances/{advance_id}/status", response_model=dict)
async def update_advance_status(advance_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRAdvance).where(HRAdvance.id == advance_id))
    advance = result.scalar_one_or_none()
    if not advance:
        raise HTTPException(status_code=404, detail="Advance not found")

    new_status = data.get("status", "pending")
    values = {"status": new_status, "approved_by": current_user.id}
    if new_status == "paid" and "payment_date" in data:
        values["payment_date"] = data["payment_date"]
    if "payment_method" in data:
        values["payment_method"] = data["payment_method"]
    await db.execute(update(HRAdvance).where(HRAdvance.id == advance_id).values(**values))

    # Emit advance.granted when approved → paid (money given to employee)
    if new_status == "paid":
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id == advance.employee_id))
        employee = emp_result.scalar_one_or_none()
        if employee:
            entry_result = await emit_advance_granted(
                advance_id=advance.id,
                employee_id=advance.employee_id,
                employee_name=employee.full_name,
                employee_code=employee.code,
                advance_type=advance.advance_type,
                amount=float(advance.amount or 0),
                payment_method=data.get("payment_method") or advance.payment_method or "BANK",
                bank_account_id=data.get("bank_account_id"),
                bank_account_name=data.get("bank_account_name"),
                request_date=advance.request_date,
                notes=advance.reason,
                user_id=current_user.id,
            )
            advance.journal_entry_id = _extract_entry_id_from_event(entry_result) or advance.journal_entry_id
            await db.flush()
            logger.info(f"HR: emitted employee.advance.granted event for advance {advance_id}")

    # Emit advance.voided when status changes to 'voided'
    elif new_status == "voided":
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id == advance.employee_id))
        employee = emp_result.scalar_one_or_none()
        await emit_advance_voided(
            advance_id=advance.id,
            employee_id=advance.employee_id,
            employee_name=employee.full_name if employee else f"موظف #{advance.employee_id}",
            original_entry_id=advance.journal_entry_id,
            reason=data.get("reason", "Voided from HR"),
            user_id=current_user.id,
        )
        logger.info(f"HR: emitted employee.advance.voided event for advance {advance_id}")

    return {"message": "Advance status updated"}


@router.put("/advances/{advance_id}", response_model=dict)
async def update_advance(advance_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRAdvance).where(HRAdvance.id == advance_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Advance not found")
    allowed_fields = ["advance_type", "amount", "installments", "monthly_deduction",
                      "request_date", "reason", "payment_method", "notes"]
    values = {}
    for f in allowed_fields:
        if f in data:
            values[f] = data[f]
    if values:
        await db.execute(update(HRAdvance).where(HRAdvance.id == advance_id).values(**values))
    return {"message": "Advance updated"}


@router.delete("/advances/{advance_id}", response_model=MessageResponse)
async def delete_advance(advance_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRAdvance).where(HRAdvance.id == advance_id))
    advance = result.scalar_one_or_none()
    if not advance:
        raise HTTPException(status_code=404, detail="Advance not found")
    if advance.status in ("paid", "approved") and advance.journal_entry_id:
        raise HTTPException(status_code=400, detail="Cannot delete a paid advance. Void it instead.")
    await db.execute(delete(HRAdvance).where(HRAdvance.id == advance_id))
    return MessageResponse(message="Advance deleted")


# ── Work Shifts (الورديات) ───────────────────────────────────

@router.get("/shifts")
async def list_shifts(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRShift).where(HRShift.is_active == True).order_by(HRShift.name))
    items = [{
        "id": s.id, "code": s.code, "name": s.name, "nameEn": s.name_en,
        "startTime": s.start_time, "endTime": s.end_time,
        "breakMinutes": s.break_minutes, "workingHours": float(s.working_hours or 0),
    } for s in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/shifts", response_model=dict)
async def create_shift(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["code", "name"])
    shift = HRShift(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), start_time=data.get("start_time"),
        end_time=data.get("end_time"), break_minutes=data.get("break_minutes"),
        working_hours=data.get("working_hours"), is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(shift)
    await db.flush()
    return {"id": shift.id, "message": "Shift created"}


@router.put("/shifts/{shift_id}", response_model=dict)
async def update_shift(shift_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("code", "name"))
    result = await db.execute(select(HRShift).where(HRShift.id == shift_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Shift not found")
    await db.execute(update(HRShift).where(HRShift.id == shift_id).values(**{
        k: data[k] for k in
        ("code", "name", "name_en", "start_time", "end_time", "break_minutes", "working_hours")
        if k in data
    }))
    return {"message": "Shift updated"}


@router.delete("/shifts/{shift_id}", response_model=MessageResponse)
async def delete_shift(shift_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(update(HRShift).where(HRShift.id == shift_id).values(is_active=False))
    return MessageResponse(message="Shift deleted")


# ── Leave Types & Balances (أنواع الإجازات وأرصدتها) ──────────

@router.get("/leave-types")
async def list_leave_types(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRLeaveType).where(HRLeaveType.is_active == True).order_by(HRLeaveType.name))
    items = [{
        "id": t.id, "code": t.code, "name": t.name, "nameEn": t.name_en,
        "daysPerYear": t.days_per_year, "isPaid": t.is_paid,
        "maxConsecutiveDays": t.max_consecutive_days, "requiresApproval": t.requires_approval,
    } for t in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/leave-types", response_model=dict)
async def create_leave_type(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["code", "name"])
    lt = HRLeaveType(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), days_per_year=data.get("days_per_year", 0),
        is_paid=data.get("is_paid", True), max_consecutive_days=data.get("max_consecutive_days"),
        requires_approval=data.get("requires_approval", True), is_active=True,
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(lt)
    await db.flush()
    return {"id": lt.id, "message": "Leave type created"}


@router.put("/leave-types/{type_id}", response_model=dict)
async def update_leave_type(type_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("code", "name"))
    result = await db.execute(select(HRLeaveType).where(HRLeaveType.id == type_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Leave type not found")
    await db.execute(update(HRLeaveType).where(HRLeaveType.id == type_id).values(**{
        k: data[k] for k in
        ("code", "name", "name_en", "days_per_year", "is_paid",
         "max_consecutive_days", "requires_approval")
        if k in data
    }))
    return {"message": "Leave type updated"}


@router.delete("/leave-types/{type_id}", response_model=MessageResponse)
async def delete_leave_type(type_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(update(HRLeaveType).where(HRLeaveType.id == type_id).values(is_active=False))
    return MessageResponse(message="Leave type deleted")


@router.get("/leave-balances")
async def list_leave_balances(
    employee_id: Optional[int] = None,
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRLeaveBalance)
    if employee_id:
        query = query.where(HRLeaveBalance.employee_id == employee_id)
    if year:
        query = query.where(HRLeaveBalance.year == year)
    result = await db.execute(query.order_by(HRLeaveBalance.year.desc(), HRLeaveBalance.employee_id))
    balances = result.scalars().all()

    emp_ids = list({b.employee_id for b in balances})
    emp_map = await _emp_names(db, emp_ids)
    type_ids = list({b.leave_type_id for b in balances})
    type_map = {}
    if type_ids:
        t_res = await db.execute(select(HRLeaveType).where(HRLeaveType.id.in_(type_ids)))
        for t in t_res.scalars().all():
            type_map[t.id] = t.name

    items = [{
        "id": b.id, "employeeId": b.employee_id,
        "employeeName": emp_map.get(b.employee_id, f"موظف #{b.employee_id}"),
        "leaveTypeId": b.leave_type_id, "leaveTypeName": type_map.get(b.leave_type_id, f"#{b.leave_type_id}"),
        "year": b.year, "daysEntitled": float(b.days_entitled or 0),
        "daysUsed": float(b.days_used or 0), "daysRemaining": float(b.days_remaining or 0),
        "notes": b.notes,
    } for b in balances]
    return {"items": items, "total": len(items)}


@router.post("/leave-balances/init", response_model=dict)
async def init_leave_balances(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    """Create/refresh leave balances for all active employees for a given year."""
    year = int(data.get("year", datetime.now().year))
    emp_result = await db.execute(select(HREmployee).where(HREmployee.is_active == True))
    employees = emp_result.scalars().all()
    type_result = await db.execute(select(HRLeaveType).where(HRLeaveType.is_active == True))
    leave_types = type_result.scalars().all()
    if not leave_types:
        raise HTTPException(status_code=400, detail="No leave types defined. Create leave types first.")

    created = 0
    for emp in employees:
        for lt in leave_types:
            existing = (await db.execute(
                select(HRLeaveBalance).where(
                    HRLeaveBalance.employee_id == emp.id,
                    HRLeaveBalance.leave_type_id == lt.id,
                    HRLeaveBalance.year == year,
                )
            )).scalar_one_or_none()
            if existing:
                continue
            db.add(HRLeaveBalance(
                employee_id=emp.id, leave_type_id=lt.id, year=year,
                days_entitled=float(lt.days_per_year or 0), days_used=0,
                days_remaining=float(lt.days_per_year or 0),
                created_at=datetime.now(UTC).replace(tzinfo=None),
            ))
            created += 1
    await db.flush()
    return {"message": f"Initialized {created} leave balances for year {year}", "created": created}


@router.put("/leave-balances/{balance_id}", response_model=dict)
async def update_leave_balance(balance_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRLeaveBalance).where(HRLeaveBalance.id == balance_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Leave balance not found")
    values = {k: data[k] for k in ("days_entitled", "days_used", "days_remaining", "notes") if k in data}
    if values:
        await db.execute(update(HRLeaveBalance).where(HRLeaveBalance.id == balance_id).values(**values))
    return {"message": "Leave balance updated"}


# ── Overtime (العمل الإضافي) ─────────────────────────────────

@router.get("/overtime", response_model=PaginationResponse)
async def list_overtime(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HROvertime)
    count_query = select(func.count(HROvertime.id))
    if employee_id:
        query = query.where(HROvertime.employee_id == employee_id)
        count_query = count_query.where(HROvertime.employee_id == employee_id)
    if status:
        query = query.where(HROvertime.status == status)
        count_query = count_query.where(HROvertime.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HROvertime.date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {o.employee_id for o in rows})

    items = [{
        "id": o.id, "employeeId": o.employee_id,
        "employeeName": emp_map.get(o.employee_id, f"موظف #{o.employee_id}"),
        "date": o.date, "hours": float(o.hours or 0),
        "rateMultiplier": float(o.rate_multiplier or 1.5),
        "amount": float(o.amount or 0), "reason": o.reason,
        "status": o.status, "approvedBy": o.approved_by,
    } for o in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/overtime", response_model=dict)
async def create_overtime(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id"])
    hours = float(data.get("hours", 0))
    rate_multiplier = float(data.get("rate_multiplier", 1.5) or 1.5)
    amount = float(data.get("amount", 0) or 0)
    if amount <= 0:
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id == data.get("employee_id")))
        emp = emp_result.scalar_one_or_none()
        if emp:
            hourly = float(emp.basic_salary or 0) / 30 / 8
            amount = round(hours * hourly * rate_multiplier, 4)
    ot = HROvertime(
        employee_id=data.get("employee_id"), date=data.get("date"),
        hours=hours, rate_multiplier=rate_multiplier, amount=amount,
        reason=data.get("reason"), status=data.get("status", "pending"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(ot)
    await db.flush()
    return {"id": ot.id, "amount": amount, "message": "Overtime created"}


@router.put("/overtime/{ot_id}", response_model=dict)
async def update_overtime(ot_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ())
    result = await db.execute(select(HROvertime).where(HROvertime.id == ot_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Overtime not found")
    await db.execute(update(HROvertime).where(HROvertime.id == ot_id).values(**{
        k: data[k] for k in
        ("date", "hours", "rate_multiplier", "amount", "reason") if k in data
    }))
    return {"message": "Overtime updated"}


@router.put("/overtime/{ot_id}/status", response_model=dict)
async def update_overtime_status(ot_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HROvertime).where(HROvertime.id == ot_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Overtime not found")
    await db.execute(update(HROvertime).where(HROvertime.id == ot_id).values(
        status=data.get("status", "pending"), approved_by=current_user.id,
        approved_at=datetime.now(UTC).replace(tzinfo=None).isoformat(),
    ))
    return {"message": "Overtime status updated"}


@router.delete("/overtime/{ot_id}", response_model=MessageResponse)
async def delete_overtime(ot_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HROvertime).where(HROvertime.id == ot_id))
    return MessageResponse(message="Overtime deleted")


# ── Bonuses & Deductions (مكافآت وخصومات) ─────────────────────

@router.get("/bonuses", response_model=PaginationResponse)
async def list_bonuses(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    bonus_type: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRBonus)
    count_query = select(func.count(HRBonus.id))
    if employee_id:
        query = query.where(HRBonus.employee_id == employee_id)
        count_query = count_query.where(HRBonus.employee_id == employee_id)
    if bonus_type:
        query = query.where(HRBonus.bonus_type == bonus_type)
        count_query = count_query.where(HRBonus.bonus_type == bonus_type)
    if status:
        query = query.where(HRBonus.status == status)
        count_query = count_query.where(HRBonus.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRBonus.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {b.employee_id for b in rows})

    items = [{
        "id": b.id, "employeeId": b.employee_id,
        "employeeName": emp_map.get(b.employee_id, f"موظف #{b.employee_id}"),
        "bonusType": b.bonus_type, "amount": float(b.amount or 0),
        "period": b.period, "description": b.description,
        "status": b.status, "approvedBy": b.approved_by,
    } for b in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/bonuses", response_model=dict)
async def create_bonus(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id", "amount"])
    bonus = HRBonus(
        employee_id=data.get("employee_id"),
        bonus_type=data.get("bonus_type", "bonus"),
        amount=float(data.get("amount", 0)),
        period=data.get("period"), description=data.get("description"),
        status=data.get("status", "pending"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(bonus)
    await db.flush()
    return {"id": bonus.id, "message": "Bonus record created"}


@router.put("/bonuses/{bonus_id}", response_model=dict)
async def update_bonus(bonus_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("amount",))
    result = await db.execute(select(HRBonus).where(HRBonus.id == bonus_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bonus not found")
    await db.execute(update(HRBonus).where(HRBonus.id == bonus_id).values(**{
        k: data[k] for k in
        ("bonus_type", "amount", "period", "description") if k in data
    }))
    return {"message": "Bonus record updated"}


@router.put("/bonuses/{bonus_id}/status", response_model=dict)
async def update_bonus_status(bonus_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRBonus).where(HRBonus.id == bonus_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Bonus not found")
    await db.execute(update(HRBonus).where(HRBonus.id == bonus_id).values(
        status=data.get("status", "pending"), approved_by=current_user.id,
    ))
    return {"message": "Bonus status updated"}


@router.delete("/bonuses/{bonus_id}", response_model=MessageResponse)
async def delete_bonus(bonus_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRBonus).where(HRBonus.id == bonus_id))
    return MessageResponse(message="Bonus record deleted")


# ── Performance Reviews (تقييم الأداء) ────────────────────────

@router.get("/performance-reviews", response_model=PaginationResponse)
async def list_performance_reviews(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRPerformanceReview)
    count_query = select(func.count(HRPerformanceReview.id))
    if employee_id:
        query = query.where(HRPerformanceReview.employee_id == employee_id)
        count_query = count_query.where(HRPerformanceReview.employee_id == employee_id)
    if status:
        query = query.where(HRPerformanceReview.status == status)
        count_query = count_query.where(HRPerformanceReview.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRPerformanceReview.review_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()

    emp_ids = {r.employee_id for r in rows}
    reviewer_ids = {r.reviewer_id for r in rows if r.reviewer_id}
    emp_map = await _emp_names(db, emp_ids | reviewer_ids)

    items = [{
        "id": r.id, "employeeId": r.employee_id,
        "employeeName": emp_map.get(r.employee_id, f"موظف #{r.employee_id}"),
        "reviewerId": r.reviewer_id,
        "reviewerName": emp_map.get(r.reviewer_id) if r.reviewer_id else None,
        "reviewDate": r.review_date, "reviewPeriod": r.review_period,
        "rating": float(r.rating or 0), "overallRating": float(r.overall_rating or 0),
        "goalsAchieved": r.goals_achieved, "strengths": r.strengths,
        "improvements": r.improvements, "recommendations": r.recommendations,
        "status": r.status, "nextReviewDate": r.next_review_date,
    } for r in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/performance-reviews", response_model=dict)
async def create_performance_review(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id"])
    review = HRPerformanceReview(
        employee_id=data.get("employee_id"), reviewer_id=data.get("reviewer_id"),
        review_date=data.get("review_date"), review_period=data.get("review_period"),
        rating=data.get("rating"), goals_achieved=data.get("goals_achieved"),
        strengths=data.get("strengths"), improvements=data.get("improvements"),
        recommendations=data.get("recommendations"), overall_rating=data.get("overall_rating"),
        status=data.get("status", "draft"), next_review_date=data.get("next_review_date"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(review)
    await db.flush()
    return {"id": review.id, "message": "Performance review created"}


@router.put("/performance-reviews/{review_id}", response_model=dict)
async def update_performance_review(review_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ())
    result = await db.execute(select(HRPerformanceReview).where(HRPerformanceReview.id == review_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Review not found")
    await db.execute(update(HRPerformanceReview).where(HRPerformanceReview.id == review_id).values(**{
        k: data[k] for k in
        ("reviewer_id", "review_date", "review_period", "rating", "goals_achieved",
         "strengths", "improvements", "recommendations", "overall_rating", "status",
         "next_review_date") if k in data
    }))
    return {"message": "Performance review updated"}


@router.delete("/performance-reviews/{review_id}", response_model=MessageResponse)
async def delete_performance_review(review_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRPerformanceReview).where(HRPerformanceReview.id == review_id))
    return MessageResponse(message="Performance review deleted")


# ── Contracts (العقود) ───────────────────────────────────────

@router.get("/contracts", response_model=PaginationResponse)
async def list_contracts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRContract)
    count_query = select(func.count(HRContract.id))
    if employee_id:
        query = query.where(HRContract.employee_id == employee_id)
        count_query = count_query.where(HRContract.employee_id == employee_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRContract.start_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {c.employee_id for c in rows})

    items = [{
        "id": c.id, "employeeId": c.employee_id,
        "employeeName": emp_map.get(c.employee_id, f"موظف #{c.employee_id}"),
        "contractType": c.contract_type, "startDate": c.start_date,
        "endDate": c.end_date, "probationEndDate": c.probation_end_date,
        "basicSalary": float(c.basic_salary or 0), "allowances": float(c.allowances or 0),
        "isActive": c.is_active, "status": c.status, "notes": c.notes,
    } for c in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/contracts", response_model=dict)
async def create_contract(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id"])
    contract = HRContract(
        employee_id=data.get("employee_id"), contract_type=data.get("contract_type"),
        start_date=data.get("start_date"), end_date=data.get("end_date"),
        probation_end_date=data.get("probation_end_date"),
        basic_salary=data.get("basic_salary"), allowances=data.get("allowances"),
        is_active=data.get("is_active", True), status=data.get("status", "active"),
        notes=data.get("notes"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(contract)
    await db.flush()
    return {"id": contract.id, "message": "Contract created"}


@router.put("/contracts/{contract_id}", response_model=dict)
async def update_contract(contract_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ())
    result = await db.execute(select(HRContract).where(HRContract.id == contract_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Contract not found")
    await db.execute(update(HRContract).where(HRContract.id == contract_id).values(**{
        k: data[k] for k in
        ("contract_type", "start_date", "end_date", "probation_end_date", "basic_salary",
         "allowances", "is_active", "status", "notes") if k in data
    }))
    return {"message": "Contract updated"}


@router.delete("/contracts/{contract_id}", response_model=MessageResponse)
async def delete_contract(contract_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRContract).where(HRContract.id == contract_id))
    return MessageResponse(message="Contract deleted")


# ── Resignations (الاستقالات وإنهاء الخدمة) ──────────────────

@router.get("/resignations", response_model=PaginationResponse)
async def list_resignations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRResignation)
    count_query = select(func.count(HRResignation.id))
    if employee_id:
        query = query.where(HRResignation.employee_id == employee_id)
        count_query = count_query.where(HRResignation.employee_id == employee_id)
    if status:
        query = query.where(HRResignation.status == status)
        count_query = count_query.where(HRResignation.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRResignation.resign_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {r.employee_id for r in rows})

    items = [{
        "id": r.id, "employeeId": r.employee_id,
        "employeeName": emp_map.get(r.employee_id, f"موظف #{r.employee_id}"),
        "resignDate": r.resign_date, "lastWorkingDay": r.last_working_day,
        "reason": r.reason, "status": r.status, "approvedBy": r.approved_by,
        "notes": r.notes,
    } for r in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/resignations", response_model=dict)
async def create_resignation(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id"])
    resignation = HRResignation(
        employee_id=data.get("employee_id"), resign_date=data.get("resign_date"),
        last_working_day=data.get("last_working_day"), reason=data.get("reason"),
        status=data.get("status", "pending"), notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(resignation)
    await db.flush()
    return {"id": resignation.id, "message": "Resignation created"}


@router.put("/resignations/{resignation_id}/status", response_model=dict)
async def update_resignation_status(resignation_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRResignation).where(HRResignation.id == resignation_id))
    resignation = result.scalar_one_or_none()
    if not resignation:
        raise HTTPException(status_code=404, detail="Resignation not found")
    new_status = data.get("status", "pending")
    await db.execute(update(HRResignation).where(HRResignation.id == resignation_id).values(
        status=new_status, approved_by=current_user.id,
    ))
    # When approved, mark the employee inactive so they leave the active roster
    if new_status == "approved":
        await db.execute(update(HREmployee).where(HREmployee.id == resignation.employee_id).values(
            employment_status="مُنهى", is_active=False,
        ))
    return {"message": "Resignation status updated"}


@router.delete("/resignations/{resignation_id}", response_model=MessageResponse)
async def delete_resignation(resignation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRResignation).where(HRResignation.id == resignation_id))
    return MessageResponse(message="Resignation deleted")


# ── Job Postings (إعلانات الوظائف) ───────────────────────────

@router.get("/job-postings", response_model=PaginationResponse)
async def list_job_postings(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRJobPosting)
    count_query = select(func.count(HRJobPosting.id))
    if status:
        query = query.where(HRJobPosting.status == status)
        count_query = count_query.where(HRJobPosting.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRJobPosting.posted_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()

    dept_ids = {p.department_id for p in rows if p.department_id}
    dept_map = {}
    if dept_ids:
        d_res = await db.execute(select(HRDepartment).where(HRDepartment.id.in_(dept_ids)))
        for d in d_res.scalars().all():
            dept_map[d.id] = d.name

    items = [{
        "id": p.id, "positionId": p.position_id, "title": p.title,
        "departmentId": p.department_id, "departmentName": dept_map.get(p.department_id),
        "description": p.description, "requirements": p.requirements,
        "vacancies": p.vacancies, "salaryMin": float(p.salary_min or 0),
        "salaryMax": float(p.salary_max or 0), "location": p.location,
        "employmentType": p.employment_type, "status": p.status,
        "postedDate": p.posted_date, "deadline": p.deadline,
        "candidatesCount": 0,
    } for p in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/job-postings", response_model=dict)
async def create_job_posting(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    posting = HRJobPosting(
        position_id=data.get("position_id"), title=data.get("title", ""),
        department_id=data.get("department_id"), description=data.get("description"),
        requirements=data.get("requirements"), vacancies=data.get("vacancies", 1),
        salary_min=data.get("salary_min"), salary_max=data.get("salary_max"),
        location=data.get("location"), employment_type=data.get("employment_type", "full_time"),
        status=data.get("status", "open"), posted_date=data.get("posted_date"),
        deadline=data.get("deadline"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(posting)
    await db.flush()
    return {"id": posting.id, "message": "Job posting created"}


@router.put("/job-postings/{posting_id}", response_model=dict)
async def update_job_posting(posting_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRJobPosting).where(HRJobPosting.id == posting_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Job posting not found")
    values = {k: data[k] for k in (
        "position_id", "title", "department_id", "description", "requirements",
        "vacancies", "salary_min", "salary_max", "location", "employment_type",
        "status", "posted_date", "deadline",
    ) if k in data}
    if values:
        await db.execute(update(HRJobPosting).where(HRJobPosting.id == posting_id).values(**values))
    return {"message": "Job posting updated"}


@router.delete("/job-postings/{posting_id}", response_model=MessageResponse)
async def delete_job_posting(posting_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRJobPosting).where(HRJobPosting.id == posting_id))
    return MessageResponse(message="Job posting deleted")


# ── Candidates (المتقدمون للوظائف) ───────────────────────────

@router.get("/candidates", response_model=PaginationResponse)
async def list_candidates(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    job_posting_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRCandidate)
    count_query = select(func.count(HRCandidate.id))
    if job_posting_id:
        query = query.where(HRCandidate.job_posting_id == job_posting_id)
        count_query = count_query.where(HRCandidate.job_posting_id == job_posting_id)
    if status:
        query = query.where(HRCandidate.status == status)
        count_query = count_query.where(HRCandidate.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRCandidate.applied_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()

    job_ids = {c.job_posting_id for c in rows if c.job_posting_id}
    job_map = {}
    if job_ids:
        j_res = await db.execute(select(HRJobPosting).where(HRJobPosting.id.in_(job_ids)))
        for j in j_res.scalars().all():
            job_map[j.id] = j.title

    items = [{
        "id": c.id, "jobPostingId": c.job_posting_id,
        "jobTitle": job_map.get(c.job_posting_id),
        "name": c.name, "email": c.email, "phone": c.phone,
        "resumeText": c.resume_text, "status": c.status,
        "appliedDate": c.applied_date, "rating": float(c.rating or 0),
        "source": c.source, "notes": c.notes,
    } for c in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/candidates", response_model=dict)
async def create_candidate(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    candidate = HRCandidate(
        job_posting_id=data.get("job_posting_id"), name=data.get("name", ""),
        email=data.get("email"), phone=data.get("phone"), resume_text=data.get("resume_text"),
        status=data.get("status", "new"), applied_date=data.get("applied_date"),
        rating=data.get("rating"), source=data.get("source"), notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(candidate)
    await db.flush()
    return {"id": candidate.id, "message": "Candidate created"}


@router.put("/candidates/{candidate_id}", response_model=dict)
async def update_candidate(candidate_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRCandidate).where(HRCandidate.id == candidate_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Candidate not found")
    values = {k: data[k] for k in (
        "job_posting_id", "name", "email", "phone", "resume_text",
        "status", "rating", "source", "notes",
    ) if k in data}
    if values:
        await db.execute(update(HRCandidate).where(HRCandidate.id == candidate_id).values(**values))
    return {"message": "Candidate updated"}


@router.delete("/candidates/{candidate_id}", response_model=MessageResponse)
async def delete_candidate(candidate_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRCandidate).where(HRCandidate.id == candidate_id))
    return MessageResponse(message="Candidate deleted")


# ── Training (التدريب والتطوير) ──────────────────────────────

@router.get("/training", response_model=PaginationResponse)
async def list_training(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRTraining)
    count_query = select(func.count(HRTraining.id))
    if employee_id:
        query = query.where(HRTraining.employee_id == employee_id)
        count_query = count_query.where(HRTraining.employee_id == employee_id)
    if status:
        query = query.where(HRTraining.status == status)
        count_query = count_query.where(HRTraining.status == status)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HRTraining.start_date.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {t.employee_id for t in rows})

    items = [{
        "id": t.id, "employeeId": t.employee_id,
        "employeeName": emp_map.get(t.employee_id, f"موظف #{t.employee_id}"),
        "courseName": t.course_name, "provider": t.provider,
        "startDate": t.start_date, "endDate": t.end_date,
        "cost": float(t.cost or 0), "certificate": t.certificate,
        "status": t.status, "notes": t.notes,
    } for t in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/training", response_model=dict)
async def create_training(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id", "course_name"])
    training = HRTraining(
        employee_id=data.get("employee_id"), course_name=data.get("course_name", ""),
        provider=data.get("provider"), start_date=data.get("start_date"),
        end_date=data.get("end_date"), cost=data.get("cost"),
        certificate=data.get("certificate"), status=data.get("status", "planned"),
        notes=data.get("notes"), created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(training)
    await db.flush()
    return {"id": training.id, "message": "Training created"}


@router.put("/training/{training_id}", response_model=dict)
async def update_training(training_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ("course_name",))
    result = await db.execute(select(HRTraining).where(HRTraining.id == training_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Training not found")
    await db.execute(update(HRTraining).where(HRTraining.id == training_id).values(**{
        k: data[k] for k in
        ("course_name", "provider", "start_date", "end_date", "cost", "certificate",
         "status", "notes") if k in data
    }))
    return {"message": "Training updated"}


@router.delete("/training/{training_id}", response_model=MessageResponse)
async def delete_training(training_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRTraining).where(HRTraining.id == training_id))
    return MessageResponse(message="Training deleted")


# ── Employee Documents (مستندات الموظفين) ────────────────────

@router.get("/documents", response_model=PaginationResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    employee_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HREmployeeDocument)
    count_query = select(func.count(HREmployeeDocument.id))
    if employee_id:
        query = query.where(HREmployeeDocument.employee_id == employee_id)
        count_query = count_query.where(HREmployeeDocument.employee_id == employee_id)

    total = (await db.execute(count_query)).scalar() or 0
    offset = (page - 1) * per_page
    query = query.order_by(HREmployeeDocument.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    rows = result.scalars().all()
    emp_map = await _emp_names(db, {d.employee_id for d in rows})

    items = [{
        "id": d.id, "employeeId": d.employee_id,
        "employeeName": emp_map.get(d.employee_id, f"موظف #{d.employee_id}"),
        "documentType": d.document_type, "title": d.title,
        "fileName": d.file_name, "filePath": d.file_path,
        "issueDate": d.issue_date, "expiryDate": d.expiry_date, "notes": d.notes,
    } for d in rows]
    return PaginationResponse(total=total, page=page, per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0, items=items)


@router.post("/documents", response_model=dict)
async def create_document(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    require_fields(data, ["employee_id"])
    doc = HREmployeeDocument(
        employee_id=data.get("employee_id"), document_type=data.get("document_type"),
        title=data.get("title"), file_name=data.get("file_name"),
        file_path=data.get("file_path"), issue_date=data.get("issue_date"),
        expiry_date=data.get("expiry_date"), notes=data.get("notes"),
        created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(doc)
    await db.flush()
    return {"id": doc.id, "message": "Document created"}


@router.put("/documents/{doc_id}", response_model=dict)
async def update_document(doc_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    _require_update_fields(data, ())
    result = await db.execute(select(HREmployeeDocument).where(HREmployeeDocument.id == doc_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Document not found")
    await db.execute(update(HREmployeeDocument).where(HREmployeeDocument.id == doc_id).values(**{
        k: data[k] for k in
        ("document_type", "title", "file_name", "file_path", "issue_date",
         "expiry_date", "notes") if k in data
    }))
    return {"message": "Document updated"}


@router.delete("/documents/{doc_id}", response_model=MessageResponse)
async def delete_document(doc_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HREmployeeDocument).where(HREmployeeDocument.id == doc_id))
    return MessageResponse(message="Document deleted")


# ── Holidays (الإجازات الرسمية) ──────────────────────────────

@router.get("/holidays")
async def list_holidays(year: Optional[int] = None, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    query = select(HRHoliday)
    if year:
        query = query.where(HRHoliday.date.startswith(str(year)))
    result = await db.execute(query.order_by(HRHoliday.date))
    items = [{
        "id": h.id, "name": h.name, "date": h.date,
        "isRecurring": h.is_recurring, "type": h.type, "isActive": h.is_active,
    } for h in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/holidays", response_model=dict)
async def create_holiday(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    holiday = HRHoliday(
        name=data.get("name", ""), date=data.get("date", ""),
        is_recurring=data.get("is_recurring", False), type=data.get("type", "official"),
        is_active=True, created_at=datetime.now(UTC).replace(tzinfo=None),
    )
    db.add(holiday)
    await db.flush()
    return {"id": holiday.id, "message": "Holiday created"}


@router.put("/holidays/{holiday_id}", response_model=dict)
async def update_holiday(holiday_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    result = await db.execute(select(HRHoliday).where(HRHoliday.id == holiday_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Holiday not found")
    values = {k: data[k] for k in ("name", "date", "is_recurring", "type") if k in data}
    if values:
        await db.execute(update(HRHoliday).where(HRHoliday.id == holiday_id).values(**values))
    return {"message": "Holiday updated"}


@router.delete("/holidays/{holiday_id}", response_model=MessageResponse)
async def delete_holiday(holiday_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_permission("MANAGE_HR"))):
    await db.execute(delete(HRHoliday).where(HRHoliday.id == holiday_id))
    return MessageResponse(message="Holiday deleted")


# ── HR Reports (تقارير الموارد البشرية) ──────────────────────

@router.get("/reports/summary")
async def hr_reports_summary(
    year: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    year = year or datetime.now().year

    active_emp = (await db.execute(select(func.count(HREmployee.id)).where(HREmployee.is_active == True))).scalar() or 0
    total_emp = (await db.execute(select(func.count(HREmployee.id)))).scalar() or 0
    dept_count = (await db.execute(select(func.count(HRDepartment.id)).where(HRDepartment.is_active == True))).scalar() or 0
    pending_leaves = (await db.execute(select(func.count(HRLeave.id)).where(HRLeave.status == "pending"))).scalar() or 0
    pending_overtime = (await db.execute(select(func.count(HROvertime.id)).where(HROvertime.status == "pending"))).scalar() or 0
    pending_resignations = (await db.execute(select(func.count(HRResignation.id)).where(HRResignation.status == "pending"))).scalar() or 0
    open_jobs = (await db.execute(select(func.count(HRJobPosting.id)).where(HRJobPosting.status == "open"))).scalar() or 0
    new_candidates = (await db.execute(select(func.count(HRCandidate.id)).where(HRCandidate.status == "new"))).scalar() or 0
    open_candidates = (await db.execute(select(func.count(HRCandidate.id)))).scalar() or 0
    training_planned = (await db.execute(select(func.count(HRTraining.id)).where(HRTraining.status != "completed"))).scalar() or 0
    draft_payroll = (await db.execute(select(func.count(HRPayroll.id)).where(HRPayroll.status == "draft"))).scalar() or 0
    approved_advances = (await db.execute(select(func.count(HRAdvance.id)).where(HRAdvance.status == "approved"))).scalar() or 0

    emp_by_dept = []
    dept_rows = await db.execute(
        select(HRDepartment.name, func.count(HREmployee.id))
        .outerjoin(HREmployee, HREmployee.department_id == HRDepartment.id)
        .where(HRDepartment.is_active == True)
        .group_by(HRDepartment.name)
        .order_by(func.count(HREmployee.id).desc())
    )
    for name, cnt in dept_rows.all():
        emp_by_dept.append({"department": name, "count": cnt})

    emp_by_gender = []
    gender_rows = await db.execute(
        select(HREmployee.gender, func.count(HREmployee.id)).where(HREmployee.is_active == True).group_by(HREmployee.gender)
    )
    for gender, cnt in gender_rows.all():
        emp_by_gender.append({"gender": gender or "غير محدد", "count": cnt})

    leave_summary = []
    leave_rows = await db.execute(
        select(HRLeave.leave_type, func.count(HRLeave.id), func.sum(HRLeave.days_count))
        .where(HRLeave.status == "approved")
        .group_by(HRLeave.leave_type)
    )
    for lt, cnt, days in leave_rows.all():
        leave_summary.append({"leaveType": lt, "count": cnt, "days": int(days or 0)})

    payroll_total = (await db.execute(
        select(func.coalesce(func.sum(HRPayroll.net_salary), 0)).where(
            HRPayroll.status == "paid",
            HRPayroll.period_from.startswith(str(year)),
        )
    )).scalar() or 0

    gender_total = sum(g["count"] for g in emp_by_gender) or 1

    return {
        "activeEmployees": active_emp,
        "totalEmployees": total_emp,
        "departments": dept_count,
        "pendingLeaves": pending_leaves,
        "pendingOvertime": pending_overtime,
        "pendingResignations": pending_resignations,
        "openJobs": open_jobs,
        "openCandidates": open_candidates,
        "newCandidates": new_candidates,
        "trainingPlanned": training_planned,
        "draftPayroll": draft_payroll,
        "approvedAdvances": approved_advances,
        "payrollPaidTotal": float(payroll_total or 0),
        "employeesByDepartment": emp_by_dept,
        "employeesByGender": emp_by_gender,
        "leaveSummary": leave_summary,
        "genderDistribution": [{"label": g["gender"], "value": round(g["count"] / gender_total * 100, 1)} for g in emp_by_gender],
    }
