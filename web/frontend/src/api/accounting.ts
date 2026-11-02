import { get, post, put, del } from './client';
import type { Account, AccountCreateData, JournalEntry, TrialBalanceResponse, PaginationParams } from '@/types';

export async function getAccounts() {
  return await get<{ items: Account[]; total: number }>('/accounting/accounts');
}

export async function getAccountsTree(type?: string) {
  return await get<Account[]>('/accounting/accounts/tree', type ? { type } : undefined);
}

export async function getAccountsFlat(type?: string) {
  return await get<Account[]>('/accounting/accounts/flat', type ? { type } : undefined);
}

export async function getAccount(id: number) {
  return await get<Account & { children: Account[] }>(`/accounting/accounts/${id}`);
}

export async function createAccount(data: AccountCreateData) {
  return await post<Account>('/accounting/accounts', data);
}

export async function updateAccount(id: number, data: Partial<AccountCreateData>) {
  return await put<Account>(`/accounting/accounts/${id}`, data);
}

export async function deleteAccount(id: number) {
  return await del(`/accounting/accounts/${id}`);
}

export async function getJournalEntries(params: PaginationParams) {
  const { page, search, status } = params;
  const perPage = params.perPage ?? (params.pageSize as number | undefined);
  const query: Record<string, unknown> = { page };
  if (perPage) query.per_page = perPage;
  if (search) query.search = search;
  if (status) query.status = status;
  return await get<{ items: JournalEntry[]; total: number }>('/accounting/journal-entries', query);
}

export async function getJournalEntry(id: string) {
  return await get<JournalEntry>(`/accounting/journal-entries/${id}`);
}

export async function createJournalEntry(data: Partial<JournalEntry>) {
  return await post<JournalEntry>('/accounting/journal-entries', data);
}

export async function postJournalEntry(id: string) {
  return await post<JournalEntry>(`/accounting/journal-entries/${id}/post`);
}

export async function reverseJournalEntry(id: string) {
  return await post<JournalEntry>(`/accounting/journal-entries/${id}/void`);
}

export async function getTrialBalance(params?: { date?: string; search?: string; account_type?: string; fiscal_period_id?: number; page?: number; per_page?: number }) {
  return await get<TrialBalanceResponse>('/accounting/trial-balance', params as Record<string, unknown>);
}

export async function getGeneralLedger(params: { account_id: number; from_date?: string; to_date?: string; partner_id?: number; page?: number; per_page?: number }) {
  return await get<import('@/types').GeneralLedgerResponse>('/accounting/general-ledger', params as Record<string, unknown>);
}

export async function updateJournalEntry(id: string, data: Record<string, unknown>) {
  return await put(`/accounting/journal-entries/${id}`, data);
}

export async function deleteJournalEntry(id: string) {
  return await del(`/accounting/journal-entries/${id}`);
}

export async function voidJournalEntry(id: string, reason: string) {
  return await post(`/accounting/journal-entries/${id}/void?reason=${encodeURIComponent(reason)}`);
}

export async function getCostCenters() {
  return await get<import('@/types').CostCenter[]>('/accounting/cost-centers');
}

export async function getCostCenter(id: number) {
  return await get<import('@/types').CostCenter>(`/accounting/cost-centers/${id}`);
}

export async function createCostCenter(data: { code: string; name: string; name_en?: string; parent_id?: number }) {
  return await post('/accounting/cost-centers', data);
}

export async function updateCostCenter(id: number, data: { code: string; name: string; name_en?: string; parent_id?: number }) {
  return await put(`/accounting/cost-centers/${id}`, data);
}

export async function deleteCostCenter(id: number) {
  return await del(`/accounting/cost-centers/${id}`);
}

export async function getRecurringJETemplates() {
  return await get<import('@/types').RecurringJETemplate[]>('/accounting/recurring-je-templates');
}

export async function getRecurringJETemplate(id: number) {
  return await get<import('@/types').RecurringJETemplate>(`/accounting/recurring-je-templates/${id}`);
}

export async function createRecurringJETemplate(data: Record<string, unknown>) {
  return await post('/accounting/recurring-je-templates', data);
}

export async function updateRecurringJETemplate(id: number, data: Record<string, unknown>) {
  return await put(`/accounting/recurring-je-templates/${id}`, data);
}

export async function deleteRecurringJETemplate(id: number) {
  return await del(`/accounting/recurring-je-templates/${id}`);
}

export async function runRecurringJETemplate(id: number) {
  return await post(`/accounting/recurring-je-templates/${id}/run`);
}

export async function previewRecurringJETemplate(id: number) {
  return await post<import('@/types').RecurringJEPreview>(`/accounting/recurring-je-templates/${id}/preview`);
}

export async function toggleRecurringJETemplate(id: number) {
  return await post<{ id: number; is_active: boolean }>(`/accounting/recurring-je-templates/${id}/toggle`);
}

export interface Voucher {
  id: number;
  voucher_type: 'RECEIPT' | 'PAYMENT';
  voucher_number: string;
  voucher_date: string | null;
  partner_type?: string | null;
  partner_id?: number | null;
  amount: number | string;
  payment_method: 'cash' | 'bank';
  bank_id?: number | null;
  reference_number?: string | null;
  description?: string | null;
  status?: string | null;
  journal_entry_id?: number | null;
  reversal_entry_id?: number | null;
  void_reason?: string | null;
  company_id?: number | null;
  created_at?: string | null;
}

export async function getVouchers(params?: Record<string, unknown>) {
  return await get<{ items: Voucher[]; total: number; page: number; per_page: number; pages: number }>(
    '/accounting/vouchers',
    params,
  );
}

export async function getVoucher(id: number) {
  return await get<Voucher>(`/accounting/vouchers/${id}`);
}

export async function createVoucher(data: Record<string, unknown>) {
  return await post<{ message: string; voucher: Voucher; journal_entry_id: number }>('/accounting/vouchers', data);
}

export async function voidVoucher(id: number, reason: string) {
  return await post(`/accounting/vouchers/${id}/void?reason=${encodeURIComponent(reason)}`);
}
