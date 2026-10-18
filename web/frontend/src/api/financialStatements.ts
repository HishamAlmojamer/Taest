import { get, post } from './client';

// Financial Statements API
export async function getBalanceSheet(asOfDate?: string, companyId?: number) {
  const params: Record<string, any> = {};
  if (asOfDate) params.as_of_date = asOfDate;
  if (companyId) params.company_id = companyId;
  return await get<any>('/financial-statements/balance-sheet', params);
}

export async function getIncomeStatement(periodStart?: string, periodEnd?: string, companyId?: number) {
  const params: Record<string, any> = {};
  if (periodStart) params.period_start = periodStart;
  if (periodEnd) params.period_end = periodEnd;
  if (companyId) params.company_id = companyId;
  return await get<any>('/financial-statements/income-statement', params);
}

export async function getCashFlowStatement(periodStart?: string, periodEnd?: string, companyId?: number) {
  const params: Record<string, any> = {};
  if (periodStart) params.period_start = periodStart;
  if (periodEnd) params.period_end = periodEnd;
  if (companyId) params.company_id = companyId;
  return await get<any>('/financial-statements/cash-flow-statement', params);
}

export async function getDetailedTrialBalance(asOfDate?: string, companyId?: number) {
  const params: Record<string, any> = {};
  if (asOfDate) params.as_of_date = asOfDate;
  if (companyId) params.company_id = companyId;
  return await get<any>('/financial-statements/trial-balance-detailed', params);
}
