import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getProducts } from '@/api/inventory';
import { cn, formatCurrency } from '@/lib/utils';

export default function ProductsListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['products', page, search],
    queryFn: () => getProducts({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', sortable: true, render: (item) => <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded">{String(item.code ?? '-')}</span> },
    { key: 'name', header: 'اسم المنتج', sortable: true, render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'categoryName', header: 'التصنيف', render: (item) => String(item.categoryName || '-') },
    { key: 'sellingPrice', header: 'سعر البيع', sortable: true, render: (item) => <span className="whitespace-nowrap tabular-nums">{formatCurrency(Number(item.sellingPrice))}</span> },
    { key: 'currentStock', header: 'المخزون', sortable: true, render: (item) => {
      const stock = Number(item.currentStock) || 0;
      const min = Number(item.minStock) || 0;
      const low = stock <= 0 || (min > 0 && stock <= min);
      return (
        <span
          title={low ? 'المخزون منخفض أو منتهٍ' : undefined}
          className={cn(
            'inline-flex min-w-[2.5rem] justify-center rounded-md px-2 py-0.5 text-xs font-semibold tabular-nums',
            low
              ? 'bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-400'
              : 'bg-gray-100 text-gray-700 dark:bg-zinc-800 dark:text-zinc-300'
          )}
        >
          {stock}
        </span>
      );
    }},
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="المنتجات"
        subtitle="إدارة المنتجات والمخزون"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>}
        actions={<button onClick={() => navigate('/inventory/products/new')} className="btn-primary">+ منتج جديد</button>}
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
        searchPlaceholder="بحث بالاسم أو الكود..."
        onRowClick={(item) => navigate(`/inventory/products/${item.id}`)}
      />
    </div>
  );
}
