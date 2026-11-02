import { get, post, put, del } from './client';
import type {
  PaginatedResponse,
  HREmployee,
  HRDepartment,
  HRPosition,
  HRAttendance,
  HRLeave,
  HRPayroll,
  HRAdvance,
  HRShift,
  HRLeaveType,
  HRLeaveBalance,
  HROvertime,
  HRBonus,
  HRPerformanceReview,
  HRContract,
  HRResignation,
  HRJobPosting,
  HRCandidate,
  HRTraining,
  HRDocument,
  HRHoliday,
  HRReportsSummary,
  PaginationParams,
} from '@/types';

export async function getEmployees(params?: PaginationParams) {
  return await get<PaginatedResponse<HREmployee>>('/hr/employees', params as Record<string, unknown>);
}

export async function getEmployee(id: number) {
  return await get<HREmployee>(`/hr/employees/${id}`);
}

export async function createEmployee(data: Partial<HREmployee>) {
  return await post<{ id: number; message: string }>('/hr/employees', data);
}

export async function updateEmployee(id: number, data: Partial<HREmployee>) {
  return await put<{ message: string }>(`/hr/employees/${id}`, data);
}

export async function deleteEmployee(id: number) {
  return await del<{ message: string }>(`/hr/employees/${id}`);
}

export async function getDepartments() {
  return await get<{ items: HRDepartment[]; total: number }>('/hr/departments');
}

export async function getDepartmentTree() {
  return await get<{ items: HRDepartment[]; total: number }>('/hr/departments/tree');
}

export async function createDepartment(data: Partial<HRDepartment>) {
  return await post<{ id: number; message: string }>('/hr/departments', data);
}

export async function updateDepartment(id: number, data: Partial<HRDepartment>) {
  return await put<{ message: string }>(`/hr/departments/${id}`, data);
}

export async function deleteDepartment(id: number) {
  return await del<{ message: string }>(`/hr/departments/${id}`);
}

export async function getPositions(params?: PaginationParams) {
  return await get<{ items: HRPosition[]; total: number }>('/hr/positions', params as Record<string, unknown>);
}

export async function getPositionTree() {
  return await get<{ items: HRPosition[]; total: number }>('/hr/positions');
}

export async function createPosition(data: { code: string; name: string; nameEn?: string; departmentId?: number; description?: string; minSalary?: number; maxSalary?: number }) {
  return await post<{ id: number; message: string }>('/hr/positions', data);
}

export async function updatePosition(id: number, data: { code?: string; name?: string; nameEn?: string; departmentId?: number; description?: string; minSalary?: number; maxSalary?: number }) {
  return await put<{ message: string }>(`/hr/positions/${id}`, data);
}

export async function deletePosition(id: number) {
  return await del<{ message: string }>(`/hr/positions/${id}`);
}

export async function getAttendance(params?: PaginationParams) {
  return await get<PaginatedResponse<HRAttendance>>('/hr/attendance', params as Record<string, unknown>);
}

export async function createAttendance(data: Partial<HRAttendance>) {
  return await post<{ id: number; message: string }>('/hr/attendance', data);
}

export async function updateAttendance(id: number, data: Partial<HRAttendance>) {
  return await put<{ message: string }>(`/hr/attendance/${id}`, data);
}

export async function deleteAttendance(id: number) {
  return await del<{ message: string }>(`/hr/attendance/${id}`);
}

export async function getLeaves(params?: PaginationParams) {
  return await get<{ items: HRLeave[]; total: number }>('/hr/leaves', params as Record<string, unknown>);
}

export async function createLeave(data: Partial<HRLeave>) {
  return await post<{ id: number; message: string }>('/hr/leaves', data);
}

export async function approveLeave(id: number) {
  return await put<{ message: string }>(`/hr/leaves/${id}/status`, { status: 'approved' });
}

export async function rejectLeave(id: number) {
  return await put<{ message: string }>(`/hr/leaves/${id}/status`, { status: 'rejected' });
}

export async function getPayroll(params?: PaginationParams) {
  return await get<{ items: HRPayroll[]; total: number }>('/hr/payroll', params as Record<string, unknown>);
}

export async function calculatePayroll(data: { employee_id: number; period_from: string; period_to: string }) {
  return await post<{ id: number; net_salary: number; message: string }>('/hr/payroll/calculate', data);
}

export async function calculateBulkPayroll(data: { period_from: string; period_to: string; department_id?: number }) {
  return await post<{ message: string; items: Array<{ employee_id: number; employee_name: string; net_salary: number }> }>('/hr/payroll/calculate-bulk', data);
}

export async function updatePayrollStatus(id: number, status: string) {
  return await put<{ message: string }>(`/hr/payroll/${id}/status`, { status });
}

export async function approvePayroll(id: number) {
  return await updatePayrollStatus(id, 'approved');
}

export async function voidPayroll(id: number) {
  return await updatePayrollStatus(id, 'voided');
}

export async function payPayroll(
  id: number,
  data: {
    payment_method?: string;
    bank_account_id?: number;
    bank_account_name?: string;
    payment_date?: string;
  } = {},
) {
  return await put<{ message: string }>(`/hr/payroll/${id}/status`, { status: 'paid', ...data });
}

export async function getAdvances(params?: PaginationParams) {
  return await get<{ items: HRAdvance[]; total: number }>('/hr/advances', params as Record<string, unknown>);
}

export async function createAdvance(data: Partial<HRAdvance>) {
  return await post<{ id: number; monthly_deduction: number; message: string }>('/hr/advances', data);
}

export async function updateAdvance(id: number, data: Partial<HRAdvance>) {
  return await put<{ message: string }>(`/hr/advances/${id}`, data);
}

export async function updateAdvanceStatus(id: number, data: { status: string; reason?: string }) {
  return await put<{ message: string }>(`/hr/advances/${id}/status`, data);
}

export async function approveAdvance(id: number) {
  return await updateAdvanceStatus(id, { status: 'approved' });
}

export async function payAdvance(id: number) {
  return await updateAdvanceStatus(id, { status: 'paid' });
}

export async function voidAdvance(id: number) {
  return await updateAdvanceStatus(id, { status: 'voided' });
}

export async function deleteAdvance(id: number) {
  return await del<{ message: string }>(`/hr/advances/${id}`);
}

// ── Shifts (الورديات) ─────────────────────────────────────────

export async function getShifts() {
  return await get<{ items: HRShift[]; total: number }>('/hr/shifts');
}

export async function createShift(data: Partial<HRShift>) {
  return await post<{ id: number; message: string }>('/hr/shifts', data);
}

export async function updateShift(id: number, data: Partial<HRShift>) {
  return await put<{ message: string }>(`/hr/shifts/${id}`, data);
}

export async function deleteShift(id: number) {
  return await del<{ message: string }>(`/hr/shifts/${id}`);
}

// ── Leave Types & Balances (أنواع الإجازات وأرصدتها) ──────────

export async function getLeaveTypes() {
  return await get<{ items: HRLeaveType[]; total: number }>('/hr/leave-types');
}

export async function createLeaveType(data: Partial<HRLeaveType>) {
  return await post<{ id: number; message: string }>('/hr/leave-types', data);
}

export async function updateLeaveType(id: number, data: Partial<HRLeaveType>) {
  return await put<{ message: string }>(`/hr/leave-types/${id}`, data);
}

export async function deleteLeaveType(id: number) {
  return await del<{ message: string }>(`/hr/leave-types/${id}`);
}

export async function getLeaveBalances(params?: { employee_id?: number; year?: number }) {
  return await get<{ items: HRLeaveBalance[]; total: number }>('/hr/leave-balances', params as Record<string, unknown>);
}

export async function initLeaveBalances(year: number) {
  return await post<{ message: string; created: number }>('/hr/leave-balances/init', { year });
}

export async function updateLeaveBalance(id: number, data: Partial<HRLeaveBalance>) {
  return await put<{ message: string }>(`/hr/leave-balances/${id}`, data);
}

// ── Overtime (العمل الإضافي) ─────────────────────────────────

export async function getOvertime(params?: PaginationParams) {
  return await get<PaginatedResponse<HROvertime>>('/hr/overtime', params as Record<string, unknown>);
}

export async function createOvertime(data: Partial<HROvertime>) {
  return await post<{ id: number; amount: number; message: string }>('/hr/overtime', data);
}

export async function updateOvertime(id: number, data: Partial<HROvertime>) {
  return await put<{ message: string }>(`/hr/overtime/${id}`, data);
}

export async function updateOvertimeStatus(id: number, status: string) {
  return await put<{ message: string }>(`/hr/overtime/${id}/status`, { status });
}

export async function approveOvertime(id: number) {
  return await updateOvertimeStatus(id, 'approved');
}

export async function deleteOvertime(id: number) {
  return await del<{ message: string }>(`/hr/overtime/${id}`);
}

// ── Bonuses & Deductions (مكافآت وخصومات) ─────────────────────

export async function getBonuses(params?: PaginationParams) {
  return await get<PaginatedResponse<HRBonus>>('/hr/bonuses', params as Record<string, unknown>);
}

export async function createBonus(data: Partial<HRBonus>) {
  return await post<{ id: number; message: string }>('/hr/bonuses', data);
}

export async function updateBonus(id: number, data: Partial<HRBonus>) {
  return await put<{ message: string }>(`/hr/bonuses/${id}`, data);
}

export async function updateBonusStatus(id: number, status: string) {
  return await put<{ message: string }>(`/hr/bonuses/${id}/status`, { status });
}

export async function approveBonus(id: number) {
  return await updateBonusStatus(id, 'approved');
}

export async function deleteBonus(id: number) {
  return await del<{ message: string }>(`/hr/bonuses/${id}`);
}

// ── Performance Reviews (تقييم الأداء) ────────────────────────

export async function getPerformanceReviews(params?: PaginationParams) {
  return await get<PaginatedResponse<HRPerformanceReview>>('/hr/performance-reviews', params as Record<string, unknown>);
}

export async function createPerformanceReview(data: Partial<HRPerformanceReview>) {
  return await post<{ id: number; message: string }>('/hr/performance-reviews', data);
}

export async function updatePerformanceReview(id: number, data: Partial<HRPerformanceReview>) {
  return await put<{ message: string }>(`/hr/performance-reviews/${id}`, data);
}

export async function deletePerformanceReview(id: number) {
  return await del<{ message: string }>(`/hr/performance-reviews/${id}`);
}

// ── Contracts (العقود) ───────────────────────────────────────

export async function getContracts(params?: PaginationParams) {
  return await get<PaginatedResponse<HRContract>>('/hr/contracts', params as Record<string, unknown>);
}

export async function createContract(data: Partial<HRContract>) {
  return await post<{ id: number; message: string }>('/hr/contracts', data);
}

export async function updateContract(id: number, data: Partial<HRContract>) {
  return await put<{ message: string }>(`/hr/contracts/${id}`, data);
}

export async function deleteContract(id: number) {
  return await del<{ message: string }>(`/hr/contracts/${id}`);
}

// ── Resignations (الاستقالات وإنهاء الخدمة) ──────────────────

export async function getResignations(params?: PaginationParams) {
  return await get<PaginatedResponse<HRResignation>>('/hr/resignations', params as Record<string, unknown>);
}

export async function createResignation(data: Partial<HRResignation>) {
  return await post<{ id: number; message: string }>('/hr/resignations', data);
}

export async function updateResignationStatus(id: number, data: { status: string; notes?: string }) {
  return await put<{ message: string }>(`/hr/resignations/${id}/status`, data);
}

export async function approveResignation(id: number) {
  return await updateResignationStatus(id, { status: 'approved' });
}

export async function rejectResignation(id: number) {
  return await updateResignationStatus(id, { status: 'rejected' });
}

export async function deleteResignation(id: number) {
  return await del<{ message: string }>(`/hr/resignations/${id}`);
}

// ── Recruitment (التوظيف) ────────────────────────────────────

export async function getJobPostings(params?: PaginationParams) {
  return await get<PaginatedResponse<HRJobPosting>>('/hr/job-postings', params as Record<string, unknown>);
}

export async function createJobPosting(data: Partial<HRJobPosting>) {
  return await post<{ id: number; message: string }>('/hr/job-postings', data);
}

export async function updateJobPosting(id: number, data: Partial<HRJobPosting>) {
  return await put<{ message: string }>(`/hr/job-postings/${id}`, data);
}

export async function deleteJobPosting(id: number) {
  return await del<{ message: string }>(`/hr/job-postings/${id}`);
}

export async function getCandidates(params?: PaginationParams) {
  return await get<PaginatedResponse<HRCandidate>>('/hr/candidates', params as Record<string, unknown>);
}

export async function createCandidate(data: Partial<HRCandidate>) {
  return await post<{ id: number; message: string }>('/hr/candidates', data);
}

export async function updateCandidate(id: number, data: Partial<HRCandidate>) {
  return await put<{ message: string }>(`/hr/candidates/${id}`, data);
}

export async function deleteCandidate(id: number) {
  return await del<{ message: string }>(`/hr/candidates/${id}`);
}

// ── Training (التدريب والتطوير) ──────────────────────────────

export async function getTraining(params?: PaginationParams) {
  return await get<PaginatedResponse<HRTraining>>('/hr/training', params as Record<string, unknown>);
}

export async function createTraining(data: Partial<HRTraining>) {
  return await post<{ id: number; message: string }>('/hr/training', data);
}

export async function updateTraining(id: number, data: Partial<HRTraining>) {
  return await put<{ message: string }>(`/hr/training/${id}`, data);
}

export async function deleteTraining(id: number) {
  return await del<{ message: string }>(`/hr/training/${id}`);
}

// ── Employee Documents (مستندات الموظفين) ────────────────────

export async function getDocuments(params?: PaginationParams) {
  return await get<PaginatedResponse<HRDocument>>('/hr/documents', params as Record<string, unknown>);
}

export async function createDocument(data: Partial<HRDocument>) {
  return await post<{ id: number; message: string }>('/hr/documents', data);
}

export async function updateDocument(id: number, data: Partial<HRDocument>) {
  return await put<{ message: string }>(`/hr/documents/${id}`, data);
}

export async function deleteDocument(id: number) {
  return await del<{ message: string }>(`/hr/documents/${id}`);
}

// ── Holidays (الإجازات الرسمية) ──────────────────────────────

export async function getHolidays(params?: { year?: number }) {
  return await get<{ items: HRHoliday[]; total: number }>('/hr/holidays', params as Record<string, unknown>);
}

export async function createHoliday(data: Partial<HRHoliday>) {
  return await post<{ id: number; message: string }>('/hr/holidays', data);
}

export async function updateHoliday(id: number, data: Partial<HRHoliday>) {
  return await put<{ message: string }>(`/hr/holidays/${id}`, data);
}

export async function deleteHoliday(id: number) {
  return await del<{ message: string }>(`/hr/holidays/${id}`);
}

// ── HR Reports (تقارير الموارد البشرية) ──────────────────────

export async function getHRReportSummary(params?: { year?: number }) {
  return await get<HRReportsSummary>('/hr/reports/summary', params as Record<string, unknown>);
}
