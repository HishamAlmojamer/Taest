import { get } from './client';

export async function getSalesReport(params?: Record<string, unknown>) {
  return await get('/reports/sales-summary', params);
}

export async function getPurchasesReport(params?: Record<string, unknown>) {
  return await get('/reports/purchases-summary', params);
}

export async function getFinancialReport(params?: Record<string, unknown>) {
  return await get('/reports/financial-summary', params);
}
