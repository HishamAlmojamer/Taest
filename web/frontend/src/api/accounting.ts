import { get, post, put } from './client';
import type { Account, JournalEntry, TrialBalanceResponse, PaginationParams } from '@/types';

export async function getAccounts() {
  return await get<{ items: Account[]; total: number }>('/accounting/accounts');
}

export async function createAccount(data: Partial<Account>) {
  return await post<Account>('/accounting/accounts', data);
}

export async function updateAccount(id: string, data: Partial<Account>) {
  return await put<Account>(`/accounting/accounts/${id}`, data);
}

export async function getJournalEntries(params: PaginationParams) {
  return await get<{ items: JournalEntry[]; total: number }>('/accounting/journal-entries', params as Record<string, unknown>);
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

export async function getTrialBalance(params?: { date?: string }) {
  return await get<TrialBalanceResponse>('/accounting/trial-balance', params as Record<string, unknown>);
}
