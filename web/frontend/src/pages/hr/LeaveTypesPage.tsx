import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getLeaveTypes, createLeaveType, updateLeaveType, deleteLeaveType, getLeaveBalances, initLeaveBalances, updateLeaveBalance, getEmployees } from '@/api/hr';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRLeaveType, HRLeaveBalance } from '@/types';

export default function LeaveTypesPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'types' | 'balances'>('types');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRLeaveType | null>(null);
  const [showDelete, setShowDelete] = useState<HRLeaveType | null>(null);
  const toast = useToast();
  const [year, setYear] = useState(new Date().getFullYear());

  const [form, setForm] = useState({
    code: '', name: '', nameEn: '', daysPerYear: '30', isPaid: true, maxConsecutiveDays: '', requiresApproval: true,
  });

  const { data, isLoading } = useQuery({ queryKey: ['hr-leave-types'], queryFn: getLeaveTypes });
  const items = data?.items || [];

  const { data: balancesData, isLoading: balancesLoading } = useQuery({
    queryKey: ['hr-leave-balances', year],
    queryFn: () => getLeaveBalances({ year }),
  });
  const balances = balancesData?.items || [];

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createLeaveType({
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      daysPerYear: Number(form.daysPerYear) || 0,
      isPaid: form.isPaid,
      maxConsecutiveDays: form.maxConsecutiveDays ? Number(form.maxConsecutiveDays) : undefined,
      requiresApproval: form.requiresApproval,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-leave-types'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updateLeaveType(editing!.id, {
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      daysPerYear: Number(form.daysPerYear) || 0,
      isPaid: form.isPaid,
      maxConsecutiveDays: form.maxConsecutiveDays ? Number(form.maxConsecutiveDays) : undefined,
      requiresApproval: form.requiresApproval,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-leave-types'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteLeaveType,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-leave-types'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const initMutation = useMutation({
    mutationFn: initLeaveBalances,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-leave-balances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const balanceUpdate = useMutation({
    mutationFn: (b: { id: number; data: Partial<HRLeaveBalance> }) => updateLeaveBalance(b.id, b.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-leave-balances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ code: '', name: '', nameEn: '', daysPerYear: '30', isPaid: true, maxConsecutiveDays: '', requiresApproval: true });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (lt: HRLeaveType) => {
    setEditing(lt);
    setForm({
      code: lt.code,
      name: lt.name,
      nameEn: lt.nameEn || '',
      daysPerYear: String(lt.daysPerYear ?? 0),
      isPaid: Boolean(lt.isPaid),
      maxConsecutiveDays: lt.maxConsecutiveDays ? String(lt.maxConsecutiveDays) : '',
      requiresApproval: Boolean(lt.requiresApproval),
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded">{String(item.code || '-')}</span> },
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'daysPerYear', header: 'أيام/سنة', render: (item) => <span className="font-bold text-primary-600">{String(item.daysPerYear)}</span> },
    { key: 'isPaid', header: 'مدفوعة', render: (item) => item.isPaid ? <span className="text-emerald-600">مدفوعة</span> : <span className="text-gray-400">بدون راتب</span> },
    { key: 'maxConsecutiveDays', header: 'الحد الأقصى المتتالي', render: (item) => String(item.maxConsecutiveDays || '-') },
    { key: 'requiresApproval', header: 'تتطلب موافقة', render: (item) => item.requiresApproval ? 'نعم' : 'لا' },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRLeaveType)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRLeaveType)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const balanceColumns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{String(item.employeeName)}</span> },
    { key: 'leaveTypeName', header: 'النوع', render: (item) => String(item.leaveTypeName) },
    { key: 'daysEntitled', header: 'المستحق', render: (item) => <span className="font-bold text-primary-600">{String(item.daysEntitled)}</span> },
    { key: 'daysUsed', header: 'المستخدم', render: (item) => <span className="text-amber-600">{String(item.daysUsed)}</span> },
    { key: 'daysRemaining', header: 'المتبقي', render: (item) => <span className="text-emerald-600">{String(item.daysRemaining)}</span> },
    { key: 'notes', header: 'ملاحظات', render: (item) => String(item.notes || '-') },
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="أنواع الإجازات وأرصدتها"
          subtitle={tab === 'types' ? `${data?.total || 0} نوع إجازة` : `${balances.length} رصيد`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={tab === 'types'
            ? <button onClick={openAdd} className="btn-primary">نوع إجازة جديد</button>
            : (
              <div className="flex items-center gap-2">
                <input type="number" value={year} onChange={(e) => setYear(Number(e.target.value) || new Date().getFullYear())} className={`${inputClass} w-28`} />
                <button onClick={() => initMutation.mutate(year)} disabled={initMutation.isPending} className="btn-secondary">
                  {initMutation.isPending ? 'جاري التهيئة...' : 'تهيئة الأرصدة'}
                </button>
              </div>
            )}
        />
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        <button onClick={() => setTab('types')} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'types' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
          أنواع الإجازات
        </button>
        <button onClick={() => setTab('balances')} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'balances' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
          الأرصدة ({employees.length} موظف)
        </button>
      </div>

      {tab === 'types' ? (
        <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} pageSize={20} keepPreviousData />
      ) : (
        <DataTable columns={balanceColumns} data={balances as any} loading={balancesLoading} totalItems={balances.length} pageSize={20} keepPreviousData />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل نوع الإجازة' : 'نوع إجازة جديد'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الكود</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الاسم</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">الاسم (إنجليزي)</label>
            <input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">أيام/سنة</label>
              <input type="number" min="0" value={form.daysPerYear} onChange={(e) => setForm({ ...form, daysPerYear: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الحد الأقصى المتتالي (أيام)</label>
              <input type="number" min="0" value={form.maxConsecutiveDays} onChange={(e) => setForm({ ...form, maxConsecutiveDays: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.isPaid} onChange={(e) => setForm({ ...form, isPaid: e.target.checked })} className="rounded" />
              إجازة مدفوعة
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.requiresApproval} onChange={(e) => setForm({ ...form, requiresApproval: e.target.checked })} className="rounded" />
              تتطلب موافقة
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setEditing(null); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editing ? updateMutation : createMutation).mutate()}
              disabled={!form.code || !form.name || createMutation.isPending || updateMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending || updateMutation.isPending ? 'جاري الحفظ...' : editing ? 'تحديث' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={showDelete !== null}
        onClose={() => setShowDelete(null)}
        onConfirm={() => showDelete && deleteMutation.mutate(showDelete.id)}
        title="حذف نوع الإجازة"
        message={`هل أنت متأكد من حذف "${showDelete?.name}"؟`}
        variant="danger"
      />
    </div>
  );
}
