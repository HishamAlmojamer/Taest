import { get, post, put, del } from './client';

// Tax Rate API
export async function getTaxRates(taxType?: string, appliesTo?: string) {
  const params: Record<string, string> = {};
  if (taxType) params.tax_type = taxType;
  if (appliesTo) params.applies_to = appliesTo;
  return await get<any[]>('/taxes/tax-rates', params);
}

export async function getTaxRate(id: number) {
  return await get<any>(`/taxes/tax-rates/${id}`);
}

export async function createTaxRate(data: any) {
  return await post<any>('/taxes/tax-rates', data);
}

export async function updateTaxRate(id: number, data: any) {
  return await put<any>(`/taxes/tax-rates/${id}`, data);
}

export async function deleteTaxRate(id: number) {
  return await del<any>(`/taxes/tax-rates/${id}`);
}

export async function calculateTax(data: { tax_rate_id: number; amount: number }) {
  return await post<any>('/taxes/calculate-tax', data);
}
