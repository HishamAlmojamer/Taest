import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getCustomers, createCustomer } from '@/api/crm';
import { formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';

export default function CustomersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['customers', page, search],
    queryFn: () => getCustomers({ page, pageSize: 10, search }),
  });

  const createMutation = useMutation({
    mutationFn: createCustomer,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['customers'] }); setShowModal(false); },
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم العميل', sortable: true, render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'city', header: 'المدينة', render: (item) => String(item.city || '-') },
    { key: 'balance', header: 'الرصيد', render: (item) => formatCurrency(Number(item.balance)) },
    { key: 'isActive', header: 'الحالة', render: (item) => <StatusBadge status={item.isActive ? 'active' : 'inactive'} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">العملاء</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ عميل جديد</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالاسم أو البريد..." />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="عميل جديد" size="lg">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          name: d.name,
          email: d.email,
          phone: d.phone,
          address: d.address,
          creditLimit: d.creditLimit || 0,
          currentBalance: 0,
          companyId: 1,
        } as never))} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">اسم العميل</label><input {...register('name', { required: true })} className="input" /></div>
            <div><label className="label">البريد الإلكتروني</label><input {...register('email')} type="email" className="input" /></div>
            <div><label className="label">الهاتف</label><input {...register('phone')} className="input" /></div>
            <div><label className="label">حد الائتمان</label><input {...register('creditLimit', { valueAsNumber: true })} type="number" className="input" /></div>
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
