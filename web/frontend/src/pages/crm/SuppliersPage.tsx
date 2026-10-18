import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getSuppliers, createSupplier } from '@/api/crm';
import { formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';

export default function SuppliersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['suppliers', page, search],
    queryFn: () => getSuppliers({ page, pageSize: 10, search }),
  });

  const createMutation = useMutation({
    mutationFn: createSupplier,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['suppliers'] }); setShowModal(false); },
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم المورد', sortable: true, render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'city', header: 'المدينة', render: (item) => String(item.city || '-') },
    { key: 'balance', header: 'الرصيد', render: (item) => formatCurrency(Number(item.balance)) },
    { key: 'isActive', header: 'الحالة', render: (item) => <StatusBadge status={item.isActive ? 'active' : 'inactive'} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الموردين</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ مورد جديد</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث..." />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="مورد جديد" size="lg">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          name: d.name,
          contactPerson: d.contactPerson,
          email: d.email,
          phone: d.phone,
          address: d.address,
        } as never))} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">اسم المورد</label><input {...register('name', { required: true })} className="input" /></div>
            <div><label className="label">جهة الاتصال</label><input {...register('contactPerson')} className="input" /></div>
            <div><label className="label">البريد الإلكتروني</label><input {...register('email')} type="email" className="input" /></div>
            <div><label className="label">الهاتف</label><input {...register('phone')} className="input" /></div>
          </div>
          <div><label className="label">العنوان</label><textarea {...register('address')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
