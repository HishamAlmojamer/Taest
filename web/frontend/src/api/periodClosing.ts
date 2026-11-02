import { get, post } from './client';

export interface FiscalPeriod {
  id: number;
  name: string;
  nameEn?: string | null;
  startDate: string;
  endDate: string;
  isClosed: boolean;
  isLocked: boolean;
  isSoftClosed?: boolean;
  fiscalYearId?: number | null;
  closedBy?: number | null;
  closedAt?: string | null;
}

export interface FiscalYear {
  id: number;
  name: string;
  nameEn?: string | null;
  startDate: string;
  endDate: string;
  isClosed: boolean;
  closedBy?: number | null;
  closedAt?: string | null;
  openingBalancesPosted: boolean;
  notes?: string | null;
  createdAt?: string | null;
  periodCount?: number;
  closedPeriodCount?: number;
}

export interface ValidatePeriodResult {
  canClose: boolean;
  issues: string[];
}

export async function getFiscalPeriods(): Promise<FiscalPeriod[]> {
  return get<FiscalPeriod[]>('/period-closing/fiscal-periods');
}

export async function createFiscalPeriod(data: {
  name: string;
  startDate: string;
  endDate: string;
}): Promise<{ id: number; message: string }> {
  return post<{ id: number; message: string }>('/period-closing/fiscal-periods', data);
}

export async function validatePeriodForClosing(periodId: number): Promise<ValidatePeriodResult> {
  return get<ValidatePeriodResult>(`/period-closing/fiscal-periods/${periodId}/validate`);
}

export async function closeFiscalPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/close`);
}

export async function lockFiscalPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/lock`);
}

export async function unlockFiscalPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/unlock`);
}

export async function reopenFiscalPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/reopen`);
}

export async function softCloseFiscalPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/soft-close`);
}

export async function reopenSoftClosedPeriod(periodId: number): Promise<{ message: string }> {
  return post<{ message: string }>(`/period-closing/fiscal-periods/${periodId}/reopen-soft`);
}

// ---- Fiscal Years ----

export async function getFiscalYears(): Promise<FiscalYear[]> {
  return get<FiscalYear[]>('/period-closing/fiscal-years');
}

export async function createFiscalYear(data: {
  name?: string;
  nameEn?: string;
  startDate: string;
  endDate: string;
  notes?: string;
}): Promise<{ id: number; message: string }> {
  return post<{ id: number; message: string }>('/period-closing/fiscal-years', data);
}

export async function generateFiscalPeriods(fiscalYearId: number, periods: number = 12): Promise<{ message: string; created: number }> {
  return post<{ message: string; created: number }>(`/period-closing/fiscal-years/${fiscalYearId}/generate-periods?periods=${periods}`);
}

export async function closeFiscalYear(fiscalYearId: number): Promise<{ message: string; journalEntryId?: number | null; retainedEarnings?: number }> {
  return post<{ message: string; journalEntryId?: number | null; retainedEarnings?: number }>(`/period-closing/fiscal-years/${fiscalYearId}/closing`);
}

export async function openNextFiscalYear(fiscalYearId: number): Promise<{ message: string; journalEntryId?: number | null; lines?: number }> {
  return post<{ message: string; journalEntryId?: number | null; lines?: number }>(`/period-closing/fiscal-years/${fiscalYearId}/open-next-year`);
}
