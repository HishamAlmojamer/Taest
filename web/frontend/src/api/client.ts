import axios, { type AxiosRequestConfig } from 'axios';
import { useAuthStore } from '@/stores/authStore';

const BASE_URL = import.meta.env.VITE_API_URL || '/api';

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
  baseURL: BASE_URL,
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

// Single-flight refresh: concurrent 401s share one refresh request.
let refreshPromise: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) throw new Error('No refresh token available');

  // Use raw axios so this call does not recurse through the interceptors.
  // Send both key styles so it works through the gateway (camelCase) and
  // directly against FastAPI (snake_case).
  const res = await axios.post(
    `${BASE_URL}/auth/refresh`,
    { refreshToken, refresh_token: refreshToken },
    { headers: { 'Content-Type': 'application/json' } },
  );

  const data = res.data || {};
  const accessToken = data.accessToken ?? data.access_token;
  const newRefreshToken = data.refreshToken ?? data.refresh_token ?? refreshToken;

  if (!accessToken) throw new Error('Refresh response missing access token');
  useAuthStore.getState().setTokens(accessToken, newRefreshToken);
  return accessToken;
}

function redirectToLogin() {
  useAuthStore.getState().logout();
  if (window.location.pathname !== '/login') {
    window.location.href = '/login';
  }
}

client.interceptors.response.use(
  (response: any) => {
    response.data = camelizeKeys(response.data);
    return response;
  },
  async (error: any) => {
    const original = error.config as (AxiosRequestConfig & { _retry?: boolean }) | undefined;
    const status = error.response?.status;
    const requestUrl = (original as { url?: string } | undefined)?.url;
    const isAuthEndpoint = typeof requestUrl === 'string' && requestUrl.includes('/auth/');

    if (status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const token = await refreshPromise;
        original.headers = { ...(original.headers || {}), Authorization: `Bearer ${token}` };
        return client(original);
      } catch {
        redirectToLogin();
        return Promise.reject(error);
      }
    }

    if (status === 401 && !isAuthEndpoint) {
      redirectToLogin();
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
