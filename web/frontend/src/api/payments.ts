import { get, post } from './client';
import type { PaginatedResponse } from '@/types';

export async function getCustomerPayments(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<unknown>>('/payments/customers', params);
}

export async function createCustomerPayment(data: unknown) {
  return await post('/payments/customers', data);
}

export async function getSupplierPayments(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<unknown>>('/payments/suppliers', params);
}

export async function createSupplierPayment(data: unknown) {
  return await post('/payments/suppliers', data);
}

export async function getBanks() {
  return await get('/payments/banks');
}

export async function createBank(data: unknown) {
  return await post('/payments/banks', data);
}

export async function getBankTransactions(bankId: string, params?: Record<string, unknown>) {
  return await get(`/payments/banks/${bankId}/transactions`, params);
}
