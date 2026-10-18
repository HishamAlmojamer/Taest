import { get } from './client';

export async function getAuditLogs(params?: Record<string, unknown>) {
  return await get('/audit/logs', params);
}

export async function getAuditLog(id: number) {
  return await get(`/audit/logs/${id}`);
}

export async function getAuditLogsByEntity(entityType: string, entityId: number) {
  return await get(`/audit/logs/entity/${entityType}/${entityId}`);
}

export async function getAuditLogsByUser(userId: number) {
  return await get(`/audit/logs/user/${userId}`);
}
