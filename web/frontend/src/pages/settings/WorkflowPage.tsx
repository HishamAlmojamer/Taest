import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { get, post, put, del } from '@/api/client';
import type { PaginatedResponse, WorkflowRule } from '@/types';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';

const EMPTY_FORM = { name: '', nameAr: '', module: '', action: '', condition: '', approverRole: '' };

export default function WorkflowPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<WorkflowRule | null>(null);
  const [formData, setFormData] = useState(EMPTY_FORM);

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-rules', page],
    queryFn: async () => get<PaginatedResponse<WorkflowRule>>('/settings/workflow', { page, pageSize: 10 }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['workflow-rules'] });

  const saveMutation = useMutation({
    mutationFn: async (payload: typeof EMPTY_FORM) =>
      editing ? put(`/settings/workflow/${editing.id}`, payload) : post('/settings/workflow', payload),
    onSuccess: () => {
      invalidate(); setShowModal(false); setEditing(null); setFormData(EMPTY_FORM);
      toast.success(editing ? 'تم تحديث القاعدة بنجاح' : 'تم إنشاء القاعدة بنجاح');
    },
    onError: (error: any) => { toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message)); },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, activate }: { id: string; activate: boolean }) =>
      activate ? post(`/settings/workflow/${id}/activate`) : del(`/settings/workflow/${id}`),
    onSuccess: (_, vars) => { invalidate(); toast.success(vars.activate ? 'تم تفعيل القاعدة' : 'تم تعطيل القاعدة'); },
    onError: (error: any) => { toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message)); },
  });

  const openCreate = () => { setEditing(null); setFormData(EMPTY_FORM); setShowModal(true); };
  const openEdit = (rule: WorkflowRule) => {
    setEditing(rule);
    setFormData({ name: rule.name || '', nameAr: rule.nameAr || '', module: rule.module || '', action: rule.action || '', condition: rule.condition || '', approverRole: rule.approverRole || '' });
    setShowModal(true);
  };

  const handleSubmit = () => {
    if (!formData.name || !formData.module || !formData.action || !formData.approverRole) {
      toast.warning('يرجى ملء جميع الحقول المطلوبة');
      return;
    }
    saveMutation.mutate(formData);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم القاعدة', sortable: true, render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'module', header: 'الوحدة', render: (item) => <span className="badge-info">{String(item.module)}</span> },
    { key: 'action', header: 'الإجراء', render: (item) => String(item.action) },
    { key: 'approverRole', header: 'دور المعتمد', render: (item) => String(item.approverRole) },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    {
      key: 'actions', header: 'الإجراءات',
      render: (item) => {
        const rule = item as unknown as WorkflowRule;
        return (
          <div className="flex items-center gap-2">
            <button onClick={(e) => { e.stopPropagation(); openEdit(rule); }} className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400">تعديل</button>
            {rule.isActive ? (
              <button onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: rule.id, activate: false }); }} className="text-sm text-red-600 hover:text-red-800 dark:text-red-400">تعطيل</button>
            ) : (
              <button onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: rule.id, activate: true }); }} className="text-sm text-green-600 hover:text-green-800 dark:text-green-400">تفعيل</button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="سير العمل"
        subtitle="قواعد الاعتماد وتدفق العمل"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" /></svg>}
        actions={<button onClick={openCreate} className="btn-primary">+ قاعدة جديدة</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل قاعدة سير عمل' : 'قاعدة سير عمل جديدة'} size="lg">
        <div className="space-y-4">
          <div><label className="label">اسم القاعدة</label><input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="input" placeholder="اسم القاعدة بالإنجليزية" /></div>
          <div><label className="label">الاسم بالعربية</label><input type="text" value={formData.nameAr} onChange={(e) => setFormData({ ...formData, nameAr: e.target.value })} className="input" placeholder="اسم القاعدة بالعربية" /></div>
          <div>
            <label className="label">الوحدة</label>
            <select value={formData.module} onChange={(e) => setFormData({ ...formData, module: e.target.value })} className="input">
              <option value="">اختر الوحدة</option>
              <option value="sales">المبيعات</option><option value="purchases">المشتريات</option><option value="inventory">المخزون</option><option value="accounting">المحاسبة</option><option value="hr">الموارد البشرية</option>
            </select>
          </div>
          <div>
            <label className="label">الإجراء</label>
            <select value={formData.action} onChange={(e) => setFormData({ ...formData, action: e.target.value })} className="input">
              <option value="">اختر الإجراء</option>
              <option value="create">إنشاء</option><option value="approve">اعتماد</option><option value="delete">حذف</option><option value="post">ترحيل</option>
            </select>
          </div>
          <div><label className="label">الشرط</label><input type="text" value={formData.condition} onChange={(e) => setFormData({ ...formData, condition: e.target.value })} className="input" placeholder="مثال: amount > 10000" /></div>
          <div>
            <label className="label">دور المعتمد</label>
            <select value={formData.approverRole} onChange={(e) => setFormData({ ...formData, approverRole: e.target.value })} className="input">
              <option value="">اختر الدور</option>
              <option value="admin">مدير</option><option value="accountant">محاسب</option><option value="manager">مدير قسم</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={handleSubmit} className="btn-primary" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
