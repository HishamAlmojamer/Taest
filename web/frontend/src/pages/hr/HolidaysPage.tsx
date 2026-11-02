import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getHolidays, createHoliday, updateHoliday, deleteHoliday } from '@/api/hr';
import { formatDate } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRHoliday } from '@/types';

export default function HolidaysPage() {
  const queryClient = useQueryClient();
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRHoliday | null>(null);
  const [showDelete, setShowDelete] = useState<HRHoliday | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    name: '', date: '', type: 'عطلة رسمية', isRecurring: true, isActive: true,
  });

  const years = Array.from({ length: 5 }, (_, i) => currentYear - 2 + i);

  const { data, isLoading } = useQuery({
    queryKey: ['hr-holidays', year],
    queryFn: () => getHolidays({ year }),
  });

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createHoliday({
      name: form.name,
      date: form.date,
      type: form.type || undefined,
      isRecurring: form.isRecurring,
      isActive: form.isActive,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-holidays'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updateHoliday(editing!.id, {
      name: form.name,
      date: form.date,
      type: form.type || undefined,
      isRecurring: form.isRecurring,
      isActive: form.isActive,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-holidays'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteHoliday,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-holidays'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ name: '', date: '', type: 'عطلة رسمية', isRecurring: true, isActive: true });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (h: HRHoliday) => {
    setEditing(h);
    setForm({
      name: h.name,
      date: h.date || '',
      type: h.type || 'عطلة رسمية',
      isRecurring: Boolean(h.isRecurring),
      isActive: h.isActive !== undefined ? Boolean(h.isActive) : true,
    });
    setShowModal(true);
  };

  const weekdayName = (date: string) => {
    if (!date) return '';
    try {
      return new Date(date).toLocaleDateString('ar-EG', { weekday: 'long' });
    } catch { return ''; }
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-bold">{String(item.name)}</span> },
    { key: 'date', header: 'التاريخ', render: (item) => <span>{formatDate(String(item.date))} <span className="text-gray-400 text-xs">({weekdayName(String(item.date))})</span></span> },
    { key: 'type', header: 'النوع', render: (item) => <span className="badge bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-300">{String(item.type || '-')}</span> },
    { key: 'isRecurring', header: 'سنوية', render: (item) => item.isRecurring ? <span className="text-emerald-600">نعم</span> : <span className="text-gray-400">لا</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive === false ? <span className="badge bg-red-50 dark:bg-red-500/10 text-red-600 dark:text-red-400">موقوفة</span> : <span className="badge bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">مفعّلة</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRHoliday)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRHoliday)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="الإجازات الرسمية"
          subtitle={`${data?.total || 0} إجازة في ${year}`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<div className="flex gap-2">
            <select value={year} onChange={(e) => setYear(Number(e.target.value))} className={inputClass + ' w-32'}>
              {years.map((y) => <option key={y} value={y}>{y}</option>)}
            </select>
            <button onClick={openAdd} className="btn-primary">إضافة إجازة</button>
          </div>}
        />
      </div>

      <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل الإجازة' : 'إضافة إجازة'}>
        <div className="space-y-4">
          <div>
            <label className="label">اسم الإجازة</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} placeholder="مثال: عيد الفطر" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">التاريخ</label>
              <input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">النوع</label>
              <input value={form.type} onChange={(e) => setForm({ ...form, type: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="flex gap-6">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.isRecurring} onChange={(e) => setForm({ ...form, isRecurring: e.target.checked })} className="rounded" />
              إجازة سنوية متكررة
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input type="checkbox" checked={form.isActive} onChange={(e) => setForm({ ...form, isActive: e.target.checked })} className="rounded" />
              مفعّلة
            </label>
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setEditing(null); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editing ? updateMutation : createMutation).mutate()}
              disabled={!form.name || !form.date || createMutation.isPending || updateMutation.isPending}
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
        title="حذف الإجازة"
        message={`هل أنت متأكد من حذف "${showDelete?.name}"؟`}
        variant="danger"
      />
    </div>
  );
}
