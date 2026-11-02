import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { getCostCenters, createCostCenter, updateCostCenter, deleteCostCenter } from '@/api/accounting';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import ExcelExportButton from '@/components/excel/ExcelExportButton';
import ExcelImportButton from '@/components/excel/ExcelImportButton';

const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

const EMPTY_FORM = { code: '', name: '', nameEn: '', parentId: '' };

export default function CostCentersPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const { data: costCenters = [], isLoading } = useQuery({
    queryKey: ['cost-centers'],
    queryFn: () => getCostCenters(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['cost-centers'] });

  const saveMutation = useMutation({
    mutationFn: (payload: any) =>
      editing ? updateCostCenter(editing.id, payload) : createCostCenter(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_FORM); toast.success('تم حفظ مركز التكلفة بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCostCenter(id),
    onSuccess: () => { invalidate(); setShowDeleteConfirm(false); setDeleteTarget(null); toast.success('تم حذف مركز التكلفة بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };
  const openEdit = (item: any) => {
    setEditing(item);
    setForm({
      code: item.code || '',
      name: item.name || '',
      nameEn: item.nameEn || item.name_en || '',
      parentId: String(item.parentId || item.parent_id || ''),
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-medium">{String(item.code)}</span> },
    { key: 'name', header: 'الاسم', render: (item) => String(item.name) },
    { key: 'nameEn', header: 'الاسم بالإنجليزية', render: (item) => String(item.nameEn || item.name_en || '-') },
    { key: 'parentId', header: 'مركز رئيسي', render: (item) => {
      const parentId = item.parentId || item.parent_id;
      if (!parentId) return <span className="text-gray-400">-</span>;
      const parent = (costCenters as any[]).find((cc: any) => cc.id === parentId || String(cc.id) === String(parentId));
      return parent ? parent.name : String(parentId);
    }},
    { key: 'isActive', header: 'الحالة', render: (item) => (item.isActive !== false) ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex items-center gap-2">
        <button onClick={() => openEdit(item)} className="text-blue-600 hover:underline text-sm">تعديل</button>
        <button onClick={() => { setDeleteTarget(item); setShowDeleteConfirm(true); }} className="text-red-600 hover:underline text-sm">حذف</button>
      </div>
    )},
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader title="مراكز التكلفة" subtitle="إدارة مراكز التكلفة" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} actions={<>
          <ExcelExportButton url="/excel/exports/cost-center-report" filename="cost-center-report.xlsx" label="تقرير مراكز التكلفة Excel" />
          <ExcelExportButton url="/excel/exports/cost-centers" filename="cost-centers.xlsx" label="تصدير مراكز التكلفة" />
          <ExcelImportButton url="/excel/imports/cost-centers" label="استيراد مراكز" onSuccess={invalidate} />
          <button onClick={openCreate} className="btn-primary">+ مركز تكلفة جديد</button>
        </>} />

      <DataTable
        columns={columns}
        data={costCenters as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={costCenters.length}
      />

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل مركز التكلفة' : 'مركز تكلفة جديد'} size="md">
        <div className="space-y-4">
          <div>
            <label className="label">الكود *</label>
            <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} placeholder="CC-001" disabled={!!editing} />
          </div>
          <div>
            <label className="label">الاسم *</label>
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className="label">الاسم بالإنجليزية</label>
            <input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className="label">مركز رئيسي</label>
            <select value={form.parentId} onChange={(e) => setForm({ ...form, parentId: e.target.value })} className={inputClass}>
              <option value="">بدون (مستوى أعلى)</option>
              {(costCenters as any[]).filter((cc: any) => !editing || cc.id !== editing.id).map((cc: any) => (
                <option key={cc.id} value={cc.id}>{cc.code} - {cc.name}</option>
              ))}
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={() => saveMutation.mutate({ code: form.code, name: form.name, name_en: form.nameEn, parent_id: form.parentId || null })} className="btn-primary" disabled={!form.code || !form.name || saveMutation.isPending}>
              {saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="حذف مركز التكلفة"
        message={`هل أنت متأكد من حذف "${deleteTarget?.name || ''}"؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
