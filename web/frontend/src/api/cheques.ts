import { get, post, put } from './client';

export interface Cheque {
  id: number;
  cheque_number: string;
  cheque_type: 'received' | 'issued';
  amount: number;
  currency_code: string;
  exchange_rate: number;
  payer_name?: string | null;
  payee_name?: string | null;
  customer_id?: number | null;
  supplier_id?: number | null;
  bank_id?: number | null;
  bank_name?: string | null;
  bank_branch?: string | null;
  issue_date?: string | null;
  due_date?: string | null;
  deposit_date?: string | null;
  clear_date?: string | null;
  status: 'on_hand' | 'deposited' | 'under_collection' | 'cleared' | 'returned' | 'stopped' | 'cancelled' | 'replaced';
  status_reason?: string | null;
  replaced_by_cheque_id?: number | null;
  journal_entry_id?: number | null;
  reversal_entry_id?: number | null;
  reference_type?: string | null;
  reference_id?: number | null;
  description?: string | null;
  created_by?: number | null;
  created_at?: string | null;
  updated_at?: string | null;
  company_id?: number | null;
}

export interface PaginatedCheques {
  items: Cheque[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

export async function getCheques(params?: Record<string, unknown>) {
  return await get<PaginatedCheques>('/cheques', params);
}

export async function getCheque(id: number) {
  return await get<Cheque>(`/cheques/${id}`);
}

export async function createCheque(data: Record<string, unknown>) {
  return await post<{ id: number; cheque_number: string; message: string }>('/cheques', data);
}

export async function updateCheque(id: number, data: Record<string, unknown>) {
  return await put<{ message: string }>(`/cheques/${id}`, data);
}

export async function transitionCheque(id: number, data: Record<string, unknown>) {
  return await post<{ message: string; status: string }>(`/cheques/${id}/transition`, data);
}

export async function bulkDepositCheques(data: { cheque_ids: number[]; bank_id: number }) {
  return await post<{ deposited: number; message: string }>('/cheques/bulk-deposit', data);
}

export async function getChequeSummary() {
  return await get<Record<string, Record<string, number>>>('/cheques/summary/counts');
}