import { get, post, put } from './client';
import type { PaginatedResponse, HREmployee, HRDepartment, HRAttendance, HRLeave, HRPayroll, PaginationParams } from '@/types';

export async function getEmployees(params: PaginationParams) {
  return await get<PaginatedResponse<HREmployee>>('/hr/employees', params as Record<string, unknown>);
}

export async function getEmployee(id: string) {
  return await get<HREmployee>(`/hr/employees/${id}`);
}

export async function createEmployee(data: Partial<HREmployee>) {
  return await post<HREmployee>('/hr/employees', data);
}

export async function updateEmployee(id: string, data: Partial<HREmployee>) {
  return await put<HREmployee>(`/hr/employees/${id}`, data);
}

export async function getDepartments() {
  return await get<{ items: HRDepartment[]; total: number }>('/hr/departments');
}

export async function getPositions(params?: PaginationParams) {
  return await get<{ items: Array<{ id: number; name: string; code?: string }>; total: number }>('/hr/positions', params as Record<string, unknown>);
}

export async function createDepartment(data: Partial<HRDepartment>) {
  return await post<HRDepartment>('/hr/departments', data);
}

export async function updateDepartment(id: string, data: Partial<HRDepartment>) {
  return await put<HRDepartment>(`/hr/departments/${id}`, data);
}

export async function getAttendance(params: PaginationParams) {
  return await get<{ items: HRAttendance[]; total: number }>('/hr/attendance', params as Record<string, unknown>);
}

export async function createAttendance(data: Partial<HRAttendance>) {
  return await post<HRAttendance>('/hr/attendance', data);
}

export async function getLeaves(params: PaginationParams) {
  return await get<{ items: HRLeave[]; total: number }>('/hr/leaves', params as Record<string, unknown>);
}

export async function createLeave(data: Partial<HRLeave>) {
  return await post<HRLeave>('/hr/leaves', data);
}

export async function approveLeave(id: string) {
  return await put<HRLeave>(`/hr/leaves/${id}/status`, { status: 'approved' });
}

export async function rejectLeave(id: string) {
  return await put<HRLeave>(`/hr/leaves/${id}/status`, { status: 'rejected' });
}

export async function getPayroll(params: PaginationParams) {
  return await get<{ items: HRPayroll[]; total: number }>('/hr/payroll', params as Record<string, unknown>);
}

export async function processPayroll(data: { period: string }) {
  return await post<HRPayroll[]>('/hr/payroll/calculate', data);
}
