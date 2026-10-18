import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getStockMovements } from '@/api/inventory';
import { formatDate, formatCurrency } from '@/lib/utils';

export default function StockMovementsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['stock-movements', page, search],
    queryFn: () => getStockMovements({ page, pageSize: 10, search }),
  });

  const typeLabels: Record<string, string> = { IN: 'وارد', OUT: 'صادر', TRANSFER: 'نقل', ADJUSTMENT: 'تسوية' };
  const typeColors: Record<string, string> = { IN: 'badge-success', OUT: 'badge-danger', TRANSFER: 'badge-info', ADJUSTMENT: 'badge-warning' };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'productName', header: 'المنتج', render: (item) => <span className="font-medium">{String(item.productName)}</span> },
    { key: 'type', header: 'النوع', render: (item) => <span className={typeColors[String(item.type)] || 'badge-info'}>{typeLabels[String(item.type)] || String(item.type)}</span> },
    { key: 'warehouseName', header: 'المخزن', render: (item) => String(item.warehouseName) },
    { key: 'quantity', header: 'الكمية', render: (item) => String(item.quantity) },
    { key: 'unitCost', header: 'التكلفة', render: (item) => formatCurrency(Number(item.unitCost)) },
    { key: 'reference', header: 'المرجع', render: (item) => String(item.reference || '-') },
    { key: 'createdAt', header: 'التاريخ', render: (item) => formatDate(String(item.createdAt)) },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">حركة المخزون</h1>
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالمنتج..." />
    </div>
  );
}
