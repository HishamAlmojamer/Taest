import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getLeads } from '@/api/crm';
import { formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function LeadsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['leads', page, search],
    queryFn: () => getLeads({ page, pageSize: 10, search }),
  });

  const leads = Array.isArray(data) ? data : (data as Record<string, unknown>)?.items || [];

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'leadName', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.leadName || item.name || '-')}</span> },
    { key: 'company', header: 'الشركة', render: (item) => String(item.company || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'source', header: 'المصدر', render: (item) => String(item.source || '-') },
    { key: 'expectedAmount', header: 'القيمة', render: (item) => formatCurrency(Number(item.expectedAmount || item.value || 0)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">العملاء المحتملون</h1>
        <span className="text-sm text-gray-500 dark:text-zinc-400">البيانات من قاعدة البيانات فقط</span>
      </div>
      <DataTable columns={columns} data={leads as Record<string, unknown>[]} loading={isLoading} totalItems={(leads as Record<string, unknown>[]).length || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث..." />
    </div>
  );
}
