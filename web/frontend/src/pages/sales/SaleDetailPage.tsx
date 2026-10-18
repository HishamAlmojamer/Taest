import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSale, submitSale, approveSale, rejectSale } from '@/api/sales';
import { formatCurrency, formatDate, getStatusLabel } from '@/lib/utils';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function SaleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: sale, isLoading } = useQuery({
    queryKey: ['sale', id],
    queryFn: () => getSale(id!),
    enabled: !!id,
  });

  const submitMutation = useMutation({
    mutationFn: () => submitSale(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sale', id] }),
  });

  const approveMutation = useMutation({
    mutationFn: () => approveSale(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sale', id] }),
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectSale(id!),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sale', id] }),
  });

  if (isLoading) return <PageLoader />;
  if (!sale) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">الفاتورة غير موجودة</div>;

  const saleStatus = sale.workflowState || sale.status || 'DRAFT';
  const saleTotal = sale.finalAmount || sale.total || sale.totalAmount || 0;
  const saleSubtotal = sale.subtotal || sale.totalAmount || 0;
  const salePaidAmount = sale.paidAmount || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">فاتورة {sale.invoiceNumber || '-'}</h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">{formatDate(sale.date || sale.createdAt)}</p>
        </div>
        <div className="flex items-center gap-2">
          {saleStatus.toUpperCase() === 'DRAFT' && (
            <button onClick={() => submitMutation.mutate()} className="btn-primary" disabled={submitMutation.isPending}>إرسال للمراجعة</button>
          )}
          {saleStatus.toUpperCase() === 'SUBMITTED' && (
            <>
              <button onClick={() => approveMutation.mutate()} className="btn-primary bg-green-600 hover:bg-green-700" disabled={approveMutation.isPending}>اعتماد</button>
              <button onClick={() => rejectMutation.mutate()} className="btn-danger" disabled={rejectMutation.isPending}>رفض</button>
            </>
          )}
          <button onClick={() => navigate('/sales')} className="btn-secondary">رجوع</button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card space-y-4">
          <h3 className="text-lg font-semibold">تفاصيل الفاتورة</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500 dark:text-zinc-400">العميل: </span><span className="font-medium">{sale.customerName || '-'}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">الحالة: </span><StatusBadge status={saleStatus} /></div>
            <div><span className="text-gray-500 dark:text-zinc-400">التاريخ: </span><span>{formatDate(sale.date || sale.createdAt)}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">رقم الفاتورة: </span><span>{sale.invoiceNumber || '-'}</span></div>
          </div>

          <table className="w-full mt-4">
            <thead>
              <tr className="table-header">
                <th className="px-3 py-2 text-right text-xs">المنتج</th>
                <th className="px-3 py-2 text-right text-xs">الكمية</th>
                <th className="px-3 py-2 text-right text-xs">السعر</th>
                <th className="px-3 py-2 text-right text-xs">الخصم</th>
                <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(sale.items || []).map((item: any) => (
                <tr key={item.id} className="table-row">
                  <td className="px-3 py-2 text-sm">{item.productName || item.product_name || '-'}</td>
                  <td className="px-3 py-2 text-sm">{item.quantity}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item.unitPrice || item.unit_price || 0)}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item.discount || 0)}</td>
                  <td className="px-3 py-2 text-sm font-medium">{formatCurrency(item.total || item.totalPrice || item.total_price || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card space-y-4">
          <h3 className="text-lg font-semibold">الملخص المالي</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع الفرعي</span><span>{formatCurrency(saleSubtotal)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة</span><span>{formatCurrency(sale.taxAmount || 0)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الخصم</span><span>{formatCurrency(sale.discount || 0)}</span></div>
            <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-3">
              <span>الإجمالي</span>
              <span className="text-primary-600">{formatCurrency(saleTotal)}</span>
            </div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المدفوع</span><span className="text-green-600">{formatCurrency(salePaidAmount)}</span></div>
            <div className="flex justify-between text-sm font-medium"><span className="text-gray-500 dark:text-zinc-400">المتبقي</span><span className="text-red-600">{formatCurrency(saleTotal - salePaidAmount)}</span></div>
          </div>
          {sale.notes && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-700">
              <p className="text-sm text-gray-500 dark:text-zinc-400">ملاحظات:</p>
              <p className="text-sm mt-1">{sale.notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
