import { get, post, del } from './client';
import type { PaginatedResponse, AppNotification } from '@/types';

export async function getNotifications(params: { page?: number; pageSize?: number; unreadOnly?: boolean } = {}) {
  return await get<PaginatedResponse<AppNotification>>('/notifications', {
    page: params.page || 1,
    per_page: params.pageSize || 30,
    unread_only: params.unreadOnly,
  });
}

export async function getUnreadCount() {
  return await get<{ count: number }>('/notifications/unread-count');
}

export async function createNotification(data: {
  userId?: number;
  title: string;
  message?: string;
  notificationType?: string;
  link?: string;
  companyId?: number;
}) {
  return await post<{ id: number; message: string }>('/notifications', data);
}

export async function markNotificationRead(id: string | number) {
  return await post<{ message: string }>(`/notifications/${id}/read`);
}

export async function markAllNotificationsRead() {
  return await post<{ message: string }>('/notifications/read-all');
}

export async function deleteNotification(id: string | number) {
  return await del<{ message: string }>(`/notifications/${id}`);
}