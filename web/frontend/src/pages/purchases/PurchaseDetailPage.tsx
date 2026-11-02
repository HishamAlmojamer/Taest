import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPurchase, submitPurchase, approvePurchase, rejectPurchase } from '@/api/purchases';
import { formatCurrency, formatDate, getStatusLabel } from '@/lib/utils';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

export default function PurchaseDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const company = useCompany();
  const toast = useToast();
  const [showPrint, setShowPrint] = useState(false);

  const { data: purchase, isLoading } = useQuery({
    queryKey: ['purchase', id],
    queryFn: () => getPurchase(id!),
    enabled: !!id,
  });

  const submitMutation = useMutation({
    mutationFn: () => submitPurchase(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase', id] });
      toast.success('تم إرسال أمر الشراء للمراجعة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: () => approvePurchase(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase', id] });
      toast.success('تم اعتماد أمر الشراء');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectPurchase(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchase', id] });
      toast.warning('تم رفض أمر الشراء');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  if (isLoading) return <PageLoader />;
  if (!purchase) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">أمر الشراء غير موجود</div>;

  const status = purchase.workflowState || purchase.status || 'DRAFT';
  const purchaseTotal = purchase.finalAmount || purchase.total || 0;
  const purchaseSubtotal = purchase.subtotal || purchase.totalAmount || 0;
  const purchasePaidAmount = purchase.paidAmount || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`أمر شراء ${purchase.orderNumber || purchase.invoiceNumber || '-'}`}
        subtitle={formatDate(purchase.date || purchase.createdAt)}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>}
        actions={
          <>
            {status.toUpperCase() === 'DRAFT' && (
              <button onClick={() => submitMutation.mutate()} className="btn-primary" disabled={submitMutation.isPending}>إرسال للمراجعة</button>
            )}
            {status.toUpperCase() === 'SUBMITTED' && (
              <>
                <button onClick={() => approveMutation.mutate()} className="btn-primary bg-green-600 hover:bg-green-700" disabled={approveMutation.isPending}>اعتماد</button>
                <button onClick={() => rejectMutation.mutate()} className="btn-danger" disabled={rejectMutation.isPending}>رفض</button>
              </>
            )}
            <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
              </svg>
              طباعة / PDF
            </button>
            <button onClick={() => navigate('/purchases')} className="btn-secondary">رجوع</button>
          </>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card space-y-4">
          <h3 className="text-lg font-semibold">تفاصيل أمر الشراء</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500 dark:text-zinc-400">المورد: </span><span className="font-medium">{purchase.supplierName || '-'}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">الحالة: </span><StatusBadge status={status} /></div>
            <div><span className="text-gray-500 dark:text-zinc-400">التاريخ: </span><span>{formatDate(purchase.date || purchase.createdAt)}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">تاريخ الاستحقاق: </span><span>{formatDate(purchase.dueDate)}</span></div>
          </div>

          <table className="w-full mt-4">
            <thead>
              <tr className="table-header">
                <th className="px-3 py-2 text-right text-xs">المنتج</th>
                <th className="px-3 py-2 text-right text-xs">الكمية</th>
                <th className="px-3 py-2 text-right text-xs">سعر الوحدة</th>
                <th className="px-3 py-2 text-right text-xs">الخصم</th>
                <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(purchase.items || []).map((item: any) => (
                <tr key={item.id} className="table-row">
                  <td className="px-3 py-2 text-sm">{item.productName || item.product_name || '-'}</td>
                  <td className="px-3 py-2 text-sm">{item.quantity}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item.unitCost || item.unit_cost || 0)}</td>
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
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع الفرعي</span><span>{formatCurrency(purchaseSubtotal)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة</span><span>{formatCurrency(purchase.taxAmount || 0)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الخصم</span><span>{formatCurrency(purchase.discount || 0)}</span></div>
            <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-3">
              <span>الإجمالي</span>
              <span className="text-primary-600">{formatCurrency(purchaseTotal)}</span>
            </div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المدفوع</span><span className="text-green-600">{formatCurrency(purchasePaidAmount)}</span></div>
            <div className="flex justify-between text-sm font-medium"><span className="text-gray-500 dark:text-zinc-400">المتبقي</span><span className="text-red-600">{formatCurrency(purchaseTotal - purchasePaidAmount)}</span></div>
          </div>
          {purchase.notes && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-700">
              <p className="text-sm text-gray-500 dark:text-zinc-400">ملاحظات:</p>
              <p className="text-sm mt-1">{purchase.notes}</p>
            </div>
          )}
        </div>
      </div>

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title={`أمر شراء ${purchase.orderNumber || purchase.invoiceNumber || '-'}`}
        filename={`أمر-شراء-${purchase.orderNumber || purchase.invoiceNumber || purchase.id}`}
      >
        <PrintDocument
          company={company}
          title="أمر شراء"
          footerText={undefined}
          meta={[
            { label: 'رقم الأمر', value: purchase.orderNumber || purchase.invoiceNumber || '-' },
            { label: 'التاريخ', value: formatDate(purchase.date || purchase.createdAt) },
            { label: 'المورد', value: purchase.supplierName || '-' },
            { label: 'الحالة', value: getStatusLabel(status, 'ar') },
          ]}
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">#</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المنتج</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الكمية</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">سعر الوحدة</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الخصم</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(purchase.items || []).map((item: any, idx: number) => (
                <tr key={item.id || idx}>
                  <td className="px-3 py-2 border border-gray-300">{idx + 1}</td>
                  <td className="px-3 py-2 border border-gray-300">{item.productName || item.product_name || '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{item.quantity}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(item.unitCost || item.unit_cost || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(item.discount || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300 font-medium">{formatCurrency(item.total || item.totalPrice || item.total_price || 0)}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-semibold">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>المجموع الفرعي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(purchaseSubtotal)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الضريبة</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(purchase.taxAmount || 0)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الخصم</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(purchase.discount || 0)}</td>
              </tr>
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300 text-primary-600">{formatCurrency(purchaseTotal)}</td>
              </tr>
            </tbody>
          </table>
          {purchase.notes && (
            <div className="mt-4">
              <p className="text-sm font-semibold text-gray-700 mb-1">ملاحظات:</p>
              <p className="text-sm text-gray-600">{purchase.notes}</p>
            </div>
          )}
          <div className="mt-10 grid grid-cols-2 gap-8 text-center text-sm text-gray-700">
            <div><p className="border-t border-gray-400 pt-2 font-medium">توقيع المستلم</p></div>
            <div><p className="border-t border-gray-400 pt-2 font-medium">ختم وتوقيع الشركة</p></div>
          </div>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}