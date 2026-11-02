from typing import Optional
from pydantic import BaseModel, ConfigDict


class HRDepartmentCreate(BaseModel):
    code: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    parent_id: Optional[int] = None


class HRDepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    description: Optional[str] = None
    manager_id: Optional[int] = None
    managerName: Optional[str] = None
    parent_id: Optional[int] = None
    employeeCount: int = 0
    is_active: bool = True
    created_at: Optional[str] = None


class HRPositionCreate(BaseModel):
    code: str
    name: str
    name_en: Optional[str] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    min_salary: Optional[float] = 0
    max_salary: Optional[float] = 0


class HRPositionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    name_en: Optional[str] = None
    department_id: Optional[int] = None
    description: Optional[str] = None
    min_salary: Optional[float] = 0
    max_salary: Optional[float] = 0
    is_active: bool = True
    created_at: Optional[str] = None


class HREmployeeCreate(BaseModel):
    code: str
    full_name: str
    full_name_en: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    department_id: Optional[int] = None
    position_id: Optional[int] = None
    manager_id: Optional[int] = None
    hire_date: Optional[str] = None
    employment_status: Optional[str] = "نشط"
    salary_type: Optional[str] = "شهري"
    basic_salary: Optional[float] = 0
    housing_allowance: Optional[float] = 0
    transportation_allowance: Optional[float] = 0
    other_allowances: Optional[float] = 0
    total_salary: Optional[float] = 0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    iban: Optional[str] = None
    id_type: Optional[str] = "هوية وطنية"
    id_number: Optional[str] = None
    id_expiry: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    health_insurance_provider: Optional[str] = None
    health_insurance_number: Optional[str] = None
    notes: Optional[str] = None


class HREmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    full_name: str
    full_name_en: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    address: Optional[str] = None
    gender: Optional[str] = None
    birth_date: Optional[str] = None
    nationality: Optional[str] = None
    marital_status: Optional[str] = None
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    position_id: Optional[int] = None
    position_name: Optional[str] = None
    manager_id: Optional[int] = None
    manager_name: Optional[str] = None
    hire_date: Optional[str] = None
    employment_status: Optional[str] = None
    salary_type: Optional[str] = None
    basic_salary: float = 0
    housing_allowance: float = 0
    transportation_allowance: float = 0
    other_allowances: float = 0
    total_salary: float = 0
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    iban: Optional[str] = None
    id_type: Optional[str] = None
    id_number: Optional[str] = None
    id_expiry: Optional[str] = None
    passport_number: Optional[str] = None
    passport_expiry: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    health_insurance_provider: Optional[str] = None
    health_insurance_number: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class HRAttendanceCreate(BaseModel):
    employee_id: int
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = "حاضر"
    notes: Optional[str] = None


class HRAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    date: str
    check_in: Optional[str] = None
    check_out: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


class HRLeaveCreate(BaseModel):
    employee_id: int
    leave_type: str
    start_date: str
    end_date: str
    days_count: int
    reason: Optional[str] = None


class HRLeaveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    leave_type: str
    start_date: str
    end_date: str
    days_count: int
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    approved_by: Optional[int] = None
    created_at: Optional[str] = None


class HRPayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    period_from: str
    period_to: str
    basic_salary: float = 0
    housing_allowance: float = 0
    transportation_allowance: float = 0
    other_allowances: float = 0
    total_allowances: float = 0
    overtime: float = 0
    bonus: float = 0
    deductions: float = 0
    advance_deduction: float = 0
    net_salary: float = 0
    status: Optional[str] = "draft"
    payment_date: Optional[str] = None
    payment_method: Optional[str] = None
    journal_entry_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


class HRPayrollPayRequest(BaseModel):
    payment_method: str = "BANK"
    bank_account_id: Optional[int] = None
    bank_account_name: Optional[str] = None
    payment_date: Optional[str] = None


class HRAdvanceCreate(BaseModel):
    employee_id: int
    advance_type: str = "advance"
    amount: float
    installments: Optional[int] = 1
    monthly_deduction: Optional[float] = 0
    request_date: Optional[str] = None
    reason: Optional[str] = None
    payment_method: str = "BANK"
    bank_account_id: Optional[int] = None
    bank_account_name: Optional[str] = None
    notes: Optional[str] = None


class HRAdvanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: int
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None
    advance_type: str = "advance"
    amount: float = 0
    installments: Optional[int] = 1
    monthly_deduction: Optional[float] = 0
    request_date: Optional[str] = None
    reason: Optional[str] = None
    status: Optional[str] = "pending"
    approved_by: Optional[int] = None
    payment_method: Optional[str] = None
    payment_date: Optional[str] = None
    journal_entry_id: Optional[int] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None
