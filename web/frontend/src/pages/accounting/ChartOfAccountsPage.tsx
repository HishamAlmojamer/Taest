import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getAccounts, createAccount } from '@/api/accounting';
import { Modal } from '@/components/ui/Modal';
import { TreeView } from '@/components/ui/TreeView';
import { useForm } from 'react-hook-form';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { EmptyState } from '@/components/ui/EmptyState';
import { formatCurrency } from '@/lib/utils';

interface AccountNode {
  id: string;
  code: string;
  name: string;
  type: string;
  balance: number;
  children?: AccountNode[];
}

export default function ChartOfAccountsPage() {
  const [showModal, setShowModal] = useState(false);
  const queryClient = useQueryClient();
  const { data: accounts, isLoading } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  });

  const createMutation = useMutation({
    mutationFn: createAccount,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['accounts'] }); setShowModal(false); },
  });

  const { register, handleSubmit, reset } = useForm();

  if (isLoading) return <LoadingSpinner />;

  const typeLabels: Record<string, string> = {
    ASSET: 'الأصول', LIABILITY: 'الخصوم', EQUITY: 'حقوق الملكية', REVENUE: 'الإيرادات', EXPENSE: 'المصروفات',
  };

  const treeData = ((accounts as any)?.items || []).map((a: any) => ({
    id: a.id,
    code: a.code,
    label: a.name,
    meta: <span className={a.balance >= 0 ? 'text-gray-700 dark:text-zinc-300' : 'text-red-600 dark:text-red-400'}>{formatCurrency(a.balance)}</span>,
    children: a.children?.map((c: any) => ({
      id: c.id,
      code: c.code,
      label: c.name,
      meta: <span className={c.balance >= 0 ? 'text-gray-700 dark:text-zinc-300' : 'text-red-600 dark:text-red-400'}>{formatCurrency(c.balance)}</span>,
      children: c.children?.map((gc: any) => ({
        id: gc.id,
        code: gc.code,
        label: gc.name,
        meta: <span className={gc.balance >= 0 ? 'text-gray-700 dark:text-zinc-300' : 'text-red-600 dark:text-red-400'}>{formatCurrency(gc.balance)}</span>,
      })),
    })),
  }));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">دليل الحسابات</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ حساب جديد</button>
      </div>

      {treeData.length === 0 ? (
        <EmptyState title="لا توجد حسابات" description="ابدأ بإضافة حسابات في الدليل المحاسبي" />
      ) : (
        <TreeView
          nodes={treeData}
          searchable
          searchPlaceholder="بحث في الحسابات..."
          onSelect={(node) => console.log('Selected:', node)}
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="حساب جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          accountCode: d.code,
          accountName: d.name,
          accountNameEn: d.nameEn,
          accountType: d.type,
        } as never))} className="space-y-4">
          <div>
            <label className="label">كود الحساب</label>
            <input {...register('code', { required: true })} className="input" />
          </div>
          <div>
            <label className="label">اسم الحساب</label>
            <input {...register('name', { required: true })} className="input" />
          </div>
          <div>
            <label className="label">الاسم بالإنجليزية</label>
            <input {...register('nameEn')} className="input" />
          </div>
          <div>
            <label className="label">نوع الحساب</label>
            <select {...register('type', { required: true })} className="input">
              {Object.entries(typeLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
