import { useState } from 'react';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post, put } from '@/api/client';
import type { PaginatedResponse, User, RoleItem } from '@/types';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';

const EMPTY_FORM = { username: '', fullName: '', email: '', password: '', role: 'user' };

export default function UsersPage() {
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset } = useForm();
  const toast = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: async () => {
      const res = await get<PaginatedResponse<User>>('/settings/users', { page, pageSize: 10 });
      return res;
    },
  });

  const { data: rolesData } = useQuery({
    queryKey: ['roles'],
    queryFn: () => get<{ items: RoleItem[] }>('/settings/roles'),
  });

  const roles = rolesData?.items || [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] });

  const createMutation = useMutation({
    mutationFn: (formData: unknown) => post('/settings/users', formData),
    onSuccess: () => {
      invalidate();
      setShowModal(false);
      reset();
      toast.success('تم إنشاء المستخدم بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, formData }: { id: string; formData: unknown }) => put(`/settings/users/${id}`, formData),
    onSuccess: () => {
      invalidate();
      setShowModal(false);
      setEditing(null);
      reset();
      toast.success('تم تحديث المستخدم بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const toggleMutation = useMutation({
    mutationFn: async ({ id, activate }: { id: string; activate: boolean }) =>
      activate ? post(`/settings/users/${id}/activate`) : post(`/settings/users/${id}/deactivate`),
    onSuccess: (_, vars) => {
      invalidate();
      toast.success(vars.activate ? 'تم تفعيل المستخدم' : 'تم تعطيل المستخدم');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const openCreate = () => {
    setEditing(null);
    reset(EMPTY_FORM as any);
    setShowModal(true);
  };

  const openEdit = (user: User) => {
    setEditing(user);
    reset({
      username: user.username,
      fullName: user.fullName,
      email: user.email || '',
      password: '',
      role: user.role,
    } as any);
    setShowModal(true);
  };

  const onModalSubmit = (d: Record<string, unknown>) => {
    const selectedRole = roles.find(r => r.name === d.role);
    const roleId = selectedRole?.id || null;

    if (editing) {
      const payload: Record<string, unknown> = { fullName: d.fullName, email: d.email, role: d.role, roleId };
      if (d.password) payload.password = d.password;
      updateMutation.mutate({ id: editing.id, formData: payload });
    } else {
      createMutation.mutate({ ...d, roleId });
    }
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'username', header: 'اسم المستخدم', sortable: true, render: (item) => <span className="font-medium">{String(item.username)}</span> },
    { key: 'fullName', header: 'الاسم الكامل', sortable: true, render: (item) => String(item.fullName) },
    { key: 'email', header: 'البريد الإلكتروني', render: (item) => String(item.email || '-') },
    { key: 'role', header: 'الدور', render: (item) => <span className="px-2.5 py-0.5 text-xs font-medium rounded-full bg-primary-50 text-primary-700 dark:bg-primary-500/10 dark:text-primary-400">{String(item.role)}</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    {
      key: 'actions',
      header: 'الإجراءات',
      render: (item) => {
        const user = item as unknown as User;
        return (
          <div className="flex items-center gap-2">
            <button onClick={(e) => { e.stopPropagation(); openEdit(user); }} className="text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300">
              تعديل
            </button>
            {user.isActive ? (
              <button
                onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: user.id, activate: false }); }}
                className="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
              >
                تعطيل
              </button>
            ) : (
              <button
                onClick={(e) => { e.stopPropagation(); toggleMutation.mutate({ id: user.id, activate: true }); }}
                className="text-sm text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
              >
                تفعيل
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="المستخدمون"
        subtitle="إدارة حسابات المستخدمين والأدوار والصلاحيات"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        }
        actions={<button onClick={openCreate} className="btn-primary">+ مستخدم جديد</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); reset(); }} title={editing ? 'تعديل مستخدم' : 'مستخدم جديد'} size="sm">
        <form onSubmit={handleSubmit((d) => onModalSubmit(d as Record<string, unknown>))} className="space-y-4">
          {!editing && (
            <div>
              <label className="label">اسم المستخدم</label>
              <input {...register('username', { required: true })} className="input" />
            </div>
          )}
          <div><label className="label">الاسم الكامل</label><input {...register('fullName', { required: true })} className="input" /></div>
          <div><label className="label">البريد الإلكتروني</label><input {...register('email')} type="email" className="input" /></div>
          <div>
            <label className="label">كلمة المرور</label>
            <input {...register('password')} type="password" className="input" placeholder={editing ? 'اتركها فارغة لعدم التغيير' : ''} />
          </div>
          <div>
            <label className="label">الدور</label>
            <select {...register('role', { required: true })} className="input">
              {roles.length > 0 ? (
                roles.map(r => <option key={r.id} value={r.name}>{r.nameEn || r.name}</option>)
              ) : (
                <>
                  <option value="admin">مدير</option>
                  <option value="accountant">محاسب</option>
                  <option value="viewer">مشاهد</option>
                </>
              )}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || updateMutation.isPending}>
              {(createMutation.isPending || updateMutation.isPending) ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => {}}
        title="حذف المستخدم"
        message={`هل أنت متأكد من حذف المستخدم "${deleteTarget?.fullName}"؟`}
        confirmText="حذف"
        cancelText="إلغاء"
        variant="danger"
      />
    </div>
  );
}
