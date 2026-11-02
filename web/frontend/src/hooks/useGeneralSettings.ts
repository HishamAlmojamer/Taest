import { useQuery } from '@tanstack/react-query';
import { get } from '@/api/client';

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

export function useGeneralSettings(): Record<string, string> {
  const { data } = useQuery({
    queryKey: ['general-settings'],
    queryFn: async () => {
      try {
        const res = await get<{ values: Record<string, string> }>('/settings/general');
        const values: Record<string, string> = {};
        for (const [key, val] of Object.entries(res.values || {})) {
          values[toSnakeCase(key)] = val;
        }
        return values;
      } catch {
        return {};
      }
    },
    staleTime: 5 * 60 * 1000,
  });
  return data || {};
}
