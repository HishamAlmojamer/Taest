import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getPurchases, getPurchase, submitPurchase, approvePurchase, rejectPurchase, voidPurchase, deletePurchase } from '@/api/purchases';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { useToast } from '@/components/ui/Toast';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';

export default function PurchasesListPage() {
  const navigate = useNavigate();
  const company = useCompany();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [printId, setPrintId] = useState<string | null>(null);
  const [voidTarget, setVoidTarget] = useState<Record<string, unknown> | null>(null);
  const [voidReason, setVoidReason] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<Record<string, unknown> | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['purchases', page, search],
    queryFn: () => getPurchases({ page, pageSize: 10, search }),
  });

  const { data: printData } = useQuery({
    queryKey: ['purchase', printId],
    queryFn: () => getPurchase(printId!),
    enabled: !!printId,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['purchases'] });

  const submitMutation = useMutation({
    mutationFn: (id: string) => submitPurchase(id),
    onSuccess: () => { invalidate(); toast.success('تم إرسال أمر الشراء بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const approveMutation = useMutation({
    mutationFn: (id: string) => approvePurchase(id),
    onSuccess: () => { invalidate(); toast.success('تم اعتماد أمر الشراء'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const rejectMutation = useMutation({
    mutationFn: (id: string) => rejectPurchase(id),
    onSuccess: () => { invalidate(); toast.warning('تم رفض أمر الشراء'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const voidMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => voidPurchase(id, reason),
    onSuccess: () => { invalidate(); toast.warning('تم إلغاء أمر الشراء'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const deleteMutation = useMutation({
    mutationFn: (id: string) => deletePurchase(id),
    onSuccess: () => { invalidate(); toast.success('تم حذف أمر الشراء'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const runVoid = (item: Record<string, unknown>) => {
    setVoidTarget(item);
    setVoidReason('');
  };

  const confirmVoid = () => {
    if (voidTarget && voidReason.trim()) {
      voidMutation.mutate({ id: String(voidTarget.id), reason: voidReason });
      setVoidTarget(null);
      setVoidReason('');
    }
  };

  const runDelete = (item: Record<string, unknown>) => {
    setDeleteTarget(item);
  };

  const actions = (item: Record<string, unknown>) => {
    const state = String(item.workflowState || item.status || 'draft').toLowerCase();
    const busy = submitMutation.isPending || approveMutation.isPending || rejectMutation.isPending || voidMutation.isPending || deleteMutation.isPending;
    return (
      <div className="flex items-center gap-1">
        {state === 'draft' && (
          <button onClick={() => submitMutation.mutate(String(item.id))} disabled={busy} className="btn-primary text-xs px-2 py-1">إرسال</button>
        )}
        {state === 'submitted' && (
          <>
            <button onClick={() => approveMutation.mutate(String(item.id))} disabled={busy} className="text-xs font-medium px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700">اعتماد</button>
            <button onClick={() => rejectMutation.mutate(String(item.id))} disabled={busy} className="text-xs font-medium px-2 py-1 rounded bg-red-500 text-white hover:bg-red-600">رفض</button>
          </>
        )}
        {state === 'approved' && (
          <button onClick={() => runVoid(item)} disabled={busy} className="text-xs font-medium px-2 py-1 rounded border border-red-300 text-red-600 hover:bg-red-50 dark:border-red-700 dark:text-red-400">إلغاء</button>
        )}
        {(state === 'draft' || state === 'rejected' || state === 'voided') && (
          <button onClick={() => runDelete(item)} disabled={busy} className="text-xs font-medium px-2 py-1 rounded border border-gray-300 text-gray-500 hover:bg-gray-50 dark:border-zinc-700 dark:text-zinc-400">حذف</button>
        )}
        <button onClick={() => setPrintId(String(item.id))} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">طباعة</button>
      </div>
    );
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'orderNumber', header: 'رقم الطلب', sortable: true, render: (item) => (
      <button onClick={() => navigate(`/purchases/${String(item.id)}`)} className="font-medium text-primary-600 hover:underline">
        {String(item.invoiceNumber || item.orderNumber || item.id || '-')}
      </button>
    ) },
    { key: 'supplierName', header: 'المورد', sortable: true, render: (item) => String(item.supplierName || '-') },
    { key: 'date', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.createdAt || item.date || '')) },
    { key: 'total', header: 'المبلغ', sortable: true, render: (item) => formatCurrency(Number(item.finalAmount || item.total || 0)) },
    { key: 'paymentStatus', header: 'الدفع', render: (item) => <StatusBadge status={String(item.paymentStatus || 'pending')} /> },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.workflowState || item.status || 'DRAFT')} /> },
    { key: 'actions', header: 'إجراءات', render: actions },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="أوامر الشراء"
        subtitle="إدارة أوامر الشراء من الموردين"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>}
        actions={<button onClick={() => navigate('/purchases/new')} className="btn-primary">+ أمر شراء جديد</button>}
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
        searchPlaceholder="بحث برقم الطلب أو اسم المورد..."
      />
      <PrintPreviewModal
        isOpen={printId !== null}
        onClose={() => setPrintId(null)}
        title={`أمر شراء ${printData?.orderNumber || ''}`}
        filename={`أمر-شراء-${printData?.orderNumber || printId || 'purchase'}`}
      >
        {printData ? (
          <PrintDocument
            company={company}
            title="أمر شراء"
            meta={[
              { label: 'رقم الأمر', value: printData.orderNumber || printData.invoiceNumber || '-' },
              { label: 'التاريخ', value: formatDate(printData.date) },
              { label: 'المورد', value: printData.supplierName || '-' },
              { label: 'تاريخ الاستحقاق', value: formatDate(printData.dueDate) },
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
                {(printData.items || []).map((item: any, idx: number) => (
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
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(printData.subtotal || 0)}</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 border border-gray-300" colSpan={5}>الضريبة</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(printData.taxAmount || 0)}</td>
                </tr>
                <tr>
                  <td className="px-3 py-2 border border-gray-300" colSpan={5}>الخصم</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(printData.discount || 0)}</td>
                </tr>
                <tr className="bg-gray-100 font-bold">
                  <td className="px-3 py-2 border border-gray-300" colSpan={5}>الإجمالي</td>
                  <td className="px-3 py-2 border border-gray-300 text-primary-600">{formatCurrency(printData.total || 0)}</td>
                </tr>
              </tbody>
            </table>
            {printData.notes && (
              <div className="mt-4">
                <p className="text-sm font-semibold text-gray-700 mb-1">ملاحظات:</p>
                <p className="text-sm text-gray-600">{printData.notes}</p>
              </div>
            )}
            <div className="mt-10 grid grid-cols-2 gap-8 text-center text-sm text-gray-700">
              <div><p className="border-t border-gray-400 pt-2 font-medium">توقيع المستلم</p></div>
              <div><p className="border-t border-gray-400 pt-2 font-medium">ختم وتوقيع الشركة</p></div>
            </div>
          </PrintDocument>
        ) : null}
      </PrintPreviewModal>

      {/* Void Reason Modal */}
      <Modal isOpen={!!voidTarget} onClose={() => { setVoidTarget(null); setVoidReason(''); }} title="إلغاء أمر الشراء" size="sm">
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-zinc-400">هل أنت متأكد من إلغاء أمر الشراء رقم <strong>{String(voidTarget?.invoiceNumber || voidTarget?.orderNumber || voidTarget?.id)}</strong>؟</p>
          <div>
            <label className="label">سبب الإلغاء *</label>
            <textarea value={voidReason} onChange={(e) => setVoidReason(e.target.value)} className="input" rows={3} placeholder="أدخل سبب الإلغاء..." />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setVoidTarget(null); setVoidReason(''); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={confirmVoid} disabled={!voidReason.trim() || voidMutation.isPending} className="btn-primary bg-orange-600 hover:bg-orange-700 disabled:opacity-50">
              {voidMutation.isPending ? 'جاري الإلغاء...' : 'تأكيد الإلغاء'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => { if (deleteTarget) { deleteMutation.mutate(String(deleteTarget.id)); setDeleteTarget(null); } }}
        title="حذف أمر الشراء"
        message={`هل أنت متأكد من حذف أمر الشراء رقم ${deleteTarget ? String(deleteTarget.invoiceNumber || deleteTarget.orderNumber || deleteTarget.id) : ''}؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        variant="danger"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
