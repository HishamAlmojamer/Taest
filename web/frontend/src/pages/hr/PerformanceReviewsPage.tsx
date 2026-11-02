import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getPerformanceReviews, createPerformanceReview, updatePerformanceReview, deletePerformanceReview, getEmployees } from '@/api/hr';
import { formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRPerformanceReview } from '@/types';

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'draft', label: 'مسودة' },
  { key: 'review', label: 'قيد المراجعة' },
  { key: 'completed', label: 'مكتمل' },
];

export default function PerformanceReviewsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRPerformanceReview | null>(null);
  const [showDelete, setShowDelete] = useState<HRPerformanceReview | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '', reviewerId: '', reviewDate: new Date().toISOString().slice(0, 10), reviewPeriod: '',
    rating: '3', goalsAchieved: '', strengths: '', improvements: '', recommendations: '', status: 'draft',
    nextReviewDate: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-performance-reviews', page, statusFilter],
    queryFn: () => getPerformanceReviews({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createPerformanceReview({
      employeeId: Number(form.employeeId),
      reviewerId: form.reviewerId ? Number(form.reviewerId) : undefined,
      reviewDate: form.reviewDate,
      reviewPeriod: form.reviewPeriod || undefined,
      rating: Number(form.rating) || 0,
      goalsAchieved: form.goalsAchieved || undefined,
      strengths: form.strengths || undefined,
      improvements: form.improvements || undefined,
      recommendations: form.recommendations || undefined,
      status: form.status,
      nextReviewDate: form.nextReviewDate || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-performance-reviews'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updatePerformanceReview(editing!.id, {
      reviewerId: form.reviewerId ? Number(form.reviewerId) : undefined,
      reviewDate: form.reviewDate,
      reviewPeriod: form.reviewPeriod || undefined,
      rating: Number(form.rating) || 0,
      goalsAchieved: form.goalsAchieved || undefined,
      strengths: form.strengths || undefined,
      improvements: form.improvements || undefined,
      recommendations: form.recommendations || undefined,
      status: form.status,
      nextReviewDate: form.nextReviewDate || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-performance-reviews'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deletePerformanceReview,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-performance-reviews'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', reviewerId: '', reviewDate: new Date().toISOString().slice(0, 10), reviewPeriod: '', rating: '3', goalsAchieved: '', strengths: '', improvements: '', recommendations: '', status: 'draft', nextReviewDate: '' });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (r: HRPerformanceReview) => {
    setEditing(r);
    setForm({
      employeeId: String(r.employeeId),
      reviewerId: r.reviewerId ? String(r.reviewerId) : '',
      reviewDate: r.reviewDate || new Date().toISOString().slice(0, 10),
      reviewPeriod: r.reviewPeriod || '',
      rating: String(r.rating ?? 0),
      goalsAchieved: r.goalsAchieved || '',
      strengths: r.strengths || '',
      improvements: r.improvements || '',
      recommendations: r.recommendations || '',
      status: r.status || 'draft',
      nextReviewDate: r.nextReviewDate || '',
    });
    setShowModal(true);
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId) as any;
    return emp ? (emp.fullName || emp.full_name || `#${empId}`) : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'reviewerName', header: 'المقيِّم', render: (item) => String(item.reviewerName || '-') },
    { key: 'reviewDate', header: 'تاريخ التقييم', render: (item) => formatDate(String(item.reviewDate)) },
    { key: 'reviewPeriod', header: 'الفترة', render: (item) => String(item.reviewPeriod || '-') },
    { key: 'rating', header: 'التقييم', render: (item) => (
      <span className="inline-flex items-center gap-1 font-bold text-primary-600">
        {Number(item.rating || 0).toFixed(1)}
        <span className="text-amber-500 text-xs">★</span>
      </span>
    )},
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRPerformanceReview)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRPerformanceReview)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="تقييم الأداء"
          subtitle={`${data?.total || 0} تقييم`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={openAdd} className="btn-primary">تقييم جديد</button>}
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

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل التقييم' : 'تقييم جديد'} size="lg">
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
              <label className="label">المقيِّم</label>
              <select value={form.reviewerId} onChange={(e) => setForm({ ...form, reviewerId: e.target.value })} className={inputClass}>
                <option value="">— غير محدد —</option>
                {employees.map((e: any) => <option key={e.id} value={e.id}>{e.fullName || e.full_name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">تاريخ التقييم</label>
              <input type="date" value={form.reviewDate} onChange={(e) => setForm({ ...form, reviewDate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الفترة</label>
              <input type="text" value={form.reviewPeriod} onChange={(e) => setForm({ ...form, reviewPeriod: e.target.value })} className={inputClass} placeholder="مثال: 2026-Q1" />
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">التقييم (1-5)</label>
              <input type="number" min="0" max="5" step="0.5" value={form.rating} onChange={(e) => setForm({ ...form, rating: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الحالة</label>
              <select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })} className={inputClass}>
                <option value="draft">مسودة</option>
                <option value="review">قيد المراجعة</option>
                <option value="completed">مكتمل</option>
              </select>
            </div>
            <div>
              <label className="label">التقييم القادم</label>
              <input type="date" value={form.nextReviewDate} onChange={(e) => setForm({ ...form, nextReviewDate: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">الأهداف المحققة</label>
            <textarea value={form.goalsAchieved} onChange={(e) => setForm({ ...form, goalsAchieved: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div>
            <label className="label">نقاط القوة</label>
            <textarea value={form.strengths} onChange={(e) => setForm({ ...form, strengths: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div>
            <label className="label">مجالات التحسين</label>
            <textarea value={form.improvements} onChange={(e) => setForm({ ...form, improvements: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div>
            <label className="label">التوصيات</label>
            <textarea value={form.recommendations} onChange={(e) => setForm({ ...form, recommendations: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setEditing(null); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editing ? updateMutation : createMutation).mutate()}
              disabled={!form.employeeId || createMutation.isPending || updateMutation.isPending}
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
        title="حذف التقييم"
        message="هل أنت متأكد من حذف هذا التقييم؟ لا يمكن التراجع عن هذا الإجراء."
        variant="danger"
      />
    </div>
  );
}
