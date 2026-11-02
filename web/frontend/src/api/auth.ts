import { post, get, put } from './client';
import type { LoginContext } from '@/types';

export async function login(data: { username: string; password: string; fiscalYearId?: number; branchId?: number }) {
  return await post('/auth/login', data);
}

export async function getLoginContext() {
  return await get<LoginContext>('/auth/context');
}

export async function refreshToken(token: string) {
  return await post('/auth/refresh', { refreshToken: token });
}

export async function getMe() {
  return await get('/auth/me');
}

export async function changePassword(data: { oldPassword: string; newPassword: string }) {
  return await put('/auth/password', data);
}
