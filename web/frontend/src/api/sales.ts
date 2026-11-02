import { get, post, put } from './client';
import type { PaginatedResponse, Sale, PaginationParams } from '@/types';

export interface DailyReportData {
  totalSales: number;
  totalInvoices: number;
  totalCustomers: number;
  salesByHour: { hour: number; amount: number }[];
  recentSales: Sale[];
  paymentMethods: { name: string; value: number }[];
  approvalPending: number;
  vsYesterday?: { sales: number; invoices: number; customers: number } | null;
}

export async function getDailyReport(date: string) {
  return await get<DailyReportData>('/reports/sales-summary', { date });
}

export async function getSales(params: PaginationParams) {
  return await get<PaginatedResponse<Sale>>('/sales', params as Record<string, unknown>);
}

export async function getSale(id: string) {
  return await get<Sale>(`/sales/${id}`);
}

export async function createSale(data: Partial<Sale>) {
  return await post<Sale>('/sales', data);
}

export async function updateSale(id: string, data: Partial<Sale>) {
  return await put<Sale>(`/sales/${id}`, data);
}

export async function submitSale(id: string) {
  return await post<Sale>(`/sales/${id}/submit`);
}

export async function approveSale(id: string) {
  return await post<Sale>(`/sales/${id}/approve`);
}

export async function rejectSale(id: string) {
  return await post<Sale>(`/sales/${id}/reject`);
}
