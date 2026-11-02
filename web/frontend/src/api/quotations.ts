import { get, post, put } from './client';
import type { PaginatedResponse, PaginationParams, Quotation } from '@/types';

export async function getQuotations(params: PaginationParams) {
  return await get<PaginatedResponse<Quotation>>('/quotations', params as Record<string, unknown>);
}

export async function getQuotation(id: string) {
  return await get<Quotation>(`/quotations/${id}`);
}

export async function createQuotation(data: Partial<Quotation>) {
  return await post<{ id: number; quotation_number: string; message: string }>('/quotations', data);
}

export async function updateQuotation(id: string, data: Partial<Quotation>) {
  return await put<{ message: string }>(`/quotations/${id}`, data);
}

export async function submitQuotation(id: string) {
  return await post<{ message: string }>(`/quotations/${id}/submit`);
}

export async function acceptQuotation(id: string) {
  return await post<{ message: string }>(`/quotations/${id}/accept`);
}

export async function convertQuotation(id: string) {
  return await post<{ id: number; invoice_number: string; message: string }>(`/quotations/${id}/convert`);
}
