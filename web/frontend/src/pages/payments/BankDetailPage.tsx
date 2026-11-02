import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBanks, getBankTransactions, createBankTransaction } from '@/api/payments';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { formatCurrency, formatDate } from '@/lib/utils';

export default function BankDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showTxModal, setShowTxModal] = useState(false);
  const [page, setPage] = useState(1);

  const { data: banks, isLoading: banksLoading } = useQuery({ queryKey: ['banks'], queryFn: getBanks });
  const bank = banks?.items?.find((b: any) => String(b.id) === id);

  const { data: transactions, isLoading: txLoading } = useQuery({
    queryKey: ['bank-transactions', id, page],
    queryFn: () => getBankTransactions(id!, { page, per_page: 20 }),
    enabled: !!id,
  });

  const createTxMutation = useMutation({
    mutationFn: (data: any) => createBankTransaction(id!, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bank-transactions', id] });
      queryClient.invalidateQueries({ queryKey: ['banks'] });
      setShowTxModal(false);
      reset();
      toast.success('تم تسجيل الحركة بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'transaction_type', header: 'النوع', render: (item) => (
        item.transaction_type === 'deposit'
          ? <span className="badge-success">إيداع</span>
          : <span className="badge-danger">سحب</span>
      ) },
    { key: 'amount', header: 'المبلغ', sortable: true, render: (item) => (
        <span className={`font-bold ${item.transaction_type === 'deposit' ? 'text-green-600' : 'text-red-600'}`}>
          {item.transaction_type === 'deposit' ? '+' : '−'} {formatCurrency(Number(item.amount))}
        </span>
      ) },
    { key: 'transaction_date', header: 'التاريخ', sortable: true, render: (item) => formatDate(String(item.transaction_date || item.created_at || '')) },
    { key: 'reference_number', header: 'مرجع', render: (item) => <span className="font-mono text-xs">{String(item.reference_number || '-')}</span> },
    { key: 'description', header: 'البيان', render: (item) => <span className="text-sm">{String(item.description || '-')}</span> },
    { key: 'reconciled', header: 'التسوية', render: (item) => item.reconciled ? <span className="badge-success">تسوية</span> : <span className="badge-info">غير مسوّى</span> },
  ];

  if (banksLoading && !bank) return <PageLoader />;
  if (!bank) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">الحساب البنكي غير موجود</div>;

  return (
    <div className="space-y-6">
      <PageHeader
        title={String(bank.name)}
        subtitle={bank.accountNumber || bank.account_number ? `رقم الحساب ${bank.accountNumber || bank.account_number}` : 'خدمة الحسابات البنكية'}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11m16-11v11M8 14v3m4-3v3m4-3v3" /></svg>}
        actions={
          <>
            <button onClick={() => setShowTxModal(true)} className="btn-primary">+ حركة جديدة</button>
            <button onClick={() => navigate('/payments/banks')} className="btn-secondary">رجوع</button>
          </>
        }
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card p-4">
          <p className="text-sm text-gray-500 dark:text-zinc-400">الرصيد الحالي</p>
          <p className="text-2xl font-bold text-green-600">{formatCurrency(Number(bank.balance ?? bank.current_balance ?? 0))}</p>
          <p className="text-xs text-gray-500 dark:text-zinc-400">{String(bank.currency || 'SAR')}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500 dark:text-zinc-400">رقم الحساب</p>
          <p className="font-mono text-lg font-medium">{String(bank.accountNumber || bank.account_number || '-')}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500 dark:text-zinc-400">IBAN</p>
          <p className="font-mono text-sm break-all">{String(bank.iban || '-')}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500 dark:text-zinc-400">الحالة</p>
          <p className="text-lg font-medium">{bank.isActive ?? bank.is_active ? 'نشط' : 'غير نشط'}</p>
        </div>
      </div>

      <div className="card overflow-hidden">
        <h3 className="text-lg font-semibold p-4 pb-0">حركات الحساب</h3>
        <div className="p-4 pt-2">
          <DataTable
            columns={columns}
            data={(transactions?.items || []) as unknown as Record<string, unknown>[]}
            loading={txLoading}
            totalItems={transactions?.total || 0}
            page={page}
            pageSize={20}
            onPageChange={setPage}
          />
        </div>
      </div>

      <Modal isOpen={showTxModal} onClose={() => { setShowTxModal(false); reset(); }} title={`حركة جديدة - ${bank.name}`} size="sm">
        <form onSubmit={handleSubmit((d) => createTxMutation.mutate({
          transaction_type: d.transaction_type,
          amount: Number(d.amount),
          transaction_date: d.transaction_date || new Date().toISOString().split('T')[0],
          reference_number: d.reference_number,
          description: d.description,
        }))} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">نوع الحركة</label>
              <select {...register('transaction_type')} className="input">
                <option value="deposit">إيداع</option>
                <option value="withdrawal">سحب</option>
              </select>
            </div>
            <div>
              <label className="label">المبلغ *</label>
              <input type="number" step="0.01" {...register('amount', { required: true, min: 0 })} className="input" placeholder="0.00" />
            </div>
          </div>
          <div>
            <label className="label">التاريخ</label>
            <input type="date" {...register('transaction_date')} defaultValue={new Date().toISOString().split('T')[0]} className="input" />
          </div>
          <div>
            <label className="label">رقم المرجع</label>
            <input {...register('reference_number')} className="input" placeholder="رقم الإيصال / السند" />
          </div>
          <div>
            <label className="label">البيان</label>
            <textarea {...register('description')} className="input" rows={2} placeholder="وصف الحركة..." />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowTxModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createTxMutation.isPending}>
              {createTxMutation.isPending ? 'جاري الحفظ...' : 'حفظ الحركة'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}