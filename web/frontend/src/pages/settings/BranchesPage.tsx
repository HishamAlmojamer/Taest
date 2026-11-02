import { useState } from 'react';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put, del } from '@/api/client';
import type { Branch } from '@/types';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';

const EMPTY_FORM = { code: '', name: '', nameEn: '', address: '', phone: '', email: '', manager: '' };

export default function BranchesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Branch | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const { data, isLoading } = useQuery({
    queryKey: ['branches'],
    queryFn: async () => get<{ items: Branch[]; total: number }>('/settings/branches', { include_inactive: true }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['branches'] });

  const saveMutation = useMutation({
    mutationFn: async (payload: typeof EMPTY_FORM) =>
      editing ? put(`/settings/branches/${editing.id}`, payload) : post('/settings/branches', payload),
    onSuccess: () => {
      invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_FORM);
      toast.success(editing ? 'تم تحديث الفرع بنجاح' : 'تم إنشاء الفرع بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, activate }: { id: number; activate: boolean }) =>
      activate ? post(`/settings/branches/${id}/restore`) : del(`/settings/branches/${id}`),
    onSuccess: (_, vars) => { invalidate(); toast.success(vars.activate ? 'تم تفعيل الفرع' : 'تم تعطيل الفرع'); },
    onError: (error: any) => { toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message)); },
  });

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };
  const openEdit = (branch: Branch) => {
    setEditing(branch);
    setForm({ code: branch.code || '', name: branch.name || '', nameEn: branch.nameEn || '', address: branch.address || '', phone: branch.phone || '', email: branch.email || '', manager: branch.manager || '' });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-medium">{String(item.code)}</span> },
    { key: 'name', header: 'الاسم', sortable: true, render: (item) => String(item.name) },
    { key: 'manager', header: 'المدير', render: (item) => String(item.manager || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    {
      key: 'actions', header: 'الإجراءات',
      render: (item) => {
        const branch = item as unknown as Branch;
        return (
          <div className="flex items-center gap-2">
            <button onClick={(e) => { e.stopPropagation(); openEdit(branch); }} className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400">تعديل</button>
            {branch.isActive ? (
              <button onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: branch.id, activate: false }); }} className="text-sm text-red-600 hover:text-red-800 dark:text-red-400">تعطيل</button>
            ) : (
              <button onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: branch.id, activate: true }); }} className="text-sm text-green-600 hover:text-green-800 dark:text-green-400">تفعيل</button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="الفروع"
        subtitle="إدارة فروع الشركة ومواقع العمل"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
        actions={<button onClick={openCreate} className="btn-primary">+ فرع جديد</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل فرع' : 'فرع جديد'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">الكود *</label><input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input" placeholder="BR-001" /></div>
            <div><label className="label">اسم الفرع *</label><input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" /></div>
            <div><label className="label">الاسم بالإنجليزية</label><input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className="input" /></div>
            <div><label className="label">المدير</label><input value={form.manager} onChange={(e) => setForm({ ...form, manager: e.target.value })} className="input" /></div>
            <div><label className="label">الهاتف</label><input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} className="input" /></div>
            <div><label className="label">البريد الإلكتروني</label><input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" className="input" /></div>
          </div>
          <div><label className="label">العنوان</label><textarea value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={() => saveMutation.mutate(form)} className="btn-primary" disabled={saveMutation.isPending || !form.code || !form.name}>
              {saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
