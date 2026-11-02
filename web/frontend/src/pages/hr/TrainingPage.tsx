import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getTraining, createTraining, updateTraining, deleteTraining, getEmployees } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRTraining } from '@/types';

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'planned', label: 'مخطط' },
  { key: 'in_progress', label: 'قيد التنفيذ' },
  { key: 'completed', label: 'مكتمل' },
  { key: 'cancelled', label: 'ملغي' },
];

export default function TrainingPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRTraining | null>(null);
  const [showDelete, setShowDelete] = useState<HRTraining | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '', courseName: '', provider: '', startDate: '', endDate: '', cost: '', certificate: false, status: 'planned', notes: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-training', page, statusFilter],
    queryFn: () => getTraining({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createTraining({
      employeeId: Number(form.employeeId),
      courseName: form.courseName,
      provider: form.provider || undefined,
      startDate: form.startDate,
      endDate: form.endDate || undefined,
      cost: form.cost ? Number(form.cost) : undefined,
      certificate: form.certificate,
      status: form.status,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-training'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updateTraining(editing!.id, {
      courseName: form.courseName,
      provider: form.provider || undefined,
      startDate: form.startDate,
      endDate: form.endDate || undefined,
      cost: form.cost ? Number(form.cost) : undefined,
      certificate: form.certificate,
      status: form.status,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-training'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteTraining,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-training'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', courseName: '', provider: '', startDate: '', endDate: '', cost: '', certificate: false, status: 'planned', notes: '' });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (t: HRTraining) => {
    setEditing(t);
    setForm({
      employeeId: String(t.employeeId),
      courseName: t.courseName,
      provider: t.provider || '',
      startDate: t.startDate || '',
      endDate: t.endDate || '',
      cost: t.cost ? String(t.cost) : '',
      certificate: Boolean(t.certificate),
      status: t.status || 'planned',
      notes: t.notes || '',
    });
    setShowModal(true);
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId) as any;
    return emp ? (emp.fullName || emp.full_name || `#${empId}`) : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'courseName', header: 'الدورة', render: (item) => <span className="font-bold">{String(item.courseName)}</span> },
    { key: 'provider', header: 'مقدم التدريب', render: (item) => String(item.provider || '-') },
    { key: 'startDate', header: 'تاريخ البداية', render: (item) => formatDate(String(item.startDate)) },
    { key: 'endDate', header: 'تاريخ النهاية', render: (item) => formatDate(String(item.endDate || '')) },
    { key: 'cost', header: 'التكلفة', render: (item) => formatCurrency(Number(item.cost || 0)) },
    { key: 'certificate', header: 'شهادة', render: (item) => item.certificate ? <span className="text-emerald-600">نعم</span> : <span className="text-gray-400">لا</span> },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRTraining)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRTraining)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="التدريب والتطوير"
          subtitle={`${data?.total || 0} برنامج تدريبي`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={openAdd} className="btn-primary">برنامج تدريبي جديد</button>}
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

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل البرنامج التدريبي' : 'برنامج تدريبي جديد'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الموظف</label>
              <select value={form.employeeId} onChange={(e) => setForm({ ...form, employeeId: e.target.value })} className={inputClass} disabled={!!editing}>
                <option value="">اختر الموظف...</option>
                {employees.map((e: any) => <option key={e.id} value={e.id}>{(e.fullName || e.full_name)} {e.code ? `(${e.code})` : ''}</option>)}
              </select>
            </div>
            <div>
              <label className="label">اسم الدورة</label>
              <input value={form.courseName} onChange={(e) => setForm({ ...form, courseName: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">مقدم التدريب</label>
              <input value={form.provider} onChange={(e) => setForm({ ...form, provider: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">التكلفة</label>
              <input type="number" min="0" step="0.01" value={form.cost} onChange={(e) => setForm({ ...form, cost: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">تاريخ البداية</label>
              <input type="date" value={form.startDate} onChange={(e) => setForm({ ...form, startDate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">تاريخ النهاية</label>
              <input type="date" value={form.endDate} onChange={(e) => setForm({ ...form, endDate: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الحالة</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}>
                {statusTabs.filter((t) => t.key !== 'all').map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
              </select>
            </div>
            <div className="flex items-end pb-2">
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input type="checkbox" checked={form.certificate} onChange={(e) => setForm({ ...form, certificate: e.target.checked })} className="rounded" />
                يحصل على شهادة
              </label>
            </div>
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setEditing(null); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editing ? updateMutation : createMutation).mutate()}
              disabled={!form.employeeId || !form.courseName || !form.startDate || createMutation.isPending || updateMutation.isPending}
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
        title="حذف البرنامج التدريبي"
        message={`هل أنت متأكد من حذف "${showDelete?.courseName}"؟`}
        variant="danger"
      />
    </div>
  );
}
