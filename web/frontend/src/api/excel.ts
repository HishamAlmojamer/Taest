import axios from 'axios';
import { useAuthStore } from '@/stores/authStore';

// Dedicated axios call (NOT the shared `client`) so the camelize interceptor
// never touches binary Blob responses.
export async function downloadExcel(
  path: string,
  params?: Record<string, unknown>,
  filename?: string,
): Promise<void> {
  const token = useAuthStore.getState().accessToken;
  const res = await axios.get(`/api${path}`, {
    params,
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  });

  const contentType = (res.headers?.['content-type'] || '').toString();
  if (!contentType.includes('spreadsheetml') && !contentType.includes('excel')) {
    const text = await (res.data as Blob).text().catch(() => '');
    throw new Error(text || 'فشل تصدير الملف');
  }

  const blob = res.data as Blob;
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename || path.split('/').pop() || 'report.xlsx';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export async function uploadExcel<T = any>(
  path: string,
  file: File,
): Promise<T> {
  const token = useAuthStore.getState().accessToken;
  const form = new FormData();
  form.append('file', file);
  const res = await axios.post(`/api${path}`, form, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'Content-Type': 'multipart/form-data',
    },
  });
  return res.data as T;
}