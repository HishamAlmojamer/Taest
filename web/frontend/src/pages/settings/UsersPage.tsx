import { useState } from 'react';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, post } from '@/api/client';
import type { PaginatedResponse, User } from '@/types';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';

export default function UsersPage() {
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: async () => {
      const res = await get<PaginatedResponse<User>>('/settings/users', { page, pageSize: 10 });
      return res;
    },
  });

  const { register, handleSubmit, reset } = useForm();

  const createMutation = useMutation({
    mutationFn: (formData: unknown) => post('/settings/users', formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setShowModal(false);
      reset();
    },
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'username', header: 'اسم المستخدم', render: (item) => <span className="font-medium">{String(item.username)}</span> },
    { key: 'fullName', header: 'الاسم الكامل', render: (item) => String(item.fullName) },
    { key: 'email', header: 'البريد الإلكتروني', render: (item) => String(item.email) },
    { key: 'role', header: 'الدور', render: (item) => <span className="badge-info">{String(item.role)}</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">المستخدمون</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ مستخدم جديد</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="مستخدم جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div><label className="label">اسم المستخدم</label><input {...register('username', { required: true })} className="input" /></div>
          <div><label className="label">الاسم الكامل</label><input {...register('fullName', { required: true })} className="input" /></div>
          <div><label className="label">البريد الإلكتروني</label><input {...register('email', { required: true })} type="email" className="input" /></div>
          <div><label className="label">كلمة المرور</label><input {...register('password', { required: true })} type="password" className="input" /></div>
          <div>
            <label className="label">الدور</label>
            <select {...register('role', { required: true })} className="input">
              <option value="admin">مدير</option>
              <option value="accountant">محاسب</option>
              <option value="sales">مبيعات</option>
              <option value="warehouse">مخازن</option>
              <option value="hr">موارد بشرية</option>
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
