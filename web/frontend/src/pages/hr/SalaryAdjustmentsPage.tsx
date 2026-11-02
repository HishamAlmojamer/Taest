import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getBonuses, createBonus, approveBonus, deleteBonus, getEmployees } from '@/api/hr';
import { formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const typeTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'bonus', label: 'المكافآت' },
  { key: 'deduction', label: 'الخصومات' },
];

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'pending', label: 'قيد الانتظار' },
  { key: 'approved', label: 'معتمد' },
  { key: 'rejected', label: 'مرفوض' },
];

const bonusTypes = [
  { value: 'bonus', label: 'مكافأة' },
  { value: 'deduction', label: 'خصم' },
  { value: 'performance', label: 'مكافأة أداء' },
  { value: 'overtime', label: 'تعويض إضافي' },
  { value: 'other', label: 'أخرى' },
];

export default function SalaryAdjustmentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [typeFilter, setTypeFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: string } | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '', bonusType: 'bonus', amount: '', period: '', description: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-bonuses', page, typeFilter, statusFilter],
    queryFn: () => getBonuses({
      page,
      per_page: 10,
      bonus_type: typeFilter !== 'all' ? typeFilter : undefined,
      status: statusFilter !== 'all' ? statusFilter : undefined,
    }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createBonus({
      employeeId: Number(form.employeeId),
      bonusType: form.bonusType,
      amount: Number(form.amount) || 0,
      period: form.period || undefined,
      description: form.description || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-bonuses'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: approveBonus,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-bonuses'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteBonus,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-bonuses'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', bonusType: 'bonus', amount: '', period: '', description: '' });
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId) as any;
    return emp ? (emp.fullName || emp.full_name || `#${empId}`) : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'bonusType', header: 'النوع', render: (item) => {
      const type = String(item.bonusType || '');
      const isDeduction = type === 'deduction';
      return <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${isDeduction ? 'bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400' : 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400'}`}>
        {isDeduction ? 'خصم' : type === 'bonus' ? 'مكافأة' : type}
      </span>;
    }},
    { key: 'amount', header: 'المبلغ', render: (item) => {
      const isDeduction = String(item.bonusType) === 'deduction';
      return <span className={`font-bold ${isDeduction ? 'text-red-600 dark:text-red-400' : 'text-primary-600'}`}>
        {isDeduction ? '- ' : '+ '}{formatCurrency(Number(item.amount))}
      </span>;
    }},
    { key: 'period', header: 'الفترة', render: (item) => String(item.period || '-') },
    { key: 'description', header: 'الوصف', render: (item) => String(item.description || '-') },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => {
      const id = Number(item.id);
      if (item.status === 'pending') return (
        <div className="flex gap-1">
          <button onClick={() => setConfirmAction({ id, action: 'approve' })} className="text-green-600 hover:text-green-700 text-xs font-medium bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded">اعتماد</button>
          <button onClick={() => setConfirmAction({ id, action: 'delete' })} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
        </div>
      );
      return (
        <button onClick={() => setConfirmAction({ id, action: 'delete' })} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      );
    }},
  ];

  const handleConfirm = () => {
    if (!confirmAction) return;
    const { id, action } = confirmAction;
    if (action === 'approve') approveMutation.mutate(id);
    else if (action === 'delete') deleteMutation.mutate(id);
    setConfirmAction(null);
  };

  const confirmMessages: Record<string, { title: string; message: string }> = {
    approve: { title: 'اعتماد السجل', message: 'هل أنت متأكد من اعتماد هذا السجل؟' },
    delete: { title: 'حذف السجل', message: 'هل أنت متأكد من حذف هذا السجل؟ لا يمكن التراجع عن هذا الإجراء.' },
  };

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  const currentMonth = new Date().toISOString().slice(0, 7);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="المكافآت والخصومات"
          subtitle={`${data?.total || 0} سجل`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={() => setShowModal(true)} className="btn-primary">سجل جديد</button>}
        />
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        {typeTabs.map((tab) => (
          <button key={tab.key} onClick={() => { setTypeFilter(tab.key); setPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${typeFilter === tab.key ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
            {tab.label}
          </button>
        ))}
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        {statusTabs.map((tab) => (
          <button key={tab.key} onClick={() => { setStatusFilter(tab.key); setPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${statusFilter === tab.key ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
            {tab.label}
          </button>
        ))}
      </div>

      <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} keepPreviousData />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm(); }} title="سجل مكافأة / خصم جديد" size="md">
        <div className="space-y-4">
          <div>
            <label className="label">الموظف</label>
            <select value={form.employeeId} onChange={(e) => setForm({ ...form, employeeId: e.target.value })} className={inputClass}>
              <option value="">اختر الموظف...</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{(e.fullName || e.full_name)} {e.code ? `(${e.code})` : ''}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">النوع</label>
              <select value={form.bonusType} onChange={(e) => setForm({ ...form, bonusType: e.target.value })} className={inputClass}>
                {bonusTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">المبلغ</label>
              <input type="number" min="0" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className={inputClass} placeholder="0.00" />
            </div>
          </div>
          <div>
            <label className="label">الفترة (شهر/سنة)</label>
            <input type="month" value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })} className={inputClass} placeholder={currentMonth} />
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.employeeId || !form.amount || Number(form.amount) <= 0 || createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={confirmAction !== null}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirm}
        title={confirmAction ? confirmMessages[confirmAction.action]?.title : ''}
        message={confirmAction ? confirmMessages[confirmAction.action]?.message : ''}
        variant={confirmAction?.action === 'delete' ? 'danger' : 'warning'}
      />
    </div>
  );
}
