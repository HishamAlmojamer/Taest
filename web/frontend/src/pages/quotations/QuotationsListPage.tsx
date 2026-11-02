import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getQuotations } from '@/api/quotations';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function QuotationsListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['quotations', page, search],
    queryFn: () => getQuotations({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'quotationNumber', header: 'رقم العرض', sortable: true, render: (item) => <span className="font-medium text-primary-600">{String(item.quotationNumber || '-')}</span> },
    { key: 'customerName', header: 'العميل', render: (item) => String(item.customerName || '-') },
    { key: 'quotationDate', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.quotationDate || item.createdAt)) },
    { key: 'finalAmount', header: 'المبلغ', sortable: true, render: (item) => formatCurrency(Number(item.finalAmount || 0)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status || 'draft')} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="عروض الأسعار"
        subtitle="إدارة عروض الأسعار للعملاء"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>}
        actions={<button onClick={() => navigate('/quotations/new')} className="btn-primary">+ عرض سعر جديد</button>}
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
        searchPlaceholder="بحث برقم العرض..."
        onRowClick={(item) => navigate(`/quotations/${item.id}`)}
      />
    </div>
  );
}
