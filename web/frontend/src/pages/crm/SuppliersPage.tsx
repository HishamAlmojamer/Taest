import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { getSuppliers, createSupplier, updateSupplier, deleteSupplier, type Supplier } from '@/api/crm';
import { formatCurrency, formatDate } from '@/lib/utils';
import { IconBuilding, IconRefresh } from '@/components/ui/Icons';

export default function SuppliersPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Supplier | null>(null);
  const [deleting, setDeleting] = useState<Supplier | null>(null);

  const { register, handleSubmit, reset } = useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['suppliers', page, search],
    queryFn: () => getSuppliers({ page, pageSize: 10, search: search || undefined }),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['suppliers'] });

  const { data: parentsData } = useQuery({
    queryKey: ['suppliers-parents'],
    queryFn: () => getSuppliers({ pageSize: 100 }),
  });
  const parentOptions = (parentsData?.items || []).filter((p) => p.id !== editing?.id);

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateSupplier(editing.id, payload) : createSupplier(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteSupplier(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const openCreate = () => { setEditing(null); reset({ is_active: true, currency: 'SAR' }); setShowModal(true); };
  const openEdit = (item: Supplier) => {
    setEditing(item);
    reset({
      name: item.name, name_ar: item.nameAr, code: item.code, contact_person: item.contactPerson,
      phone: item.phone, email: item.email, city: item.city, website: item.website, tax_id: item.taxId,
      industry: item.industry, currency: item.currency || 'SAR', payment_terms: item.paymentTerms,
      parent_id: item.parentId ?? '',
      bank_name: item.bankName, bank_account: item.bankAccount, iban: item.iban, notes: item.notes,
      is_active: item.isActive,
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم المورد', sortable: true, render: (item) => (
      <div className="flex items-center gap-2"><span className="font-medium">{String(item.name)}</span>{!!item.code && <span className="text-xs text-gray-400 font-mono">{String(item.code)}</span>}</div>
    )},
    { key: 'contactPerson', header: 'مسؤول الاتصال', render: (item) => String(item.contactPerson || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'city', header: 'المدينة', render: (item) => String(item.city || '-') },
    { key: 'currentBalance', header: 'الرصيد', render: (item) => formatCurrency(Number(item.currentBalance)) },
    { key: 'createdAt', header: 'تاريخ الإضافة', render: (item) => formatDate(String(item.createdAt)) },
    { key: 'isActive', header: 'الحالة', render: (item) => <StatusBadge status={item.isActive ? 'ACTIVE' : 'INACTIVE'} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button className="btn-ghost px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); openEdit(item as unknown as Supplier); }}>تعديل</button>
        <button className="btn-ghost px-2 py-1 text-xs text-red-600" onClick={(e) => { e.stopPropagation(); setDeleting(item as unknown as Supplier); }}>حذف</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="الموردون"
        subtitle="إدارة موردي المؤسسة وبياناتهم المصرفية"
        icon={<IconBuilding className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}><span className="ml-2">+</span> مورد جديد</button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <input className="input w-64" placeholder="بحث بالاسم أو البريد أو الهاتف..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        {isLoading && <IconRefresh className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      {!data?.items?.length && !isLoading ? (
        <EmptyState title="لا يوجد موردون" description="ابدأ بإضافة أول مورد" />
      ) : (
        <DataTable
          columns={columns}
          data={(data?.items || []) as unknown as Record<string, unknown>[]}
          loading={isLoading}
          totalItems={data?.total || 0}
          page={page}
          pageSize={10}
          onPageChange={setPage}
          emptyTitle="لا يوجد موردون"
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل مورد' : 'مورد جديد'} size="xl">
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div><label className="label">اسم المورد *</label><input className="input" {...register('name', { required: true })} /></div>
            <div><label className="label">الاسم بالعربية</label><input className="input" {...register('name_ar')} /></div>
            <div><label className="label">الكود</label><input className="input" {...register('code')} /></div>
            <div><label className="label">مسؤول الاتصال</label><input className="input" {...register('contact_person')} /></div>
            <div><label className="label">الهاتف</label><input className="input" {...register('phone')} /></div>
            <div><label className="label">البريد</label><input className="input" type="email" {...register('email')} dir="ltr" /></div>
            <div><label className="label">المدينة</label><input className="input" {...register('city')} /></div>
            <div><label className="label">الموقع</label><input className="input" {...register('website')} dir="ltr" /></div>
            <div><label className="label">الرقم الضريبي</label><input className="input" {...register('tax_id')} /></div>
            <div><label className="label">القطاع</label><input className="input" {...register('industry')} /></div>
            <div>
              <label className="label">المورد الأب (فرع من)</label>
              <select className="input" {...register('parent_id')}>
                <option value="">بدون (جذر)</option>
                {parentOptions.map((p) => <option key={p.id} value={p.id}>{p.code ? `${p.code} - ` : ''}{p.name}</option>)}
              </select>
            </div>
            <div><label className="label">العملة</label><input className="input" {...register('currency')} defaultValue="SAR" /></div>
            <div><label className="label">شروط السداد</label><input className="input" {...register('payment_terms')} /></div>
            <div><label className="label">اسم البنك</label><input className="input" {...register('bank_name')} /></div>
            <div><label className="label">رقم الحساب</label><input className="input" {...register('bank_account')} dir="ltr" /></div>
            <div><label className="label">الآيبان</label><input className="input" {...register('iban')} dir="ltr" /></div>
            <div className="flex items-center gap-2 mt-6"><input type="checkbox" className="h-4 w-4" {...register('is_active')} /><label className="text-sm">مورد نشط</label></div>
          </div>
          <div><label className="label">ملاحظات</label><textarea className="input" rows={2} {...register('notes')} /></div>
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
        title="حذف المورد"
        message={`هل أنت متأكد من حذف المورد "${deleting?.name}"؟ لا يمكن حذف مورد لديه مشتريات.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
