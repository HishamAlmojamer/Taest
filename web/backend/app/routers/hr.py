import math
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from app.database import get_db
from app.models.hr import (
    HREmployee, HRDepartment, HRPosition,
    HRAttendance, HRLeave, HRPayroll,
)
from app.models.user import User
from app.schemas.common import MessageResponse, PaginationResponse
from app.utils.deps import get_current_user
from app.utils.event_emitter import emit_payroll_approved

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Departments ───────────────────────────────────────────────

@router.get("/departments")
async def list_departments(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRDepartment).where(HRDepartment.is_active == True).order_by(HRDepartment.name))
    items = [{"id": d.id, "code": d.code, "name": d.name, "name_en": d.name_en,
             "description": d.description, "manager_id": d.manager_id, "managerName": None,
             "parent_id": d.parent_id, "employeeCount": 0}
            for d in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/departments", response_model=dict)
async def create_department(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    dept = HRDepartment(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), description=data.get("description"),
        manager_id=data.get("manager_id"), parent_id=data.get("parent_id"),
        created_at=str(datetime.utcnow()),
    )
    db.add(dept)
    await db.flush()
    return {"id": dept.id, "message": "Department created"}


@router.put("/departments/{dept_id}", response_model=dict)
async def update_department(dept_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRDepartment).where(HRDepartment.id == dept_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Department not found")
    await db.execute(update(HRDepartment).where(HRDepartment.id == dept_id).values(
        code=data.get("code"), name=data.get("name"),
        name_en=data.get("name_en"), description=data.get("description"),
        manager_id=data.get("manager_id"), parent_id=data.get("parent_id"),
    ))
    return {"message": "Department updated"}


@router.delete("/departments/{dept_id}", response_model=MessageResponse)
async def delete_department(dept_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
async def create_position(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    pos = HRPosition(
        code=data.get("code"), name=data.get("name", ""),
        name_en=data.get("name_en"), department_id=data.get("department_id"),
        description=data.get("description"), min_salary=data.get("min_salary", 0),
        max_salary=data.get("max_salary", 0), created_at=datetime.utcnow(),
    )
    db.add(pos)
    await db.flush()
    return {"id": pos.id, "message": "Position created"}


@router.put("/positions/{pos_id}", response_model=dict)
async def update_position(pos_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRPosition).where(HRPosition.id == pos_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Position not found")
    await db.execute(update(HRPosition).where(HRPosition.id == pos_id).values(
        code=data.get("code"), name=data.get("name"),
        name_en=data.get("name_en"), department_id=data.get("department_id"),
        description=data.get("description"), min_salary=data.get("min_salary", 0),
        max_salary=data.get("max_salary", 0),
    ))
    return {"message": "Position updated"}


@router.delete("/positions/{pos_id}", response_model=MessageResponse)
async def delete_position(pos_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
async def create_employee(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
        notes=data.get("notes"), created_at=str(datetime.utcnow()),
    )
    db.add(emp)
    await db.flush()
    return {"id": emp.id, "message": "Employee created"}


@router.put("/employees/{emp_id}", response_model=dict)
async def update_employee(emp_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
async def delete_employee(emp_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(update(HREmployee).where(HREmployee.id == emp_id).values(is_active=False))
    return MessageResponse(message="Employee deleted")


# ── Attendance ────────────────────────────────────────────────

@router.get("/attendance")
async def list_attendance(
    employee_id: Optional[int] = None,
    date: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRAttendance)
    if employee_id:
        query = query.where(HRAttendance.employee_id == employee_id)
    if date:
        query = query.where(HRAttendance.date == date)
    if from_date:
        query = query.where(HRAttendance.date >= from_date)
    if to_date:
        query = query.where(HRAttendance.date <= to_date)
    query = query.order_by(HRAttendance.date.desc()).limit(500)
    result = await db.execute(query)
    return [{"id": a.id, "employee_id": a.employee_id, "date": a.date,
             "check_in": a.check_in, "check_out": a.check_out,
             "status": a.status, "notes": a.notes}
            for a in result.scalars().all()]


@router.post("/attendance", response_model=dict)
async def create_attendance(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    att = HRAttendance(
        employee_id=data.get("employee_id"), date=data.get("date", ""),
        check_in=data.get("check_in"), check_out=data.get("check_out"),
        status=data.get("status", "present"), notes=data.get("notes"),
    )
    db.add(att)
    await db.flush()
    return {"id": att.id, "message": "Attendance recorded"}


@router.put("/attendance/{att_id}", response_model=dict)
async def update_attendance(att_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRAttendance).where(HRAttendance.id == att_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Attendance record not found")
    values = {k: data[k] for k in ("check_in", "check_out", "status", "notes", "date") if k in data}
    if values:
        await db.execute(update(HRAttendance).where(HRAttendance.id == att_id).values(**values))
    return {"message": "Attendance updated"}


@router.delete("/attendance/{att_id}", response_model=MessageResponse)
async def delete_attendance(att_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(delete(HRAttendance).where(HRAttendance.id == att_id))
    return MessageResponse(message="Attendance deleted")


# ── Leaves ────────────────────────────────────────────────────

@router.get("/leaves")
async def list_leaves(
    employee_id: Optional[int] = None,
    status: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRLeave)
    if employee_id:
        query = query.where(HRLeave.employee_id == employee_id)
    if status:
        query = query.where(HRLeave.status == status)
    query = query.order_by(HRLeave.created_at.desc()).limit(500)
    result = await db.execute(query)
    items = [{"id": l.id, "employeeId": l.employee_id, "leaveType": l.leave_type,
             "startDate": l.start_date, "endDate": l.end_date,
             "daysCount": l.days_count, "reason": l.reason,
             "status": l.status, "approvedBy": l.approved_by}
            for l in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/leaves", response_model=dict)
async def create_leave(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
async def update_leave_status(leave_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(HRLeave).where(HRLeave.id == leave_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Leave not found")
    await db.execute(update(HRLeave).where(HRLeave.id == leave_id).values(
        status=data.get("status", "pending"), approved_by=current_user.id,
    ))
    return MessageResponse(message="Leave status updated")


@router.delete("/leaves/{leave_id}", response_model=MessageResponse)
async def delete_leave(leave_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    await db.execute(delete(HRLeave).where(HRLeave.id == leave_id))
    return MessageResponse(message="Leave deleted")


# ── Payroll ───────────────────────────────────────────────────

@router.get("/payroll")
async def list_payroll(
    employee_id: Optional[int] = None,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(HRPayroll)
    if employee_id:
        query = query.where(HRPayroll.employee_id == employee_id)
    if period_from:
        query = query.where(HRPayroll.period_from >= period_from)
    if period_to:
        query = query.where(HRPayroll.period_to <= period_to)
    query = query.order_by(HRPayroll.created_at.desc()).limit(500)
    result = await db.execute(query)
    items = [{"id": p.id, "employeeId": p.employee_id, "employeeName": f"موظف #{p.employee_id}",
             "period": p.period_from, "periodFrom": p.period_from, "periodTo": p.period_to,
             "basicSalary": p.basic_salary, "allowances": p.total_allowances,
             "overtime": p.overtime, "bonus": p.bonus,
             "deductions": p.deductions, "netSalary": p.net_salary,
             "status": p.status, "paymentDate": p.payment_date}
            for p in result.scalars().all()]
    return {"items": items, "total": len(items)}


@router.post("/payroll/calculate", response_model=dict)
async def calculate_payroll(data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    emp_id = data.get("employee_id")
    emp_result = await db.execute(select(HREmployee).where(HREmployee.id == emp_id))
    emp = emp_result.scalar_one_or_none()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")

    basic = emp.basic_salary or 0
    housing = emp.housing_allowance or 0
    transport = emp.transportation_allowance or 0
    other = emp.other_allowances or 0
    total_allow = housing + transport + other
    overtime = float(data.get("overtime", 0))
    bonus = float(data.get("bonus", 0))
    deductions = float(data.get("deductions", 0))
    net = basic + total_allow + overtime + bonus - deductions

    payroll = HRPayroll(
        employee_id=emp_id, period_from=data.get("period_from", ""),
        period_to=data.get("period_to", ""),
        basic_salary=basic, housing_allowance=housing,
        transportation_allowance=transport, other_allowances=other,
        total_allowances=total_allow, overtime=overtime,
        bonus=bonus, deductions=deductions, net_salary=net,
        notes=data.get("notes"), status="draft",
    )
    db.add(payroll)
    await db.flush()
    return {"id": payroll.id, "net_salary": net, "message": "Payroll calculated"}


@router.put("/payroll/{payroll_id}/status", response_model=MessageResponse)
async def update_payroll_status(payroll_id: int, data: dict, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    values = {"status": new_status}
    if "payment_date" in data:
        values["payment_date"] = data["payment_date"]
    await db.execute(update(HRPayroll).where(HRPayroll.id == payroll_id).values(**values))

    # Emit payroll.approved event when status changes to 'approved'
    if new_status == "approved":
        # Fetch employee details
        emp_result = await db.execute(select(HREmployee).where(HREmployee.id == payroll.employee_id))
        employee = emp_result.scalar_one_or_none()

        if employee:
            # Fetch department name
            dept_name = "Unknown Department"
            if employee.department_id:
                dept_result = await db.execute(select(HRDepartment).where(HRDepartment.id == employee.department_id))
                dept = dept_result.scalar_one_or_none()
                if dept:
                    dept_name = dept.name

            # Parse period dates to extract month/year
            try:
                period_date = datetime.strptime(payroll.period_from, "%Y-%m-%d") if payroll.period_from else datetime.now()
                period_month = period_date.month
                period_year = period_date.year
            except (ValueError, TypeError):
                period_month = datetime.now().month
                period_year = datetime.now().year

            await emit_payroll_approved(
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
                net_salary=float(payroll.net_salary or 0),
                user_id=current_user.id,
            )
            logger.info(f"HR: emitted payroll.approved event for payroll {payroll_id}")

    return MessageResponse(message="Payroll status updated")
