import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put, del } from '@/api/client';
import { Modal } from '@/components/ui/Modal';
import { PageHeader } from '@/components/ui/PageHeader';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useToast } from '@/components/ui/Toast';
import type { RoleItem, PermissionItem } from '@/types';

interface RoleForm {
  name: string;
  nameEn: string;
  description: string;
  isActive: boolean;
  permissionIds: number[];
}

const EMPTY_FORM: RoleForm = { name: '', nameEn: '', description: '', isActive: true, permissionIds: [] };

const MODULE_LABELS: Record<string, string> = {
  sales: 'المبيعات',
  purchases: 'المشتريات',
  accounting: 'المحاسبة',
  reports: 'التقارير',
  admin: 'الإدارة',
  inventory: 'المخزون',
  hr: 'الموارد البشرية',
  crm: 'علاقات العملاء',
};

export default function RolesPage() {
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<RoleItem | null>(null);
  const [form, setForm] = useState<RoleForm>(EMPTY_FORM);
  const [deleteTarget, setDeleteTarget] = useState<RoleItem | null>(null);
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: rolesData, isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => get<{ items: RoleItem[]; total: number }>('/settings/roles'),
  });

  const { data: permsData } = useQuery({
    queryKey: ['permissions'],
    queryFn: () => get<{ items: PermissionItem[]; total: number }>('/settings/permissions'),
  });

  const roles = rolesData?.items || [];
  const permissions = permsData?.items || [];

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['roles'] });
    queryClient.invalidateQueries({ queryKey: ['permissions'] });
  };

  const createMutation = useMutation({
    mutationFn: (data: RoleForm) => post('/settings/roles', {
      name: data.name, name_en: data.nameEn || null, description: data.description || null,
      is_active: data.isActive, permission_ids: data.permissionIds,
    }),
    onSuccess: () => { invalidate(); setShowModal(false); setForm(EMPTY_FORM); toast.success('تم إنشاء الدور بنجاح'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: RoleForm }) => put(`/settings/roles/${id}`, {
      name: data.name, name_en: data.nameEn || null, description: data.description || null,
      is_active: data.isActive, permission_ids: data.permissionIds,
    }),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_FORM); toast.success('تم تحديث الدور بنجاح'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => del(`/settings/roles/${id}`),
    onSuccess: () => { invalidate(); setDeleteTarget(null); toast.success('تم حذف الدور بنجاح'); },
    onError: (e: any) => { toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)); setDeleteTarget(null); },
  });

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };

  const openEdit = (role: RoleItem) => {
    setEditing(role);
    setForm({
      name: role.name,
      nameEn: role.nameEn || '',
      description: role.description || '',
      isActive: role.isActive,
      permissionIds: role.permissions.map(p => p.id),
    });
    setShowModal(true);
  };

  const togglePermission = (permId: number) => {
    setForm(prev => ({
      ...prev,
      permissionIds: prev.permissionIds.includes(permId)
        ? prev.permissionIds.filter(id => id !== permId)
        : [...prev.permissionIds, permId],
    }));
  };

  const toggleModule = (modulePerms: PermissionItem[]) => {
    const ids = modulePerms.map(p => p.id);
    const allSelected = ids.every(id => form.permissionIds.includes(id));
    setForm(prev => ({
      ...prev,
      permissionIds: allSelected
        ? prev.permissionIds.filter(id => !ids.includes(id))
        : [...new Set([...prev.permissionIds, ...ids])],
    }));
  };

  const onSubmit = () => {
    if (!form.name.trim()) { toast.warning('اسم الدور مطلوب'); return; }
    if (editing) {
      updateMutation.mutate({ id: editing.id, data: form });
    } else {
      createMutation.mutate(form);
    }
  };

  // Group permissions by module
  const permByModule: Record<string, PermissionItem[]> = {};
  permissions.forEach(p => {
    const mod = p.module || 'other';
    if (!permByModule[mod]) permByModule[mod] = [];
    permByModule[mod].push(p);
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="الأدوار والصلاحيات"
        subtitle="إدارة الأدوار وتحديد صلاحيات المستخدمين"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
        actions={<button onClick={openCreate} className="btn-primary">+ دور جديد</button>}
      />

      {isLoading ? (
        <div className="text-center py-12 text-gray-500">جاري التحميل...</div>
      ) : roles.length === 0 ? (
        <div className="text-center py-12 text-gray-500">لا توجد أدوار</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {roles.map(role => (
            <div key={role.id} className="bg-white dark:bg-zinc-800 rounded-xl border border-gray-200 dark:border-zinc-700 p-5 flex flex-col">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="text-lg font-bold text-gray-900 dark:text-zinc-100">{role.name}</h3>
                  {role.nameEn && <p className="text-sm text-gray-500 dark:text-zinc-400">{role.nameEn}</p>}
                </div>
                <span className={`px-2 py-0.5 text-xs rounded-full ${role.isActive ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                  {role.isActive ? 'نشط' : 'غير نشط'}
                </span>
              </div>
              {role.description && <p className="text-sm text-gray-600 dark:text-zinc-400 mb-3">{role.description}</p>}
              <div className="flex flex-wrap gap-1 mb-4 flex-1">
                {role.permissions.slice(0, 8).map(p => (
                  <span key={p.id} className="px-2 py-0.5 text-xs rounded bg-blue-50 text-blue-700 dark:bg-blue-900/20 dark:text-blue-300">{p.code}</span>
                ))}
                {role.permissions.length > 8 && (
                  <span className="px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600 dark:bg-zinc-700 dark:text-zinc-300">+{role.permissions.length - 8}</span>
                )}
              </div>
              <div className="flex gap-2 pt-2 border-t border-gray-100 dark:border-zinc-700">
                <button onClick={() => openEdit(role)} className="text-sm text-blue-600 hover:underline">تعديل</button>
                <button onClick={() => setDeleteTarget(role)} className="text-sm text-red-600 hover:underline mr-auto">حذف</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); setForm(EMPTY_FORM); }} title={editing ? 'تعديل الدور' : 'دور جديد'} size="lg">
        <div className="space-y-4 max-h-[70vh] overflow-y-auto">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">اسم الدور (عربي)</label>
              <input value={form.name} onChange={e => setForm(p => ({ ...p, name: e.target.value }))} className="input" placeholder="مثال: محاسب" />
            </div>
            <div>
              <label className="label">اسم الدور (إنجليزي)</label>
              <input value={form.nameEn} onChange={e => setForm(p => ({ ...p, nameEn: e.target.value }))} className="input" placeholder="e.g. Accountant" />
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <input value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} className="input" placeholder="وصف مختصر للدور" />
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" checked={form.isActive} onChange={e => setForm(p => ({ ...p, isActive: e.target.checked }))} className="rounded" />
            <label className="text-sm font-medium text-gray-700 dark:text-zinc-300">نشط</label>
          </div>

          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-zinc-300 mb-3">الصلاحيات</h3>
            {Object.entries(permByModule).map(([mod, perms]) => {
              const allSelected = perms.every(p => form.permissionIds.includes(p.id));
              const someSelected = perms.some(p => form.permissionIds.includes(p.id));
              return (
                <div key={mod} className="mb-4 border border-gray-200 dark:border-zinc-700 rounded-lg p-3">
                  <div className="flex items-center gap-2 mb-2 pb-2 border-b border-gray-100 dark:border-zinc-700">
                    <input
                      type="checkbox"
                      checked={allSelected}
                      ref={el => { if (el) el.indeterminate = someSelected && !allSelected; }}
                      onChange={() => toggleModule(perms)}
                      className="rounded"
                    />
                    <span className="text-sm font-semibold text-gray-800 dark:text-zinc-200">{MODULE_LABELS[mod] || mod}</span>
                    <span className="text-xs text-gray-400">({perms.length})</span>
                  </div>
                  <div className="grid grid-cols-2 gap-1">
                    {perms.map(p => (
                      <label key={p.id} className="flex items-center gap-2 text-sm text-gray-600 dark:text-zinc-400 hover:text-gray-900 dark:hover:text-zinc-100 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={form.permissionIds.includes(p.id)}
                          onChange={() => togglePermission(p.id)}
                          className="rounded"
                        />
                        <span>{p.name}</span>
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          <div className="flex justify-end gap-2 pt-4 border-t border-gray-200 dark:border-zinc-700">
            <button onClick={() => { setShowModal(false); setEditing(null); setForm(EMPTY_FORM); }} className="btn-secondary">إلغاء</button>
            <button onClick={onSubmit} className="btn-primary" disabled={createMutation.isPending || updateMutation.isPending}>
              {(createMutation.isPending || updateMutation.isPending) ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="حذف الدور"
        message={`هل أنت متأكد من حذف الدور "${deleteTarget?.name}"؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        cancelText="إلغاء"
        variant="danger"
      />
    </div>
  );
}
