import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getCustomerPayments, createCustomerPayment } from '@/api/payments';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';

const METHODS: Record<string, string> = { CASH: 'نقدي', BANK_TRANSFER: 'تحويل بنكي', CHECK: 'شيك', CREDIT_CARD: 'بطاقة ائتمان' };

export default function CustomerPaymentsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['customer-payments', page],
    queryFn: () => getCustomerPayments({ page, pageSize: 10 }),
  });

  const createMutation = useMutation({
    mutationFn: createCustomerPayment,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['customer-payments'] });
      setShowModal(false);
      toast.success('تم تسجيل الدفعة بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'paymentNumber', header: 'رقم الدفعة', render: (item) => <span className="font-medium text-primary-600">{String(item.paymentNumber)}</span> },
    { key: 'customerName', header: 'العميل', sortable: true, render: (item) => String(item.customerName) },
    { key: 'amount', header: 'المبلغ', sortable: true, render: (item) => <span className="font-bold">{formatCurrency(Number(item.amount))}</span> },
    { key: 'method', header: 'الطريقة', render: (item) => <span className="badge-info">{METHODS[String(item.method)] || String(item.method)}</span> },
    { key: 'date', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.date)) },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="مدفوعات العملاء"
        subtitle="تسجيل ومتابعة مدفوعات العملاء"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ دفعة جديدة</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="دفعة جديدة من عميل" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          customerId: Number(d.customerId), amount: d.amount, paymentMethod: d.method, paymentDate: d.date, notes: d.notes,
        } as never))} className="space-y-4">
          <div><label className="label">العميل (ID)</label><input {...register('customerId', { required: true })} className="input" type="number" /></div>
          <div><label className="label">المبلغ</label><input {...register('amount', { required: true, valueAsNumber: true })} type="number" className="input" /></div>
          <div>
            <label className="label">طريقة الدفع</label>
            <select {...register('method', { required: true })} className="input">
              {Object.entries(METHODS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div><label className="label">التاريخ</label><input {...register('date')} type="date" className="input" defaultValue={new Date().toISOString().split('T')[0]} /></div>
          <div><label className="label">ملاحظات</label><textarea {...register('notes')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>{createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
