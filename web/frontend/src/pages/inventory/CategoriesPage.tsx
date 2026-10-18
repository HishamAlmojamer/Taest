import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getCategories, createCategory, deleteCategory } from '@/api/inventory';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ['categories', page],
    queryFn: () => getCategories({ page, pageSize: 10 }),
  });

  const createMutation = useMutation({
    mutationFn: createCategory,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['categories'] }); setShowModal(false); },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['categories'] }),
  });

  const { register, handleSubmit, reset } = useForm();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم التصنيف', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'productCount', header: 'عدد المنتجات', render: (item) => String(item.productCount || 0) },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد؟')) deleteMutation.mutate(String(item.id)); }} className="text-red-500 hover:text-red-700 text-sm">حذف</button>
    )},
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">التصنيفات</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ تصنيف جديد</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="تصنيف جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div><label className="label">اسم التصنيف</label><input {...register('name', { required: true })} className="input" /></div>
          <div><label className="label">الاسم بالعربية</label><input {...register('nameAr')} className="input" /></div>
          <div><label className="label">الوصف</label><textarea {...register('description')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
