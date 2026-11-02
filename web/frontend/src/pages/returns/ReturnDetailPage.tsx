import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getSalesReturn,
  getPurchaseReturn,
  approveSalesReturn,
  approvePurchaseReturn,
  voidSalesReturn,
  voidPurchaseReturn,
} from '@/api/returns';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { SaleReturn, PurchaseReturn } from '@/types';

interface Props {
  type: 'sales' | 'purchase';
}

export default function ReturnDetailPage({ type }: Props) {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const isSales = type === 'sales';
  const basePath = isSales ? '/returns/sales' : '/returns/purchases';
  const toast = useToast();

  const { data: ret, isLoading } = useQuery<SaleReturn | PurchaseReturn>({
    queryKey: [isSales ? 'sales-return' : 'purchase-return', id],
    queryFn: () => (isSales ? getSalesReturn(id!) : getPurchaseReturn(id!)),
    enabled: !!id,
  });

  const approveMutation = useMutation({
    mutationFn: () => (isSales ? approveSalesReturn(id!) : approvePurchaseReturn(id!)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [isSales ? 'sales-return' : 'purchase-return', id] });
      toast.success('تم اعتماد المرتجع');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const voidMutation = useMutation({
    mutationFn: () => (isSales ? voidSalesReturn(id!, 'voided from UI') : voidPurchaseReturn(id!, 'voided from UI')),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [isSales ? 'sales-return' : 'purchase-return', id] });
      toast.success('تم إلغاء المرتجع');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  if (isLoading) return <PageLoader />;
  if (!ret) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">المرتجع غير موجود</div>;

  const retData = ret as SaleReturn & Partial<PurchaseReturn>;
  const partyName = retData.customerName || retData.supplierName || '-';
  const itemLabel = isSales ? 'unitPrice' : 'unitCost';
  const itemTotal = isSales ? 'totalPrice' : 'totalCost';
  const status = String(ret.status || 'draft');

  return (
    <div className="space-y-6">
      <PageHeader
        title={`مرتجع ${ret.returnNumber || '-'}`}
        subtitle={formatDate(ret.returnDate || ret.createdAt)}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z" /></svg>}
        actions={
          <>
            {status === 'draft' && (
              <button onClick={() => approveMutation.mutate()} className="btn-primary bg-green-600 hover:bg-green-700" disabled={approveMutation.isPending}>
                اعتماد المرتجع
              </button>
            )}
            {(status === 'draft' || status === 'submitted') && (
              <button onClick={() => voidMutation.mutate()} className="btn-danger" disabled={voidMutation.isPending}>
                إلغاء
              </button>
            )}
            <button onClick={() => navigate(basePath)} className="btn-secondary">رجوع</button>
          </>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card space-y-4">
          <h3 className="text-lg font-semibold">تفاصيل المرتجع</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500 dark:text-zinc-400">{isSales ? 'العميل' : 'المورد'}: </span><span className="font-medium">{partyName}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">الحالة: </span><StatusBadge status={status} /></div>
            <div><span className="text-gray-500 dark:text-zinc-400">المستند الأصلي: </span><span>{retData.saleInvoiceNumber || retData.purchaseOrderNumber || '-'}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">طريقة رد المبلغ: </span><span>{ret.refundMethod || '-'}</span></div>
          </div>

          <table className="w-full mt-4">
            <thead>
              <tr className="table-header">
                <th className="px-3 py-2 text-right text-xs">المنتج</th>
                <th className="px-3 py-2 text-right text-xs">الكمية</th>
                <th className="px-3 py-2 text-right text-xs">السعر</th>
                <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(ret.items || []).map((item: any, idx: number) => (
                <tr key={item.id || idx} className="table-row">
                  <td className="px-3 py-2 text-sm">{item.productName || item.product_id || '-'}</td>
                  <td className="px-3 py-2 text-sm">{item.quantity}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item[itemLabel] || 0)}</td>
                  <td className="px-3 py-2 text-sm font-medium">{formatCurrency(item[itemTotal] || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card space-y-4">
          <h3 className="text-lg font-semibold">الملخص المالي</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع</span><span>{formatCurrency(ret.totalAmount || 0)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة</span><span>{formatCurrency(ret.taxAmount || 0)}</span></div>
            <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-3">
              <span>الإجمالي</span><span className="text-primary-600">{formatCurrency(ret.finalAmount || 0)}</span>
            </div>
          </div>
          {(ret.reason || ret.notes) && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-700 space-y-2">
              {ret.reason && (
                <div><p className="text-sm text-gray-500 dark:text-zinc-400">السبب:</p><p className="text-sm mt-1">{ret.reason}</p></div>
              )}
              {ret.notes && (
                <div><p className="text-sm text-gray-500 dark:text-zinc-400">ملاحظات:</p><p className="text-sm mt-1">{ret.notes}</p></div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
