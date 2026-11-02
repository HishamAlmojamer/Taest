from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Integer, Numeric, Text, Index, DateTime
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
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


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
    advance_deduction: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    net_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRAdvance(Base):
    __tablename__ = "hr_advances"
    __table_args__ = (
        Index("ix_hr_advances_employee", "employee_id"),
        Index("ix_hr_advances_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    advance_type: Mapped[str] = mapped_column(Text, nullable=False, default="advance")
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    installments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    monthly_deduction: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    request_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    payment_method: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    payment_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    journal_entry_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRShift(Base):
    __tablename__ = "hr_shifts"
    __table_args__ = (Index("ix_hr_shifts_code", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_time: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    break_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    working_hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRLeaveType(Base):
    __tablename__ = "hr_leave_types"
    __table_args__ = (Index("ix_hr_leave_types_code", "code"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    name_en: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    days_per_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_paid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    max_consecutive_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    requires_approval: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRLeaveBalance(Base):
    __tablename__ = "hr_leave_balances"
    __table_args__ = (
        Index("ix_hr_leave_balances_emp", "employee_id"),
        Index("ix_hr_leave_balances_year", "year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    leave_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    days_entitled: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    days_used: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    days_remaining: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HROvertime(Base):
    __tablename__ = "hr_overtimes"
    __table_args__ = (
        Index("ix_hr_overtimes_employee", "employee_id"),
        Index("ix_hr_overtimes_date", "date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hours: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    rate_multiplier: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    amount: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRBonus(Base):
    __tablename__ = "hr_bonuses"
    __table_args__ = (
        Index("ix_hr_bonuses_employee", "employee_id"),
        Index("ix_hr_bonuses_period", "period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    bonus_type: Mapped[str] = mapped_column(Text, nullable=False, default="bonus")
    amount: Mapped[float] = mapped_column(Numeric(15, 4), nullable=False)
    period: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRPerformanceReview(Base):
    __tablename__ = "hr_performance_reviews"
    __table_args__ = (Index("ix_hr_reviews_employee", "employee_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reviewer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    review_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    review_period: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    goals_achieved: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strengths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    overall_rating: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    next_review_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRContract(Base):
    __tablename__ = "hr_contracts"
    __table_args__ = (Index("ix_hr_contracts_employee", "employee_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    contract_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    probation_end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    basic_salary: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    allowances: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRResignation(Base):
    __tablename__ = "hr_resignations"
    __table_args__ = (
        Index("ix_hr_resignations_employee", "employee_id"),
        Index("ix_hr_resignations_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    resign_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_working_day: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approved_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRJobPosting(Base):
    __tablename__ = "hr_job_postings"
    __table_args__ = (Index("ix_hr_job_postings_status", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    position_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    department_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    vacancies: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    salary_min: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    salary_max: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    location: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    employment_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    posted_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    deadline: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRCandidate(Base):
    __tablename__ = "hr_candidates"
    __table_args__ = (Index("ix_hr_candidates_job", "job_posting_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_posting_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    applied_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRTraining(Base):
    __tablename__ = "hr_trainings"
    __table_args__ = (Index("ix_hr_trainings_employee", "employee_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    course_name: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    end_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost: Mapped[Optional[float]] = mapped_column(Numeric(15, 4), nullable=True)
    certificate: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HREmployeeDocument(Base):
    __tablename__ = "hr_employee_documents"
    __table_args__ = (Index("ix_hr_documents_employee", "employee_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(Integer, nullable=False)
    document_type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    issue_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    expiry_date: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)


class HRHoliday(Base):
    __tablename__ = "hr_holidays"
    __table_args__ = (Index("ix_hr_holidays_date", "date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[str] = mapped_column(Text, nullable=False)
    is_recurring: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    type: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
