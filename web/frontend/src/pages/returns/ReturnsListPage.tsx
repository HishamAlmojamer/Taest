import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getSalesReturns, getPurchaseReturns } from '@/api/returns';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import type { PaginatedResponse, SaleReturn, PurchaseReturn } from '@/types';

interface Props {
  type: 'sales' | 'purchase';
}

export default function ReturnsListPage({ type }: Props) {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const isSales = type === 'sales';
  const fetchFn = isSales ? getSalesReturns : getPurchaseReturns;
  const basePath = isSales ? '/returns/sales' : '/returns/purchases';
  const title = isSales ? 'مرتجعات المبيعات' : 'مرتجعات المشتريات';
  const partyLabel = isSales ? 'العميل' : 'المورد';
  const icon = isSales ? (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z" /></svg>
  ) : (
    <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
  );

  const { data, isLoading } = useQuery<PaginatedResponse<SaleReturn> | PaginatedResponse<PurchaseReturn>>({
    queryKey: [isSales ? 'sales-returns' : 'purchase-returns', page, search],
    queryFn: () => fetchFn({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'returnNumber', header: 'رقم المرتجع', sortable: true, render: (item) => <span className="font-medium text-primary-600">{String(item.returnNumber || '-')}</span> },
    { key: 'party', header: partyLabel, render: (item) => String(item.customerName || item.supplierName || '-') },
    { key: 'returnDate', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.returnDate || item.createdAt)) },
    { key: 'finalAmount', header: 'المبلغ', sortable: true, render: (item) => formatCurrency(Number(item.finalAmount || item.totalAmount || 0)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status || 'draft')} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title={title}
        subtitle={isSales ? 'إدارة مرتجعات المبيعات' : 'إدارة مرتجعات المشتريات'}
        icon={icon}
        actions={<button onClick={() => navigate(`${basePath}/new`)} className="btn-primary">+ مرتجع جديد</button>}
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
        searchPlaceholder="بحث برقم المرتجع..."
        onRowClick={(item) => navigate(`${basePath}/${item.id}`)}
      />
    </div>
  );
}
