import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getPositions, getDepartments, createPosition, updatePosition, deletePosition } from '@/api/hr';
import { formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRPosition } from '@/types';

export default function PositionsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRPosition | null>(null);
  const [showDelete, setShowDelete] = useState<HRPosition | null>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    code: '', name: '', nameEn: '', departmentId: '', minSalary: '', maxSalary: '', description: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-positions', page, search],
    queryFn: () => getPositions({ page, per_page: 10, search: search || undefined }),
  });

  const { data: deptData } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const departments = deptData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createPosition({
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      departmentId: form.departmentId ? Number(form.departmentId) : undefined,
      minSalary: form.minSalary ? Number(form.minSalary) : undefined,
      maxSalary: form.maxSalary ? Number(form.maxSalary) : undefined,
      description: form.description || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-positions'] });
      setShowModal(false);
      resetForm();
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updatePosition(editing!.id, {
      code: form.code,
      name: form.name,
      nameEn: form.nameEn || undefined,
      departmentId: form.departmentId ? Number(form.departmentId) : undefined,
      minSalary: form.minSalary ? Number(form.minSalary) : undefined,
      maxSalary: form.maxSalary ? Number(form.maxSalary) : undefined,
      description: form.description || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-positions'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      setShowModal(false);
      setEditing(null);
      resetForm();
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deletePosition,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-positions'] });
      setShowDelete(null);
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ code: '', name: '', nameEn: '', departmentId: '', minSalary: '', maxSalary: '', description: '' });
  };

  const openAdd = () => {
    setEditing(null);
    resetForm();
    setShowModal(true);
  };

  const openEdit = (pos: HRPosition) => {
    setEditing(pos);
    setForm({
      code: pos.code,
      name: pos.name,
      nameEn: pos.nameEn || '',
      departmentId: pos.departmentId ? String(pos.departmentId) : '',
      minSalary: pos.minSalary ? String(pos.minSalary) : '',
      maxSalary: pos.maxSalary ? String(pos.maxSalary) : '',
      description: pos.description || '',
    });
    setShowModal(true);
  };

  const getDeptName = (id?: number) => {
    if (!id) return '-';
    const dept = departments.find((d) => d.id === id);
    return dept ? dept.name : `#${id}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded">{String(item.code || '-')}</span> },
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'nameEn', header: 'الاسم (إنجليزي)', render: (item) => String(item.nameEn || '-') },
    { key: 'departmentId', header: 'القسم', render: (item) => getDeptName(Number(item.departmentId)) },
    { key: 'minSalary', header: 'الحد الأدنى', render: (item) => formatCurrency(Number(item.minSalary || 0)) },
    { key: 'maxSalary', header: 'الحد الأقصى', render: (item) => formatCurrency(Number(item.maxSalary || 0)) },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRPosition)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRPosition)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="المناصب الوظيفية"
          subtitle={`${data?.total || 0} منصب`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={openAdd} className="btn-primary">منصب جديد</button>}
        />
      </div>

      <DataTable
        columns={columns}
        data={items as any}
        loading={isLoading}
        totalItems={data?.total || 0}
        page={page}
        pageSize={10}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={(v) => { setSearch(v); setPage(1); }}
        searchPlaceholder="بحث في المناصب..."
        keepPreviousData
      />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل المنصب' : 'منصب جديد'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الكود</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">القسم</label>
              <select value={form.departmentId} onChange={(e) => setForm({ ...form, departmentId: e.target.value })} className={inputClass}>
                <option value="">— بدون —</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">الاسم (عربي)</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className="label">الاسم (إنجليزي)</label>
            <input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className={inputClass} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الحد الأدنى للراتب</label>
              <input type="number" min="0" value={form.minSalary} onChange={(e) => setForm({ ...form, minSalary: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الحد الأقصى للراتب</label>
              <input type="number" min="0" value={form.maxSalary} onChange={(e) => setForm({ ...form, maxSalary: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} rows={2} />
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
        title="حذف المنصب"
        message={`هل أنت متأكد من حذف "${showDelete?.name}"؟`}
        variant="danger"
      />
    </div>
  );
}
