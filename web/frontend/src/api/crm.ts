import { get, post, put } from './client';

export async function getCustomers(params?: Record<string, unknown>) {
  return await get<{ items: Array<{ id: number; name: string; email?: string; phone?: string }>; total: number }>('/crm/customers', params);
}

export async function getCustomer(id: string) {
  return await get(`/crm/customers/${id}`);
}

export async function createCustomer(data: unknown) {
  return await post('/crm/customers', data);
}

export async function updateCustomer(id: string, data: unknown) {
  return await put(`/crm/customers/${id}`, data);
}

export async function getSuppliers(params?: Record<string, unknown>) {
  return await get<{ items: Array<{ id: number; name: string; email?: string; phone?: string }>; total: number }>('/crm/suppliers', params);
}

export async function getSupplier(id: string) {
  return await get(`/crm/suppliers/${id}`);
}

export async function createSupplier(data: unknown) {
  return await post('/crm/suppliers', data);
}

export async function updateSupplier(id: string, data: unknown) {
  return await put(`/crm/suppliers/${id}`, data);
}

export async function getLeads(params?: Record<string, unknown>) {
  return await get('/crm/leads', params);
}

export async function createLead(data: unknown) {
  return await post('/crm/leads', data);
}
