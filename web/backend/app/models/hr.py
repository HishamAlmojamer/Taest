from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class HRDepartment(Base):
    __tablename__ = "hr_departments"
    __table_args__ = (Index("ix_hr_departments_code", "code"), Index("ix_hr_departments_manager", "manager_id"))

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HRPosition(Base):
    __tablename__ = "hr_positions"
    __table_args__ = (Index("ix_hr_positions_dept", "department_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    min_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    max_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HREmployee(Base):
    __tablename__ = "hr_employees"
    __table_args__ = (
        Index("ix_hr_employees_dept", "department_id"),
        Index("ix_hr_employees_position", "position_id"),
        Index("ix_hr_employees_status", "employment_status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    mobile: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gender: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    birth_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    nationality: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    marital_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    position_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    manager_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    hire_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employment_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    salary_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    basic_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    housing_allowance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    transportation_allowance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    other_allowances: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    iban: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_expiry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passport_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    passport_expiry: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    health_insurance_provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    health_insurance_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HRAttendance(Base):
    __tablename__ = "hr_attendance"
    __table_args__ = (
        Index("ix_hr_attendance_employee", "employee_id"),
        Index("ix_hr_attendance_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    check_in: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    check_out: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HRLeave(Base):
    __tablename__ = "hr_leaves"
    __table_args__ = (
        Index("ix_hr_leaves_employee", "employee_id"),
        Index("ix_hr_leaves_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    leave_type: Mapped[str] = mapped_column(Text, nullable=False)
    start_date: Mapped[str] = mapped_column(Text, nullable=False)
    end_date: Mapped[str] = mapped_column(Text, nullable=False)
    days_count: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class HRPayroll(Base):
    __tablename__ = "hr_payroll"
    __table_args__ = (
        Index("ix_hr_payroll_employee", "employee_id"),
        Index("ix_hr_payroll_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    period_from: Mapped[str] = mapped_column(Text, nullable=False)
    period_to: Mapped[str] = mapped_column(Text, nullable=False)
    basic_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    housing_allowance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    transportation_allowance: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    other_allowances: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    total_allowances: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    overtime: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    bonus: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    deductions: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    net_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
