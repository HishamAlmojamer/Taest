import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getQuotation, submitQuotation, acceptQuotation, convertQuotation } from '@/api/quotations';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

export default function QuotationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: quotation, isLoading } = useQuery({
    queryKey: ['quotation', id],
    queryFn: () => getQuotation(id!),
    enabled: !!id,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['quotation', id] });

  const submitMutation = useMutation({
    mutationFn: () => submitQuotation(id!),
    onSuccess: () => {
      invalidate();
      toast.success('تم إرسال العرض للعميل');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const acceptMutation = useMutation({
    mutationFn: () => acceptQuotation(id!),
    onSuccess: () => {
      invalidate();
      toast.success('تم قبول العرض');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const convertMutation = useMutation({
    mutationFn: () => convertQuotation(id!),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      toast.success('تم تحويل العرض لفاتورة');
      navigate('/sales');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  if (isLoading) return <PageLoader />;
  if (!quotation) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">العرض غير موجود</div>;

  const status = String(quotation.status || 'draft');

  return (
    <div className="space-y-6">
      <PageHeader
        title={`عرض ${quotation.quotationNumber || '-'}`}
        subtitle={`${formatDate(quotation.quotationDate)} — صالح حتى ${formatDate(quotation.validUntil)}`}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>}
        actions={
          <>
            {status === 'draft' && (
              <button onClick={() => submitMutation.mutate()} className="btn-primary" disabled={submitMutation.isPending}>إرسال للعميل</button>
            )}
            {status === 'submitted' && (
              <button onClick={() => acceptMutation.mutate()} className="btn-primary bg-green-600 hover:bg-green-700" disabled={acceptMutation.isPending}>قبول العرض</button>
            )}
            {status === 'accepted' && (
              <button onClick={() => convertMutation.mutate()} className="btn-primary bg-green-600 hover:bg-green-700" disabled={convertMutation.isPending}>تحويل إلى فاتورة</button>
            )}
            <button onClick={() => navigate('/quotations')} className="btn-secondary">رجوع</button>
          </>
        }
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card space-y-4">
          <h3 className="text-lg font-semibold">تفاصيل العرض</h3>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div><span className="text-gray-500 dark:text-zinc-400">العميل: </span><span className="font-medium">{quotation.customerName || '-'}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">الحالة: </span><StatusBadge status={status} /></div>
            <div><span className="text-gray-500 dark:text-zinc-400">العملة: </span><span>{quotation.currencyCode || 'SAR'}</span></div>
            <div><span className="text-gray-500 dark:text-zinc-400">شروط الدفع: </span><span>{quotation.paymentTerms || '-'}</span></div>
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
              {(quotation.items || []).map((item: any, idx: number) => (
                <tr key={item.id || idx} className="table-row">
                  <td className="px-3 py-2 text-sm">{item.productName || item.product_id || '-'}</td>
                  <td className="px-3 py-2 text-sm">{item.quantity}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item.unitPrice || item.unit_price || 0)}</td>
                  <td className="px-3 py-2 text-sm">{formatCurrency(item.discount || 0)}</td>
                  <td className="px-3 py-2 text-sm font-medium">{formatCurrency(item.totalPrice || item.total_price || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="card space-y-4">
          <h3 className="text-lg font-semibold">الملخص المالي</h3>
          <div className="space-y-3">
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع</span><span>{formatCurrency(quotation.totalAmount || 0)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة</span><span>{formatCurrency(quotation.taxAmount || 0)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الخصم</span><span>{formatCurrency(quotation.discount || 0)}</span></div>
            <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-3">
              <span>الإجمالي</span><span className="text-primary-600">{formatCurrency(quotation.finalAmount || 0)}</span>
            </div>
          </div>
          {quotation.notes && (
            <div className="mt-4 pt-4 border-t border-gray-200 dark:border-zinc-700">
              <p className="text-sm text-gray-500 dark:text-zinc-400">ملاحظات:</p>
              <p className="text-sm mt-1">{quotation.notes}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
