import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getBanks, createBank } from '@/api/payments';
import { formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';

export default function BanksPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);

  const { data: banks, isLoading } = useQuery({
    queryKey: ['banks'],
    queryFn: getBanks,
  });

  const createMutation = useMutation({
    mutationFn: createBank,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['banks'] }); setShowModal(false); },
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم البنك', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'accountNumber', header: 'رقم الحساب', render: (item) => <span className="font-mono text-xs">{String(item.accountNumber)}</span> },
    { key: 'iban', header: 'IBAN', render: (item) => <span className="font-mono text-xs">{String(item.iban || '-')}</span> },
    { key: 'balance', header: 'الرصيد', render: (item) => <span className="font-bold">{formatCurrency(Number(item.balance))}</span> },
    { key: 'currency', header: 'العملة', render: (item) => String(item.currency || 'SAR') },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الحسابات البنكية</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ حساب بنكي جديد</button>
      </div>
      <DataTable columns={columns} data={(banks?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={banks?.total || 0} page={1} pageSize={100} onPageChange={() => {}} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="حساب بنكي جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          bankName: d.name,
          accountName: d.name,
          accountNumber: d.accountNumber,
          iban: d.iban,
          currencyId: 1,
        } as never))} className="space-y-4">
          <div><label className="label">اسم البنك</label><input {...register('name', { required: true })} className="input" /></div>
          <div><label className="label">رقم الحساب</label><input {...register('accountNumber', { required: true })} className="input" /></div>
          <div><label className="label">IBAN</label><input {...register('iban')} className="input" /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
