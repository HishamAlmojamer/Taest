import { get, post, put, del } from './client';
import type { PaginatedResponse, Product, ProductInput, Category, Warehouse, StockMovement, StockMovementInput, PaginationParams } from '@/types';

export async function getProducts(params: PaginationParams) {
  return await get<PaginatedResponse<Product>>('/inventory/products', params as Record<string, unknown>);
}

export async function getProduct(id: string | number) {
  return await get<Product>(`/inventory/products/${id}`);
}

export async function createProduct(data: ProductInput) {
  return await post<Product>('/inventory/products', data);
}

export async function updateProduct(id: string | number, data: Partial<ProductInput>) {
  return await put<Product>(`/inventory/products/${id}`, data);
}

export async function deleteProduct(id: string) {
  return await del(`/inventory/products/${id}`);
}

export async function getCategories(params?: PaginationParams) {
  return await get<{ items: Category[]; total: number }>('/inventory/categories', params as Record<string, unknown>);
}

export async function createCategory(data: Partial<Category>) {
  return await post<Category>('/inventory/categories', data);
}

export async function updateCategory(id: string, data: Partial<Category>) {
  return await put<Category>(`/inventory/categories/${id}`, data);
}

export async function deleteCategory(id: string) {
  return await del(`/inventory/categories/${id}`);
}

export async function getWarehouses(params?: PaginationParams) {
  return await get<{ items: Warehouse[]; total: number }>('/inventory/warehouses', params as Record<string, unknown>);
}

export async function createWarehouse(data: Partial<Warehouse>) {
  return await post<Warehouse>('/inventory/warehouses', data);
}

export async function updateWarehouse(id: string, data: Partial<Warehouse>) {
  return await put<Warehouse>(`/inventory/warehouses/${id}`, data);
}

export async function deleteWarehouse(id: string) {
  return await del(`/inventory/warehouses/${id}`);
}

export async function getStockMovements(params: PaginationParams) {
  return await get<PaginatedResponse<StockMovement>>('/inventory/stock-movements', params as Record<string, unknown>);
}

export async function createStockMovement(data: StockMovementInput) {
  return await post<{ id: number; message: string; currentStock: number }>('/inventory/stock-movements', data);
}
