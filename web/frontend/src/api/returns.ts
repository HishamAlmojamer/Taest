import { get, post } from './client';
import type { PaginatedResponse, PaginationParams, SaleReturn, PurchaseReturn } from '@/types';

// ── Sales Returns ─────────────────────────────

export async function getSalesReturns(params: PaginationParams) {
  return await get<PaginatedResponse<SaleReturn>>('/returns/sales', params as Record<string, unknown>);
}

export async function getSalesReturn(id: string) {
  return await get<SaleReturn>(`/returns/sales/${id}`);
}

export async function createSalesReturn(data: Partial<SaleReturn>) {
  return await post<{ id: number; return_number: string; message: string }>('/returns/sales', data);
}

export async function approveSalesReturn(id: string) {
  return await post<{ message: string }>(`/returns/sales/${id}/approve`);
}

export async function voidSalesReturn(id: string, reason?: string) {
  return await post<{ message: string }>(`/returns/sales/${id}/void`, { reason });
}

// ── Purchase Returns ──────────────────────────

export async function getPurchaseReturns(params: PaginationParams) {
  return await get<PaginatedResponse<PurchaseReturn>>('/returns/purchases', params as Record<string, unknown>);
}

export async function getPurchaseReturn(id: string) {
  return await get<PurchaseReturn>(`/returns/purchases/${id}`);
}

export async function createPurchaseReturn(data: Partial<PurchaseReturn>) {
  return await post<{ id: number; return_number: string; message: string }>('/returns/purchases', data);
}

export async function approvePurchaseReturn(id: string) {
  return await post<{ message: string }>(`/returns/purchases/${id}/approve`);
}

export async function voidPurchaseReturn(id: string, reason?: string) {
  return await post<{ message: string }>(`/returns/purchases/${id}/void`, { reason });
}
