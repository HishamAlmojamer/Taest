import { useQuery } from '@tanstack/react-query';
import { get } from '@/api/client';
import type { Company } from '@/types';

export function useCompany() {
  const { data } = useQuery({
    queryKey: ['company'],
    queryFn: async () => {
      try {
        return await get<Company>('/settings/company');
      } catch {
        return null;
      }
    },
    staleTime: 5 * 60 * 1000,
  });
  return data || null;
}
