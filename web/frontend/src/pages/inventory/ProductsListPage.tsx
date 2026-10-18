import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getProducts } from '@/api/inventory';
import { formatCurrency } from '@/lib/utils';

export default function ProductsListPage() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['products', page, search],
    queryFn: () => getProducts({ page, pageSize: 10, search }),
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'sku', header: 'الكود', sortable: true, render: (item) => <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{String(item.sku)}</span> },
    { key: 'name', header: 'اسم المنتج', sortable: true, render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'categoryName', header: 'التصنيف', render: (item) => String(item.categoryName || '-') },
    { key: 'sellingPrice', header: 'سعر البيع', sortable: true, render: (item) => formatCurrency(Number(item.sellingPrice)) },
    { key: 'currentStock', header: 'المخزون', sortable: true, render: (item) => {
      const stock = Number(item.currentStock);
      const min = Number(item.minStock);
      return <span className={stock <= min ? 'text-red-600 font-bold' : ''}>{stock}</span>;
    }},
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">المنتجات</h1>
        <button onClick={() => navigate('/inventory/products/new')} className="btn-primary flex items-center gap-2">
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
          منتج جديد
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
        searchPlaceholder="بحث بالاسم أو الكود..."
      />
    </div>
  );
}
