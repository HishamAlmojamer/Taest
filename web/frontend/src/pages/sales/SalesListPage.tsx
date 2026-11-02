import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getSales } from '@/api/sales';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import type { Sale } from '@/types';

export default function SalesListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['sales', page, search],
    queryFn: () => getSales({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'invoiceNumber', header: 'رقم الفاتورة', sortable: true, render: (item) => <span className="font-medium text-primary-600">{String(item.invoiceNumber || '-')}</span> },
    { key: 'customerName', header: 'العميل', sortable: true, render: (item) => String(item.customerName || '-') },
    { key: 'createdAt', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.createdAt || item.date)) },
    { key: 'finalAmount', header: 'المبلغ', sortable: true, render: (item) => <span className="font-bold">{formatCurrency(Number(item.finalAmount || item.totalAmount || 0))}</span> },
    { key: 'workflowState', header: 'الحالة', render: (item) => <StatusBadge status={String(item.workflowState || item.status || 'DRAFT')} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="فواتير المبيعات"
        subtitle="إدارة فواتير المبيعات ومتابعة الحالتها"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" /></svg>}
        actions={
          <button onClick={() => navigate('/sales/new')} className="btn-primary flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            فاتورة جديدة
          </button>
        }
      />
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
        searchPlaceholder="بحث برقم الفاتورة أو اسم العميل..."
        onRowClick={(item) => navigate(`/sales/${item.id}`)}
      />
    </div>
  );
}
