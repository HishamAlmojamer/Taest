import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getBanks, createBank } from '@/api/payments';
import { formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';

export default function BanksPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const navigate = useNavigate();
  const [showModal, setShowModal] = useState(false);

  const { data: banks, isLoading } = useQuery({ queryKey: ['banks'], queryFn: getBanks });

  const createMutation = useMutation({
    mutationFn: createBank,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['banks'] });
      setShowModal(false);
      toast.success('تم إنشاء الحساب البنكي بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم البنك', sortable: true, render: (item) => (
        <button onClick={() => navigate(`/payments/banks/${String(item.id)}`)} className="font-medium text-primary-600 hover:underline">
          {String(item.name)}
        </button>
      ) },
    { key: 'accountNumber', header: 'رقم الحساب', render: (item) => <span className="font-mono text-xs">{String(item.accountNumber)}</span> },
    { key: 'iban', header: 'IBAN', render: (item) => <span className="font-mono text-xs">{String(item.iban || '-')}</span> },
    { key: 'balance', header: 'الرصيد', sortable: true, render: (item) => <span className="font-bold">{formatCurrency(Number(item.balance))}</span> },
    { key: 'currency', header: 'العملة', render: (item) => <span className="badge-info">{String(item.currency || 'SAR')}</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="الحسابات البنكية"
        subtitle="إدارة الحسابات البنكية والأرصدة"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11m16-11v11M8 14v3m4-3v3m4-3v3" /></svg>}
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ حساب بنكي جديد</button>}
      />
      <DataTable columns={columns} data={(banks?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={banks?.total || 0} page={1} pageSize={100} onPageChange={() => {}} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="حساب بنكي جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({ bankName: d.name, accountName: d.name, accountNumber: d.accountNumber, iban: d.iban, currencyId: 1 } as never))} className="space-y-4">
          <div><label className="label">اسم البنك</label><input {...register('name', { required: true })} className="input" placeholder="مثال: البنك الأهلي السعودي" /></div>
          <div><label className="label">رقم الحساب</label><input {...register('accountNumber', { required: true })} className="input" /></div>
          <div><label className="label">IBAN</label><input {...register('iban')} className="input" placeholder="SA00 0000 0000 0000 0000 0000" /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>{createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
