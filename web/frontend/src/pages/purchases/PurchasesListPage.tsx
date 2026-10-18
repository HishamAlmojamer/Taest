import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getPurchases } from '@/api/purchases';
import { formatCurrency, formatDate, getStatusLabel } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function PurchasesListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['purchases', page, search],
    queryFn: () => getPurchases({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'orderNumber', header: 'رقم الطلب', sortable: true, render: (item) => <span className="font-medium text-primary-600">{String(item.orderNumber)}</span> },
    { key: 'supplierName', header: 'المورد', sortable: true, render: (item) => String(item.supplierName) },
    { key: 'date', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.date)) },
    { key: 'total', header: 'المبلغ', sortable: true, render: (item) => formatCurrency(Number(item.total)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">أوامر الشراء</h1>
        <button onClick={() => navigate('/purchases/new')} className="btn-primary flex items-center gap-2">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          أمر شراء جديد
        </button>
      </div>

      <DataTable
        columns={columns}
        data={(data?.items || []) as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={data?.total || 0}
        page={page}
        pageSize={10}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="بحث برقم الطلب أو اسم المورد..."
      />
    </div>
  );
}
