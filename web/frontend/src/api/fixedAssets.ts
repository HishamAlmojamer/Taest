import { get, post, put } from './client';

// Fixed Assets API
export async function getFixedAssets(categoryId?: number, status?: string) {
  const params: Record<string, any> = {};
  if (categoryId) params.category_id = categoryId;
  if (status) params.status = status;
  return await get<any[]>('/fixed-assets/', params);
}

export async function getFixedAsset(id: number) {
  return await get<any>(`/fixed-assets/${id}`);
}

export async function createFixedAsset(data: any) {
  return await post<any>('/fixed-assets/', data);
}

export async function updateFixedAsset(id: number, data: any) {
  return await put<any>(`/fixed-assets/${id}`, data);
}

export async function getFixedAssetsSummary() {
  return await get<any>('/fixed-assets/summary');
}

export async function calculateDepreciation(assetId: number, month: number, year: number) {
  return await post<any>(`/fixed-assets/${assetId}/depreciate`, { month, year });
}

export async function disposeFixedAsset(assetId: number, data: { disposal_date: string; disposal_amount: number }) {
  return await post<any>(`/fixed-assets/${assetId}/dispose`, data);
}

export async function getDepreciationSchedule(assetId: number) {
  return await get<any[]>(`/fixed-assets/depreciation-schedule/${assetId}`);
}

// Asset Categories API
export async function getAssetCategories() {
  return await get<any[]>('/fixed-assets/categories');
}

export async function createAssetCategory(data: any) {
  return await post<any>('/fixed-assets/categories', data);
}
