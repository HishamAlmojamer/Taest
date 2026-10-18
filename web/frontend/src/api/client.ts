import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

function toCamelCase(str: string): string {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

function camelizeKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(camelizeKeys);
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [toCamelCase(k), camelizeKeys(v)]),
    );
  }
  return obj;
}

function snakeizeKeys(obj: unknown): unknown {
  if (Array.isArray(obj)) return obj.map(snakeizeKeys);
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Date)) {
    return Object.fromEntries(
      Object.entries(obj as Record<string, unknown>).map(([k, v]) => [toSnakeCase(k), snakeizeKeys(v)]),
    );
  }
  return obj;
}

const client = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config: any) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  if (config.data && typeof config.data === 'object') {
    config.data = snakeizeKeys(config.data);
  }
  return config;
});

client.interceptors.response.use(
  (response: any) => {
    response.data = camelizeKeys(response.data);
    return response;
  },
  (error: any) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

export default client;

export async function get<T = any>(url: string, params?: Record<string, unknown>): Promise<T> {
  const res = await client.get(url, { params });
  return res.data;
}

export async function post<T = any>(url: string, data?: unknown): Promise<T> {
  const res = await client.post(url, data);
  return res.data;
}

export async function put<T = any>(url: string, data?: unknown): Promise<T> {
  const res = await client.put(url, data);
  return res.data;
}

export async function del<T = any>(url: string): Promise<T> {
  const res = await client.delete(url);
  return res.data;
}
