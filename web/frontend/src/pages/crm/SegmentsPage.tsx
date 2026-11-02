import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { getSegments, createSegment, updateSegment, deleteSegment, type Segment } from '@/api/crm';
import { IconLayers, IconPlus, IconPencil, IconTrash } from '@/components/ui/Icons';

export default function SegmentsPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Segment | null>(null);
  const [deleting, setDeleting] = useState<Segment | null>(null);

  const { register, handleSubmit, reset } = useForm();

  const { data, isLoading } = useQuery({ queryKey: ['segments'], queryFn: getSegments });
  const segments: Segment[] = data?.items || [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['segments'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateSegment(editing.id, payload) : createSegment(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSegment(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const openCreate = () => { setEditing(null); reset({ is_active: true }); setShowModal(true); };
  const openEdit = (item: Segment) => {
    setEditing(item);
    reset({ name: item.name, name_ar: item.nameAr, description: item.description, is_active: item.isActive });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'الاسم', render: (item) => (
      <div>
        <p className="font-medium">{String(item.name)}</p>
        {!!item.nameAr && <p className="text-xs text-gray-400">{String(item.nameAr)}</p>}
      </div>
    )},
    { key: 'description', header: 'الوصف', render: (item) => String(item.description || '-') },
    { key: 'customerCount', header: 'عدد العملاء', render: (item) => <span className="badge-primary">{String(item.customerCount)}</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => item.isActive ? <span className="badge-success">نشطة</span> : <span className="badge-gray">معطلة</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button className="btn-ghost p-1" onClick={(e) => { e.stopPropagation(); openEdit(item as unknown as Segment); }}><IconPencil className="h-4 w-4" /></button>
        <button className="btn-ghost p-1 text-red-600" onClick={(e) => { e.stopPropagation(); setDeleting(item as unknown as Segment); }}><IconTrash className="h-4 w-4" /></button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="شرائح العملاء"
        subtitle="تصنيف العملاء حسب الشرائح لتحسين الاستهداف"
        icon={<IconLayers className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}>
            <IconPlus className="h-4 w-4 ml-1 inline" /> شريحة جديدة
          </button>
        }
      />

      {segments.length === 0 && !isLoading ? (
        <EmptyState title="لا توجد شرائح" description="أنشئ أول شريحة لتصنيف العملاء" />
      ) : (
        <DataTable
          columns={columns}
          data={(segments as unknown) as Record<string, unknown>[]}
          loading={isLoading}
          emptyTitle="لا توجد شرائح"
          onRowClick={(item) => openEdit(item as unknown as Segment)}
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل شريحة' : 'شريحة جديدة'}>
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div><label className="label">الاسم *</label><input className="input" {...register('name', { required: true })} /></div>
          <div><label className="label">الاسم بالعربية</label><input className="input" {...register('name_ar')} /></div>
          <div><label className="label">الوصف</label><textarea className="input" rows={2} {...register('description')} /></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-4 w-4" {...register('is_active')} /> شريحة نشطة</label>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف الشريحة"
        message={`هل أنت متأكد من حذف الشريحة "${deleting?.name}"؟ سيتم إزالة التصنيف عن عملائها فقط.`}
        confirmText="حذف"
      />
    </div>
  );
}
