import { get, post } from './client';

// AR/AP Aging Reports API
export async function getARAging(asOfDate?: string) {
  const params: Record<string, any> = {};
  if (asOfDate) params.as_of_date = asOfDate;
  return await get<any>('/aging-reports/ar-aging', params);
}

export async function getAPAging(asOfDate?: string) {
  const params: Record<string, any> = {};
  if (asOfDate) params.as_of_date = asOfDate;
  return await get<any>('/aging-reports/ap-aging', params);
}

export async function getCustomerStatement(customerId: number, startDate?: string, endDate?: string) {
  const params: Record<string, any> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return await get<any>(`/aging-reports/customer-statement/${customerId}`, params);
}

export async function getSupplierStatement(supplierId: number, startDate?: string, endDate?: string) {
  const params: Record<string, any> = {};
  if (startDate) params.start_date = startDate;
  if (endDate) params.end_date = endDate;
  return await get<any>(`/aging-reports/supplier-statement/${supplierId}`, params);
}

export async function getDebtorsCreditors(asOfDate?: string) {
  const params: Record<string, any> = {};
  if (asOfDate) params.as_of_date = asOfDate;
  return await get<any>('/aging-reports/debtors-creditors', params);
}
