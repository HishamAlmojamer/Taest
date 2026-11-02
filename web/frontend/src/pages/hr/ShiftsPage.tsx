import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getShifts, createShift, updateShift, deleteShift } from '@/api/hr';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRShift } from '@/types';

export default function ShiftsPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRShift | null>(null);
  const [showDelete, setShowDelete] = useState<HRShift | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    code: '', name: '', nameEn: '', startTime: '08:00', endTime: '16:00', breakMinutes: '', workingHours: '8',
  });

  const { data, isLoading } = useQuery({ queryKey: ['hr-shifts'], queryFn: getShifts });
  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createShift({
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      startTime: form.startTime,
      endTime: form.endTime,
      breakMinutes: form.breakMinutes ? Number(form.breakMinutes) : undefined,
      workingHours: Number(form.workingHours) || 0,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-shifts'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updateShift(editing!.id, {
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      startTime: form.startTime,
      endTime: form.endTime,
      breakMinutes: form.breakMinutes ? Number(form.breakMinutes) : undefined,
      workingHours: Number(form.workingHours) || 0,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-shifts'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteShift,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-shifts'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ code: '', name: '', nameEn: '', startTime: '08:00', endTime: '16:00', breakMinutes: '', workingHours: '8' });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (shift: HRShift) => {
    setEditing(shift);
    setForm({
      code: shift.code,
      name: shift.name,
      nameEn: shift.nameEn || '',
      startTime: shift.startTime || '08:00',
      endTime: shift.endTime || '16:00',
      breakMinutes: shift.breakMinutes ? String(shift.breakMinutes) : '',
      workingHours: String(shift.workingHours ?? 8),
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded">{String(item.code || '-')}</span> },
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'nameEn', header: 'الاسم (إنجليزي)', render: (item) => String(item.nameEn || '-') },
    { key: 'startTime', header: 'بداية الدوام', render: (item) => String(item.startTime || '-') },
    { key: 'endTime', header: 'نهاية الدوام', render: (item) => String(item.endTime || '-') },
    { key: 'breakMinutes', header: 'الاستراحة (دقيقة)', render: (item) => String(item.breakMinutes || '-') },
    { key: 'workingHours', header: 'ساعات العمل', render: (item) => `${String(item.workingHours ?? 0)} س` },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRShift)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRShift)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="الورديات"
          subtitle={`${data?.total || 0} وردية`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={openAdd} className="btn-primary">وردية جديدة</button>}
        />
      </div>

      <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} pageSize={20} keepPreviousData />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل الوردية' : 'وردية جديدة'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الكود</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">اسم الوردية</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">الاسم (إنجليزي)</label>
            <input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">بداية الدوام</label>
              <input type="time" value={form.startTime} onChange={(e) => setForm({ ...form, startTime: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">نهاية الدوام</label>
              <input type="time" value={form.endTime} onChange={(e) => setForm({ ...form, endTime: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">مدة الاستراحة (دقيقة)</label>
              <input type="number" min="0" value={form.breakMinutes} onChange={(e) => setForm({ ...form, breakMinutes: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">ساعات العمل</label>
              <input type="number" min="0" step="0.5" value={form.workingHours} onChange={(e) => setForm({ ...form, workingHours: e.target.value })} className={inputClass} />
            </div>
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
        title="حذف الوردية"
        message={`هل أنت متأكد من حذف "${showDelete?.name}"؟`}
        variant="danger"
      />
    </div>
  );
}
