import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { get, post } from '@/api/client';
import type { PaginatedResponse, WorkflowRule } from '@/types';
import { getStatusLabel, getStatusColor } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';

export default function WorkflowPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    nameAr: '',
    module: '',
    action: '',
    condition: '',
    approverRole: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['workflow-rules', page],
    queryFn: async () => {
      const res = await get<PaginatedResponse<WorkflowRule>>('/settings/workflow', { page, pageSize: 10 });
      return res;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return await post('/settings/workflow', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-rules'] });
      setShowModal(false);
      setFormData({ name: '', nameAr: '', module: '', action: '', condition: '', approverRole: '' });
    },
  });

  const handleSubmit = () => {
    if (!formData.name || !formData.module || !formData.action || !formData.approverRole) {
      alert('يرجى ملء جميع الحقول المطلوبة');
      return;
    }
    createMutation.mutate(formData);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم القاعدة', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'module', header: 'الوحدة', render: (item) => <span className="badge-info">{String(item.module)}</span> },
    { key: 'action', header: 'الإجراء', render: (item) => String(item.action) },
    { key: 'approverRole', header: 'دور المعتمد', render: (item) => String(item.approverRole) },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">سير العمل</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ قاعدة جديدة</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />

      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="قاعدة سير عمل جديدة" size="lg">
        <div className="space-y-4">
          <div>
            <label className="label">اسم القاعدة</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input"
              placeholder="اسم القاعدة بالإنجليزية"
            />
          </div>
          <div>
            <label className="label">الاسم بالعربية</label>
            <input
              type="text"
              value={formData.nameAr}
              onChange={(e) => setFormData({ ...formData, nameAr: e.target.value })}
              className="input"
              placeholder="اسم القاعدة بالعربية"
            />
          </div>
          <div>
            <label className="label">الوحدة</label>
            <select
              value={formData.module}
              onChange={(e) => setFormData({ ...formData, module: e.target.value })}
              className="input"
            >
              <option value="">اختر الوحدة</option>
              <option value="sales">المبيعات</option>
              <option value="purchases">المشتريات</option>
              <option value="inventory">المخزون</option>
              <option value="accounting">المحاسبة</option>
              <option value="hr">الموارد البشرية</option>
            </select>
          </div>
          <div>
            <label className="label">الإجراء</label>
            <select
              value={formData.action}
              onChange={(e) => setFormData({ ...formData, action: e.target.value })}
              className="input"
            >
              <option value="">اختر الإجراء</option>
              <option value="create">إنشاء</option>
              <option value="approve">اعتماد</option>
              <option value="delete">حذف</option>
              <option value="post">ترحيل</option>
            </select>
          </div>
          <div>
            <label className="label">الشرط</label>
            <input
              type="text"
              value={formData.condition}
              onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
              className="input"
              placeholder="مثال: amount > 10000"
            />
          </div>
          <div>
            <label className="label">دور المعتمد</label>
            <select
              value={formData.approverRole}
              onChange={(e) => setFormData({ ...formData, approverRole: e.target.value })}
              className="input"
            >
              <option value="">اختر الدور</option>
              <option value="admin">مدير</option>
              <option value="accountant">محاسب</option>
              <option value="manager">مدير قسم</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-4">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={handleSubmit} className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
