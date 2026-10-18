import { get, post, put } from './client';
import type { PaginatedResponse, Purchase, PaginationParams } from '@/types';

export async function getPurchases(params: PaginationParams) {
  return await get<PaginatedResponse<Purchase>>('/purchases', params as Record<string, unknown>);
}

export async function getPurchase(id: string) {
  return await get<Purchase>(`/purchases/${id}`);
}

export async function createPurchase(data: Partial<Purchase>) {
  return await post<Purchase>('/purchases', data);
}

export async function updatePurchase(id: string, data: Partial<Purchase>) {
  return await put<Purchase>(`/purchases/${id}`, data);
}

export async function submitPurchase(id: string) {
  return await post<Purchase>(`/purchases/${id}/submit`);
}

export async function approvePurchase(id: string) {
  return await post<Purchase>(`/purchases/${id}/approve`);
}
