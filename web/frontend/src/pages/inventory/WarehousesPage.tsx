import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getWarehouses, createWarehouse, deleteWarehouse } from '@/api/inventory';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';

export default function WarehousesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ['warehouses', page],
    queryFn: () => getWarehouses({ page, pageSize: 10 }),
  });

  const createMutation = useMutation({
    mutationFn: createWarehouse,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['warehouses'] }); setShowModal(false); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteWarehouse,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['warehouses'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم المخزن', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'address', header: 'العنوان', render: (item) => String(item.address || '-') },
    { key: 'manager', header: 'المدير', render: (item) => String(item.manager || '-') },
    { key: 'productCount', header: 'المنتجات', render: (item) => String(item.productCount || 0) },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد؟')) deleteMutation.mutate(String(item.id)); }} className="text-red-500 hover:text-red-700 text-sm">حذف</button>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="المخازن"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ مخزن جديد</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="مخزن جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div><label className="label">اسم المخزن</label><input {...register('name', { required: true })} className="input" /></div>
          <div><label className="label">الاسم بالعربية</label><input {...register('nameAr')} className="input" /></div>
          <div><label className="label">العنوان</label><input {...register('address')} className="input" /></div>
          <div><label className="label">المدير المسؤول</label><input {...register('manager')} className="input" /></div>
          <div><label className="label">الهاتف</label><input {...register('phone')} className="input" /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
