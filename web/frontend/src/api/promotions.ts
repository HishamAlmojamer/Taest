import { get, post, put, del } from './client';
import type { PaginatedResponse, PaginationParams, Promotion } from '@/types';

export async function getPromotions(params: PaginationParams = {}) {
  return await get<PaginatedResponse<Promotion>>('/promotions', {
    page: params.page || 1,
    per_page: params.pageSize || 50,
    search: params.search,
  });
}

export async function getPromotion(id: string | number) {
  return await get<Promotion>(`/promotions/${id}`);
}

export async function createPromotion(data: Partial<Promotion>) {
  return await post<{ id: number; message: string }>('/promotions', data);
}

export async function updatePromotion(id: string | number, data: Partial<Promotion>) {
  return await put<{ message: string }>(`/promotions/${id}`, data);
}

export async function togglePromotion(id: string | number) {
  return await post<{ message: string; is_active: boolean }>(`/promotions/${id}/toggle`);
}

export async function deletePromotion(id: string | number) {
  return await del<{ message: string }>(`/promotions/${id}`);
}