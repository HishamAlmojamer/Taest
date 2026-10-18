import { post, get, put } from './client';

export async function login(data: { username: string; password: string }) {
  return await post('/auth/login', data);
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
