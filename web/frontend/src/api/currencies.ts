import { get, post, put, del } from './client';

// Currency API
export async function getCurrencies() {
  return await get<any[]>('/currencies/currencies');
}

export async function createCurrency(data: any) {
  return await post<any>('/currencies/currencies', data);
}

export async function updateCurrency(id: number, data: any) {
  return await put<any>(`/currencies/currencies/${id}`, data);
}

export async function deleteCurrency(id: number) {
  return await del<any>(`/currencies/currencies/${id}`);
}

// Exchange Rate API
export async function getExchangeRates(from?: string, to?: string) {
  const params: Record<string, string> = {};
  if (from) params.from_currency = from;
  if (to) params.to_currency = to;
  return await get<any[]>('/currencies/exchange-rates', params);
}

export async function createExchangeRate(data: any) {
  return await post<any>('/currencies/exchange-rates', data);
}

export async function convertCurrency(amount: number, from: string, to: string) {
  return await get<any>('/currencies/exchange-rates/convert', { amount, from_currency: from, to_currency: to });
}
