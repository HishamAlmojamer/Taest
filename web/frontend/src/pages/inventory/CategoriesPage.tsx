import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getCategories, createCategory, deleteCategory } from '@/api/inventory';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';

export default function CategoriesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const { data, isLoading } = useQuery({
    queryKey: ['categories', page],
    queryFn: () => getCategories({ page, pageSize: 10 }),
  });

  const createMutation = useMutation({
    mutationFn: createCategory,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['categories'] }); setShowModal(false); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteCategory,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['categories'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
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
      <PageHeader
        title="التصنيفات"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" /></svg>}
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ تصنيف جديد</button>}
      />
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
