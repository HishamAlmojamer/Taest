import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { getCustomers, createCustomer, updateCustomer, deleteCustomer, getSegments, type Customer, type Segment } from '@/api/crm';
import { formatCurrency, formatDate } from '@/lib/utils';
import { IconUsers, IconRefresh } from '@/components/ui/Icons';

export default function CustomersPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [segmentFilter, setSegmentFilter] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Customer | null>(null);
  const [deleting, setDeleting] = useState<Customer | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<string>('');

  const { register, handleSubmit, reset } = useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['customers', page, search, segmentFilter, selectedStatus],
    queryFn: () => getCustomers({
      page,
      pageSize: 10,
      search: search || undefined,
      segmentId: segmentFilter || undefined,
      isActive: selectedStatus === '' ? undefined : selectedStatus === 'active',
    }),
  });

  const { data: segmentsData } = useQuery({
    queryKey: ['segments'],
    queryFn: getSegments,
  });
  const segments: Segment[] = segmentsData?.items || [];

  const { data: parentsData } = useQuery({
    queryKey: ['customers-parents'],
    queryFn: () => getCustomers({ pageSize: 100 }),
  });
  const parentOptions = (parentsData?.items || []).filter((p) => p.id !== editing?.id);

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['customers'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateCustomer(editing.id, payload) : createCustomer(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCustomer(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const openCreate = () => { setEditing(null); reset({ is_active: true, currency: 'SAR', customer_type: 'customer' }); setShowModal(true); };
  const openEdit = (item: Customer) => {
    setEditing(item);
    reset({
      name: item.name,
      name_ar: item.nameAr,
      code: item.code,
      phone: item.phone,
      mobile: item.mobile,
      email: item.email,
      customer_type: item.customerType,
      segment_id: item.segmentId,
      parent_id: item.parentId ?? '',
      industry: item.industry,
      city: item.city,
      country: item.country,
      credit_limit: item.creditLimit,
      tax_id: item.taxId,
      national_id: item.nationalId,
      website: item.website,
      notes: item.notes,
      is_active: item.isActive,
      currency: item.currency || 'SAR',
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم العميل', sortable: true, render: (item) => (
      <div className="flex items-center gap-2">
        <span className="font-medium">{String(item.name)}</span>
        {!!item.code && <span className="text-xs text-gray-400 font-mono">{String(item.code)}</span>}
      </div>
    )},
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || item.mobile || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'city', header: 'المدينة', render: (item) => String(item.city || '-') },
    { key: 'segmentName', header: 'الشريحة', render: (item) => item.segmentName ? <span className="badge-success">{String(item.segmentName)}</span> : '-' },
    { key: 'balance', header: 'الرصيد', sortable: true, render: (item) => (
      <span className={Number(item.balance) < 0 ? 'text-red-600 font-medium' : 'font-medium'}>{formatCurrency(Number(item.balance))}</span>
    )},
    { key: 'creditLimit', header: 'حد الائتمان', render: (item) => formatCurrency(Number(item.creditLimit)) },
    { key: 'createdAt', header: 'تاريخ الإضافة', render: (item) => formatDate(String(item.createdAt)) },
    { key: 'isActive', header: 'الحالة', render: (item) => <StatusBadge status={item.isActive ? 'ACTIVE' : 'INACTIVE'} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex items-center gap-1">
        <button className="btn-ghost px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); navigate(`/crm/customers/${item.id}`); }}>ملف</button>
        <button className="btn-ghost px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); openEdit(item as unknown as Customer); }}>تعديل</button>
        <button className="btn-ghost px-2 py-1 text-xs text-red-600" onClick={(e) => { e.stopPropagation(); setDeleting(item as unknown as Customer); }}>حذف</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="العملاء"
        subtitle="إدارة عملاء المؤسسة وبياناتهم وشرائحهم"
        icon={<IconUsers className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}>
            <span className="ml-2">+</span> عميل جديد
          </button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <input
          className="input w-64"
          placeholder="بحث بالاسم أو البريد أو الهاتف..."
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
        />
        <select className="input w-44" value={segmentFilter} onChange={(e) => { setSegmentFilter(e.target.value); setPage(1); }}>
          <option value="">كل الشرائح</option>
          {segments.map((s) => <option key={s.id} value={s.id}>{s.nameAr || s.name}</option>)}
        </select>
        <select className="input w-40" value={selectedStatus} onChange={(e) => { setSelectedStatus(e.target.value); setPage(1); }}>
          <option value="">كل الحالات</option>
          <option value="active">نشط</option>
          <option value="inactive">غير نشط</option>
        </select>
        {isLoading && <IconRefresh className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      {!data?.items?.length && !isLoading ? (
        <EmptyState title="لا يوجد عملاء" description="ابدأ بإضافة أول عميل" />
      ) : (
        <DataTable
          columns={columns}
          data={(data?.items || []) as unknown as Record<string, unknown>[]}
          loading={isLoading}
          totalItems={data?.total || 0}
          page={page}
          pageSize={10}
          onPageChange={setPage}
          onRowClick={(item) => navigate(`/crm/customers/${item.id}`)}
          searchPlaceholder=""
          emptyTitle="لا يوجد عملاء"
          emptyDescription="ابدأ بإضافة أول عميل"
        />
      )}

      <Modal
        isOpen={showModal}
        onClose={() => { setShowModal(false); setEditing(null); }}
        title={editing ? 'تعديل عميل' : 'عميل جديد'}
        size="xl"
      >
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label className="label">اسم العميل *</label>
              <input className="input" {...register('name', { required: true })} placeholder="الاسم كاملاً" />
            </div>
            <div>
              <label className="label">الاسم بالعربية</label>
              <input className="input" {...register('name_ar')} placeholder="الاسم بالعربية" />
            </div>
            <div>
              <label className="label">الكود</label>
              <input className="input" {...register('code')} placeholder="CUST-001" />
            </div>
            <div>
              <label className="label">رقم الهاتف</label>
              <input className="input" {...register('phone')} placeholder="05xxxxxxxx" />
            </div>
            <div>
              <label className="label">الجوال</label>
              <input className="input" {...register('mobile')} />
            </div>
            <div>
              <label className="label">البريد الإلكتروني</label>
              <input className="input" type="email" {...register('email')} dir="ltr" />
            </div>
            <div>
              <label className="label">نوع العميل</label>
              <select className="input" {...register('customer_type')}>
                <option value="customer">عميل نقدي</option>
                <option value="company">شركة</option>
                <option value="wholesale">جملة</option>
                <option value="retail">تجزئة</option>
              </select>
            </div>
            <div>
              <label className="label">الشريحة</label>
              <select className="input" {...register('segment_id')}>
                <option value="">بدون شريحة</option>
                {segments.map((s) => <option key={s.id} value={s.id}>{s.nameAr || s.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">العميل الأب (فرع من)</label>
              <select className="input" {...register('parent_id')}>
                <option value="">بدون (جذر)</option>
                {parentOptions.map((p) => <option key={p.id} value={p.id}>{p.code ? `${p.code} - ` : ''}{p.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">القطاع</label>
              <input className="input" {...register('industry')} placeholder="مثال: تجارة التجزئة" />
            </div>
            <div>
              <label className="label">المدينة</label>
              <input className="input" {...register('city')} />
            </div>
            <div>
              <label className="label">الدولة</label>
              <input className="input" {...register('country')} placeholder="السعودية" />
            </div>
            <div>
              <label className="label">حد الائتمان</label>
              <input className="input" type="number" step="0.01" {...register('credit_limit')} />
            </div>
            <div>
              <label className="label">الرقم الضريبي</label>
              <input className="input" {...register('tax_id')} dir="ltr" />
            </div>
            <div>
              <label className="label">رقم الهوية</label>
              <input className="input" {...register('national_id')} />
            </div>
            <div>
              <label className="label">الموقع الإلكتروني</label>
              <input className="input" {...register('website')} dir="ltr" />
            </div>
            <div className="flex items-center gap-2 mt-6">
              <input type="checkbox" className="h-4 w-4" {...register('is_active')} />
              <label className="text-sm">عميل نشط</label>
            </div>
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea className="input" rows={2} {...register('notes')} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف العميل"
        message={`هل أنت متأكد من حذف العميل "${deleting?.name}"؟ لا يمكن حذف عميل لديه فواتير مبيعات.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
