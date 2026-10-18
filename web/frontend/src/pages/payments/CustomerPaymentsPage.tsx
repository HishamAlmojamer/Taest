import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getCustomerPayments, createCustomerPayment } from '@/api/payments';
import { formatCurrency, formatDate } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';

export default function CustomerPaymentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['customer-payments', page],
    queryFn: () => getCustomerPayments({ page, pageSize: 10 }),
  });

  const createMutation = useMutation({
    mutationFn: createCustomerPayment,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['customer-payments'] }); setShowModal(false); },
  });

  const { register, handleSubmit, reset } = useForm();
  const methods: Record<string, string> = { CASH: 'نقدي', BANK_TRANSFER: 'تحويل بنكي', CHECK: 'شيك', CREDIT_CARD: 'بطاقة ائتمان' };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'paymentNumber', header: 'رقم الدفعة', render: (item) => <span className="font-medium text-primary-600">{String(item.paymentNumber)}</span> },
    { key: 'customerName', header: 'العميل', render: (item) => String(item.customerName) },
    { key: 'amount', header: 'المبلغ', render: (item) => <span className="font-bold">{formatCurrency(Number(item.amount))}</span> },
    { key: 'method', header: 'الطريقة', render: (item) => methods[String(item.method)] || String(item.method) },
    { key: 'date', header: 'التاريخ', render: (item) => formatDate(String(item.date)) },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">مدفوعات العملاء</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ دفعة جديدة</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="دفعة جديدة من عميل" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          customerId: Number(d.customerId),
          amount: d.amount,
          paymentMethod: d.method,
          paymentDate: d.date,
          notes: d.notes,
        } as never))} className="space-y-4">
          <div><label className="label">العميل</label><input {...register('customerId', { required: true })} className="input" /></div>
          <div><label className="label">المبلغ</label><input {...register('amount', { required: true, valueAsNumber: true })} type="number" className="input" /></div>
          <div>
            <label className="label">طريقة الدفع</label>
            <select {...register('method', { required: true })} className="input">
              {Object.entries(methods).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div><label className="label">التاريخ</label><input {...register('date')} type="date" className="input" defaultValue={new Date().toISOString().split('T')[0]} /></div>
          <div><label className="label">ملاحظات</label><textarea {...register('notes')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
