import { get, post, put } from './client';

// Budget API
export async function getBudgets(fiscalPeriodId?: number, accountId?: number) {
  const params: Record<string, any> = {};
  if (fiscalPeriodId) params.fiscal_period_id = fiscalPeriodId;
  if (accountId) params.account_id = accountId;
  return await get<any[]>('/budgets/', params);
}

export async function createBudget(data: any) {
  return await post<any>('/budgets/', data);
}

export async function updateBudget(id: number, data: any) {
  return await put<any>(`/budgets/${id}`, data);
}

export async function approveBudget(id: number) {
  return await post<any>(`/budgets/${id}/approve`);
}

export async function getBudgetVsActual(fiscalPeriodId: number, companyId?: number) {
  const params: Record<string, any> = { fiscal_period_id: fiscalPeriodId };
  if (companyId) params.company_id = companyId;
  return await get<any>('/budgets/vs-actual', params);
}

export async function getBudgetAlerts(thresholdPercent?: number) {
  const params: Record<string, any> = {};
  if (thresholdPercent) params.threshold_percent = thresholdPercent;
  return await get<any>('/budgets/alerts', params);
}
