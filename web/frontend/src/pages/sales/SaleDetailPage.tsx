import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSale, submitSale, approveSale, rejectSale } from '@/api/sales';
import { formatCurrency, formatDate, getStatusLabel } from '@/lib/utils';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { useGeneralSettings } from '@/hooks/useGeneralSettings';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

export default function SaleDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const company = useCompany();
  const settings = useGeneralSettings();
  const toast = useToast();
  const [showPrint, setShowPrint] = useState(false);

  const { data: sale, isLoading } = useQuery({
    queryKey: ['sale', id],
    queryFn: () => getSale(id!),
    enabled: !!id,
  });

  const submitMutation = useMutation({
    mutationFn: () => submitSale(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sale', id] });
      toast.success('تم إرسال الفاتورة للمراجعة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: () => approveSale(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sale', id] });
      toast.success('تم اعتماد الفاتورة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const rejectMutation = useMutation({
    mutationFn: () => rejectSale(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sale', id] });
      toast.success('تم رفض الفاتورة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  if (isLoading) return <PageLoader />;
  if (!sale) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">الفاتورة غير موجودة</div>;

  const saleStatus = sale.workflowState || sale.status || 'DRAFT';
  const saleTotal = sale.finalAmount || sale.total || sale.totalAmount || 0;
  const saleSubtotal = sale.subtotal || sale.totalAmount || 0;
  const salePaidAmount = sale.paidAmount || 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title={`فاتورة ${sale.invoiceNumber || '-'}`}
        subtitle={formatDate(sale.date || sale.createdAt)}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
        actions={
          <>
            {saleStatus.toUpperCase() === 'DRAFT' && (
              <button onClick={() => submitMutation.mutate()} className="btn-primary" disabled={submitMutation.isPending}>إرسال للمراجعة</button>
            )}
            {saleStatus.toUpperCase() === 'SUBMITTED' && (
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
            <button onClick={() => navigate('/sales')} className="btn-secondary">رجوع</button>
          </>
        }
      />

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

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title={`فاتورة ${sale.invoiceNumber || '-'}`}
        filename={`فاتورة-${sale.invoiceNumber || sale.id}`}
      >
        <PrintDocument
          company={company}
          title="فاتورة مبيعات"
          footerText={settings.receipt_footer}
          meta={[
            { label: 'رقم الفاتورة', value: sale.invoiceNumber || '-' },
            { label: 'التاريخ', value: formatDate(sale.date || sale.createdAt) },
            { label: 'العميل', value: sale.customerName || '-' },
            { label: 'الحالة', value: getStatusLabel(saleStatus, 'ar') },
          ]}
        >
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">#</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المنتج</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الكمية</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">السعر</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الخصم</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الإجمالي</th>
              </tr>
            </thead>
            <tbody>
              {(sale.items || []).map((item: any, idx: number) => (
                <tr key={item.id || idx}>
                  <td className="px-3 py-2 border border-gray-300">{idx + 1}</td>
                  <td className="px-3 py-2 border border-gray-300">{item.productName || item.product_name || '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{item.quantity}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(item.unitPrice || item.unit_price || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(item.discount || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300 font-medium">{formatCurrency(item.total || item.totalPrice || item.total_price || 0)}</td>
                </tr>
              ))}
              <tr className="bg-gray-50 font-semibold">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>المجموع الفرعي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(saleSubtotal)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الضريبة</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(sale.taxAmount || 0)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الخصم</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(sale.discount || 0)}</td>
              </tr>
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300 text-primary-600">{formatCurrency(saleTotal)}</td>
              </tr>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>المدفوع</td>
                <td className="px-3 py-2 border border-gray-300 text-green-600">{formatCurrency(salePaidAmount)}</td>
              </tr>
              <tr className="font-medium">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>المتبقي</td>
                <td className="px-3 py-2 border border-gray-300 text-red-600">{formatCurrency(saleTotal - salePaidAmount)}</td>
              </tr>
            </tbody>
          </table>
          {sale.notes && (
            <div className="mt-4">
              <p className="text-sm font-semibold text-gray-700 mb-1">ملاحظات:</p>
              <p className="text-sm text-gray-600">{sale.notes}</p>
            </div>
          )}
          <div className="mt-10 grid grid-cols-2 gap-8 text-center text-sm text-gray-700">
            <div>
              <p className="border-t border-gray-400 pt-2 font-medium">توقيع المستلم</p>
            </div>
            <div>
              <p className="border-t border-gray-400 pt-2 font-medium">ختم وتوقيع الشركة</p>
            </div>
          </div>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
