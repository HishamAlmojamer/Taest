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

export async function getEquityChanges(fromDate: string, toDate: string) {
  return await get('/financial-statements/equity-changes', { from_date: fromDate, to_date: toDate });
}

export async function getComparativeStatement(reportType: string, p1From: string, p1To: string, p2From: string, p2To: string) {
  return await get('/financial-statements/comparative', {
    report_type: reportType, period1_from: p1From, period1_to: p1To, period2_from: p2From, period2_to: p2To,
  });
}
