import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getOvertime, createOvertime, approveOvertime, updateOvertimeStatus, deleteOvertime, getEmployees } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'pending', label: 'قيد الانتظار' },
  { key: 'approved', label: 'معتمد' },
  { key: 'rejected', label: 'مرفوض' },
];

export default function OvertimePage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: string } | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '', date: new Date().toISOString().slice(0, 10), hours: '2', rateMultiplier: '1.5', amount: '', reason: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-overtime', page, statusFilter],
    queryFn: () => getOvertime({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createOvertime({
      employeeId: Number(form.employeeId),
      date: form.date,
      hours: Number(form.hours) || 0,
      rateMultiplier: Number(form.rateMultiplier) || 1.5,
      amount: form.amount ? Number(form.amount) : 0,
      reason: form.reason || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-overtime'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: approveOvertime,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-overtime'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: number) => updateOvertimeStatus(id, 'rejected'),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-overtime'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteOvertime,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-overtime'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', date: new Date().toISOString().slice(0, 10), hours: '2', rateMultiplier: '1.5', amount: '', reason: '' });
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId) as any;
    return emp ? (emp.fullName || emp.full_name || `#${empId}`) : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'date', header: 'التاريخ', render: (item) => formatDate(String(item.date)) },
    { key: 'hours', header: 'الساعات', render: (item) => <span className="font-bold">{String(item.hours)}</span> },
    { key: 'rateMultiplier', header: 'المضاعف', render: (item) => `x${String(item.rateMultiplier)}` },
    { key: 'amount', header: 'المبلغ', render: (item) => <span className="font-bold text-primary-600">{formatCurrency(Number(item.amount))}</span> },
    { key: 'reason', header: 'السبب', render: (item) => String(item.reason || '-') },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => {
      const id = Number(item.id);
      if (item.status === 'pending') return (
        <div className="flex gap-1">
          <button onClick={() => setConfirmAction({ id, action: 'approve' })} className="text-green-600 hover:text-green-700 text-xs font-medium bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded">اعتماد</button>
          <button onClick={() => setConfirmAction({ id, action: 'reject' })} className="text-amber-600 hover:text-amber-700 text-xs font-medium bg-amber-50 dark:bg-amber-500/10 px-2 py-1 rounded">رفض</button>
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
    else if (action === 'reject') rejectMutation.mutate(id);
    else if (action === 'delete') deleteMutation.mutate(id);
    setConfirmAction(null);
  };

  const confirmMessages: Record<string, { title: string; message: string }> = {
    approve: { title: 'اعتماد العمل الإضافي', message: 'هل أنت متأكد من اعتماد هذا العمل الإضافي؟' },
    reject: { title: 'رفض العمل الإضافي', message: 'هل أنت متأكد من رفض هذا العمل الإضافي؟' },
    delete: { title: 'حذف العمل الإضافي', message: 'هل أنت متأكد من حذف هذا السجل؟ لا يمكن التراجع عن هذا الإجراء.' },
  };

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="العمل الإضافي"
          subtitle={`${data?.total || 0} سجل`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={() => setShowModal(true)} className="btn-primary">عمل إضافي جديد</button>}
        />
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

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm(); }} title="عمل إضافي جديد" size="md">
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
              <label className="label">التاريخ</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">عدد الساعات</label>
              <input type="number" min="0" step="0.5" value={form.hours} onChange={(e) => setForm({ ...form, hours: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">المضاعف (أساسي 1.5)</label>
              <input type="number" min="1" step="0.25" value={form.rateMultiplier} onChange={(e) => setForm({ ...form, rateMultiplier: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">المبلغ (اختياري — يُحسب تلقائياً)</label>
              <input type="number" min="0" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className={inputClass} placeholder="تلقائي" />
            </div>
          </div>
          <div>
            <label className="label">السبب</label>
            <textarea value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.employeeId || !form.date || !form.hours || Number(form.hours) <= 0 || createMutation.isPending}
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
