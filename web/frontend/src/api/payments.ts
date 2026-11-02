import { get, post, put } from './client';
import type { PaginatedResponse } from '@/types';

export interface CustomerPayment {
  id: number;
  customer_id: number;
  customer_name?: string;
  amount: number;
  payment_method: string;
  payment_date?: string;
  reference_number?: string;
  bank_id?: number;
  bank_name?: string;
  notes?: string;
  currency_code: string;
  journal_entry_id?: number;
  created_by?: number;
  created_at?: string;
}

export interface SupplierPayment {
  id: number;
  supplier_id: number;
  supplier_name?: string;
  amount: number;
  payment_method: string;
  payment_date?: string;
  reference_number?: string;
  bank_id?: number;
  bank_name?: string;
  notes?: string;
  currency_code: string;
  journal_entry_id?: number;
  created_by?: number;
  created_at?: string;
}

export interface Bank {
  id: number;
  name: string;
  bank_name?: string;
  name_ar?: string;
  code?: string;
  account_number?: string;
  accountNumber?: string;
  account_name?: string;
  iban?: string;
  currency_code: string;
  currency?: string;
  current_balance: number;
  balance?: number;
  opening_balance: number;
  is_active: boolean;
  isActive?: boolean;
  notes?: string;
  created_at?: string;
}

export interface BankTransaction {
  id: number;
  bank_id: number;
  transaction_type: string;
  amount: number;
  balance_after?: number;
  transaction_date?: string;
  reference_number?: string;
  description?: string;
  reconciled: boolean;
  created_at?: string;
}

export async function getCustomerPayments(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<CustomerPayment>>('/payments/customers', params);
}

export async function createCustomerPayment(data: Omit<CustomerPayment, 'id' | 'created_at' | 'customer_name' | 'bank_name'>) {
  return await post<{ id: number; message: string }>('/payments/customers', data);
}

export async function getSupplierPayments(params?: Record<string, unknown>) {
  return await get<PaginatedResponse<SupplierPayment>>('/payments/suppliers', params);
}

export async function createSupplierPayment(data: Omit<SupplierPayment, 'id' | 'created_at' | 'supplier_name' | 'bank_name'>) {
  return await post<{ id: number; message: string }>('/payments/suppliers', data);
}

export async function getBanks() {
  return await get<{ items: Bank[]; total: number }>('/payments/banks');
}

export async function createBank(data: Omit<Bank, 'id' | 'created_at' | 'current_balance'>) {
  return await post<{ id: number; message: string }>('/payments/banks', data);
}

export async function updateBank(bankId: string, data: Partial<Bank>) {
  return await put<{ message: string }>(`/payments/banks/${bankId}`, data);
}

export async function getBankTransactions(bankId: string, params?: Record<string, unknown>) {
  return await get<PaginatedResponse<BankTransaction>>(`/payments/banks/${bankId}/transactions`, params);
}

export async function createBankTransaction(bankId: string, data: Omit<BankTransaction, 'id' | 'created_at' | 'balance_after'>) {
  return await post<{ id: number; message: string }>(`/payments/banks/${bankId}/transactions`, data);
}
