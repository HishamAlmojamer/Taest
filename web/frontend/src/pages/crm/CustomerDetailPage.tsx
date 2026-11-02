import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useForm } from 'react-hook-form';
import { cn, formatCurrency, formatDate, formatDateTime } from '@/lib/utils';
import {
  getCustomer, getCustomerActivities, getCustomerLoyalty,
  createCustomerContact, updateCustomerContact, deleteCustomerContact,
  createCustomerAddress, updateCustomerAddress, deleteCustomerAddress,
  getOpportunities, getFollowups, completeFollowup, deleteFollowup,
  adjustCustomerLoyalty,
  type CustomerContact, type CustomerAddress, type Opportunity, type FollowUp, type ActivityItem,
} from '@/api/crm';
import { IconArrowRight, IconUsers, IconMapPin, IconActivity, IconTarget, IconCalendarClock, IconStar, IconPencil, IconTrash, IconPlus } from '@/components/ui/Icons';

type TabKey = 'overview' | 'contacts' | 'addresses' | 'activities' | 'opportunities' | 'followups';

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: 'overview', label: 'نظرة عامة', icon: <IconActivity className="h-4 w-4" /> },
  { key: 'contacts', label: 'جهات الاتصال', icon: <IconUsers className="h-4 w-4" /> },
  { key: 'addresses', label: 'العناوين', icon: <IconMapPin className="h-4 w-4" /> },
  { key: 'activities', label: 'النشاط', icon: <IconActivity className="h-4 w-4" /> },
  { key: 'opportunities', label: 'الفرص', icon: <IconTarget className="h-4 w-4" /> },
  { key: 'followups', label: 'المتابعات', icon: <IconCalendarClock className="h-4 w-4" /> },
];

export default function CustomerDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<TabKey>('overview');

  const [contactModal, setContactModal] = useState(false);
  const [editingContact, setEditingContact] = useState<CustomerContact | null>(null);
  const [deletingContact, setDeletingContact] = useState<CustomerContact | null>(null);
  const [addressModal, setAddressModal] = useState(false);
  const [editingAddress, setEditingAddress] = useState<CustomerAddress | null>(null);
  const [deletingAddress, setDeletingAddress] = useState<CustomerAddress | null>(null);
  const [loyaltyModal, setLoyaltyModal] = useState(false);

  const { register, handleSubmit, reset } = useForm();

  const { data: customer, isLoading } = useQuery({
    queryKey: ['customer', id],
    queryFn: () => getCustomer(id!),
    enabled: !!id,
  });

  const { data: activitiesData } = useQuery({
    queryKey: ['customer-activities', id],
    queryFn: () => getCustomerActivities(id!),
    enabled: !!id,
  });

  const { data: loyaltyData } = useQuery({
    queryKey: ['customer-loyalty', id],
    queryFn: () => getCustomerLoyalty(id!),
    enabled: !!id,
  });

  const { data: opportunitiesData } = useQuery({
    queryKey: ['customer-opportunities', id],
    queryFn: () => getOpportunities({ customerId: id }),
    enabled: !!id,
  });

  const { data: followupsData } = useQuery({
    queryKey: ['customer-followups', id],
    queryFn: () => getFollowups({ entityType: 'customer', entityId: id }),
    enabled: !!id,
  });

  const invalidateCustomer = () => {
    queryClient.invalidateQueries({ queryKey: ['customer', id] });
    queryClient.invalidateQueries({ queryKey: ['customer-activities', id] });
    queryClient.invalidateQueries({ queryKey: ['customer-followups', id] });
    queryClient.invalidateQueries({ queryKey: ['customer-opportunities', id] });
  };

  const saveContactMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editingContact ? updateCustomerContact(editingContact.id, payload) : createCustomerContact(id!, payload),
    onSuccess: () => { invalidateCustomer(); setContactModal(false); setEditingContact(null); reset(); },
  });

  const deleteContactMutation = useMutation({
    mutationFn: (contactId: number) => deleteCustomerContact(contactId),
    onSuccess: () => { invalidateCustomer(); setDeletingContact(null); },
  });

  const saveAddressMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editingAddress ? updateCustomerAddress(editingAddress.id, payload) : createCustomerAddress(id!, payload),
    onSuccess: () => { invalidateCustomer(); setAddressModal(false); setEditingAddress(null); reset(); },
  });

  const deleteAddressMutation = useMutation({
    mutationFn: (addressId: number) => deleteCustomerAddress(addressId),
    onSuccess: () => { invalidateCustomer(); setDeletingAddress(null); },
  });

  const completeFollowupMutation = useMutation({
    mutationFn: (followupId: number) => completeFollowup(followupId),
    onSuccess: () => invalidateCustomer(),
  });

  const deleteFollowupMutation = useMutation({
    mutationFn: (followupId: number) => deleteFollowup(followupId),
    onSuccess: () => invalidateCustomer(),
  });

  const adjustLoyaltyMutation = useMutation({
    mutationFn: (points: number) => adjustCustomerLoyalty(id!, points),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['customer-loyalty', id] }); setLoyaltyModal(false); reset(); },
  });

  if (isLoading) return <div className="p-8 text-center text-gray-500">جارٍ التحميل...</div>;
  if (!customer) return <div className="p-8 text-center text-gray-500">العميل غير موجود</div>;

  const activities: ActivityItem[] = activitiesData?.items || [];
  const salesActivities = activities.filter((a) => a.type === 'sale');
  const paymentsActivities = activities.filter((a) => a.type === 'payment');
  const openOpps = (opportunitiesData?.items || []).filter((o) => o.status === 'OPEN');
  const totalSales = salesActivities.reduce((sum, a) => sum + (a.amount || 0), 0);

  const contactColumns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'title', header: 'المسمى', render: (item) => String(item.title || '-') },
    { key: 'department', header: 'القسم', render: (item) => String(item.department || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || item.mobile || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'isPrimary', header: 'رئيسي', render: (item) => item.isPrimary ? <span className="badge-success">نعم</span> : '-' },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button className="btn-ghost p-1" onClick={() => {
          const c = item as unknown as CustomerContact;
          setEditingContact(c);
          reset({ name: c.name, title: c.title, department: c.department, phone: c.phone, mobile: c.mobile, email: c.email, is_primary: c.isPrimary });
          setContactModal(true);
        }}><IconPencil className="h-4 w-4" /></button>
        <button className="btn-ghost p-1 text-red-600" onClick={() => setDeletingContact(item as unknown as CustomerContact)}><IconTrash className="h-4 w-4" /></button>
      </div>
    )},
  ];

  const addressColumns: Column<Record<string, unknown>>[] = [
    { key: 'addressType', header: 'النوع', render: (item) => String(item.addressType || 'billing') },
    { key: 'addressLine1', header: 'العنوان', render: (item) => String(item.addressLine1 || item.addressLine2 || '-') },
    { key: 'city', header: 'المدينة', render: (item) => String(item.city || '-') },
    { key: 'region', header: 'المنطقة', render: (item) => String(item.region || '-') },
    { key: 'country', header: 'الدولة', render: (item) => String(item.country || '-') },
    { key: 'isPrimary', header: 'رئيسي', render: (item) => item.isPrimary ? <span className="badge-success">نعم</span> : '-' },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button className="btn-ghost p-1" onClick={() => {
          const a = item as unknown as CustomerAddress;
          setEditingAddress(a);
          reset({ address_type: a.addressType, address_line1: a.addressLine1, address_line2: a.addressLine2, city: a.city, region: a.region, country: a.country, postal_code: a.postalCode, is_primary: a.isPrimary });
          setAddressModal(true);
        }}><IconPencil className="h-4 w-4" /></button>
        <button className="btn-ghost p-1 text-red-600" onClick={() => setDeletingAddress(item as unknown as CustomerAddress)}><IconTrash className="h-4 w-4" /></button>
      </div>
    )},
  ];

  const infoRow = (label: string, value?: string | number | null) => (
    <div className="flex justify-between border-b border-gray-100 dark:border-zinc-800 py-2 text-sm">
      <span className="text-gray-500 dark:text-zinc-400">{label}</span>
      <span className="font-medium text-gray-900 dark:text-zinc-100">{value || '-'}</span>
    </div>
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title={customer.name}
        subtitle={`${customer.code || ''} ${customer.email || ''}`}
        icon={<IconUsers className="h-6 w-6" />}
        actions={
          <button className="btn-ghost" onClick={() => navigate('/crm/customers')}>
            <IconArrowRight className="h-4 w-4 ml-1" /> رجوع للقائمة
          </button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card p-4">
          <p className="text-sm text-gray-500">إجمالي المبيعات</p>
          <p className="mt-1 text-xl font-bold">{formatCurrency(totalSales)}</p>
          <p className="text-xs text-gray-400">{salesActivities.length} فاتورة</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">الرصيد الحالي</p>
          <p className={cn('mt-1 text-xl font-bold', customer.balance < 0 ? 'text-red-600' : '')}>{formatCurrency(customer.balance)}</p>
          <p className="text-xs text-gray-400">حد ائتمان {formatCurrency(customer.creditLimit)}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">المدفوعات</p>
          <p className="mt-1 text-xl font-bold">{paymentsActivities.length}</p>
          <p className="text-xs text-gray-400">دفعة مستلمة</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">الفرص المفتوحة</p>
          <p className="mt-1 text-xl font-bold">{openOpps.length}</p>
          <p className="text-xs text-gray-400">{formatCurrency(openOpps.reduce((s, o) => s + (o.expectedAmount || 0), 0))} متوقع</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-zinc-700">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              'flex items-center gap-2 px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors',
              tab === t.key
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-800 dark:hover:text-zinc-200'
            )}
          >
            {t.icon}{t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="card p-5 lg:col-span-2">
            <h3 className="font-bold mb-3">البيانات الأساسية</h3>
            <div className="grid sm:grid-cols-2 gap-x-6">
              {infoRow('الاسم', customer.name)}
              {infoRow('الاسم بالعربية', customer.nameAr)}
              {infoRow('الكود', customer.code)}
              {infoRow('النوع', customer.customerType)}
              {infoRow('الشريحة', customer.segmentName)}
              {infoRow('القطاع', customer.industry)}
              {infoRow('الرقم الضريبي', customer.taxId)}
              {infoRow('رقم الهوية', customer.nationalId)}
              {infoRow('الهاتف', customer.phone)}
              {infoRow('الجوال', customer.mobile)}
              {infoRow('البريد', customer.email)}
              {infoRow('الموقع', customer.website)}
              {infoRow('المدينة', customer.city)}
              {infoRow('الدولة', customer.country)}
              {infoRow('العنوان', customer.address)}
              {infoRow('العملة', customer.currency)}
              {infoRow('قائمة الأسعار', customer.priceList)}
              {infoRow('تاريخ الإضافة', formatDate(customer.createdAt))}
            </div>
            {customer.notes && (
              <div className="mt-4 rounded-lg bg-amber-50 dark:bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-300">
                <strong>ملاحظات: </strong>{customer.notes}
              </div>
            )}
          </div>
          <div className="space-y-4">
            <div className="card p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-bold flex items-center gap-2"><IconStar className="h-4 w-4 text-amber-500" /> برنامج الولاء</h3>
                <button className="btn-ghost px-2 py-1 text-xs" onClick={() => setLoyaltyModal(true)}>تعديل</button>
              </div>
              <div className="mt-3 space-y-2 text-sm">
                {infoRow('المستوى', loyaltyData?.tier)}
                {infoRow('نقاط الرصيد', loyaltyData?.pointsBalance)}
                {infoRow('إجمالي النقاط', loyaltyData?.totalPointsEarned)}
              </div>
            </div>
            {customer.balance > customer.creditLimit && customer.creditLimit > 0 && (
              <div className="rounded-xl bg-red-50 dark:bg-red-500/10 p-4 text-sm text-red-700 dark:text-red-300">
                <strong>تنبيه:</strong> رصيد العميل يتجاوز حد الائتمان.
              </div>
            )}
          </div>
        </div>
      )}

      {tab === 'contacts' && (
        <div className="card">
          <div className="flex justify-end p-3">
            <button className="btn-primary px-3 py-1.5 text-sm" onClick={() => { setEditingContact(null); reset({ is_primary: false }); setContactModal(true); }}>
              <IconPlus className="h-4 w-4 ml-1 inline" /> إضافة جهة اتصال
            </button>
          </div>
          <DataTable columns={contactColumns} data={(customer.contacts || []) as unknown as Record<string, unknown>[]} emptyTitle="لا توجد جهات اتصال" />
        </div>
      )}

      {tab === 'addresses' && (
        <div className="card">
          <div className="flex justify-end p-3">
            <button className="btn-primary px-3 py-1.5 text-sm" onClick={() => { setEditingAddress(null); reset({ address_type: 'billing', is_primary: false }); setAddressModal(true); }}>
              <IconPlus className="h-4 w-4 ml-1 inline" /> إضافة عنوان
            </button>
          </div>
          <DataTable columns={addressColumns} data={(customer.addresses || []) as unknown as Record<string, unknown>[]} emptyTitle="لا توجد عناوين" />
        </div>
      )}

      {tab === 'activities' && (
        <div className="card p-5">
          <h3 className="font-bold mb-4">سجل النشاط</h3>
          {activities.length === 0 && <p className="text-gray-400 text-sm">لا يوجد نشاط بعد لهذا العميل</p>}
          <div className="space-y-3">
            {activities.map((a) => (
              <div key={`${a.type}-${a.id}`} className="flex items-center gap-3 border border-gray-100 dark:border-zinc-800 rounded-lg p-3">
                <div className={cn(
                  'h-9 w-9 rounded-lg flex items-center justify-center text-xs font-bold',
                  a.type === 'sale' && 'bg-emerald-50 text-emerald-600',
                  a.type === 'payment' && 'bg-sky-50 text-sky-600',
                  a.type === 'opportunity' && 'bg-violet-50 text-violet-600',
                  a.type === 'quotation' && 'bg-amber-50 text-amber-600',
                  a.type === 'followup' && 'bg-rose-50 text-rose-600',
                )}>
                  {a.type === 'sale' ? 'ف' : a.type === 'payment' ? 'د' : a.type === 'opportunity' ? 'ص' : a.type === 'quotation' ? 'ع' : 'م'}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{a.title}</p>
                  <p className="text-xs text-gray-400">{formatDateTime(a.date)}</p>
                </div>
                {a.amount != null && <span className="text-sm font-semibold">{formatCurrency(a.amount)}</span>}
                <StatusBadge status={String(a.status)} />
              </div>
            ))}
          </div>
        </div>
      )}

      {tab === 'opportunities' && (
        <div className="card">
          <DataTable
            columns={[
              { key: 'name', header: 'الفرصة', render: (item) => <span className="font-medium">{String(item.name)}</span> },
              { key: 'stage', header: 'المرحلة', render: (item) => <StatusBadge status={String(item.stageName || item.stage || '')} /> },
              { key: 'expectedAmount', header: 'القيمة المتوقعة', render: (item) => formatCurrency(Number(item.expectedAmount)) },
              { key: 'probability', header: 'الاحتمالية', render: (item) => `${Number(item.probability)}%` },
              { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
              { key: 'expectedCloseDate', header: 'الإغلاق المتوقع', render: (item) => formatDate(String(item.expectedCloseDate)) },
            ]}
            data={((opportunitiesData?.items || []) as unknown) as Record<string, unknown>[]}
            emptyTitle="لا توجد فرص لهذا العميل"
          />
        </div>
      )}

      {tab === 'followups' && (
        <div className="card">
          <DataTable
            columns={[
              { key: 'subject', header: 'الموضوع', render: (item) => <span className="font-medium">{String(item.subject || item.type || '-')}</span> },
              { key: 'type', header: 'النوع', render: (item) => String(item.type || '-') },
              { key: 'dueDate', header: 'الموعد', render: (item) => formatDateTime(String(item.dueDate)) },
              { key: 'priority', header: 'الأولوية', render: (item) => <StatusBadge status={String(item.priority).toUpperCase()} /> },
              { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
              { key: 'actions', header: 'إجراءات', render: (item) => (
                <div className="flex gap-1">
                  {item.status === 'OPEN' && (
                    <button className="btn-ghost px-2 py-1 text-xs text-emerald-600" onClick={() => completeFollowupMutation.mutate(Number(item.id))}>إتمام</button>
                  )}
                  <button className="btn-ghost px-2 py-1 text-xs text-red-600" onClick={() => deleteFollowupMutation.mutate(Number(item.id))}>حذف</button>
                </div>
              )},
            ]}
            data={((followupsData?.items || []) as unknown) as Record<string, unknown>[]}
            emptyTitle="لا توجد متابعات"
          />
        </div>
      )}

      <Modal isOpen={contactModal} onClose={() => { setContactModal(false); setEditingContact(null); }} title={editingContact ? 'تعديل جهة اتصال' : 'إضافة جهة اتصال'}>
        <form onSubmit={handleSubmit((d) => saveContactMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">الاسم *</label><input className="input" {...register('name', { required: true })} /></div>
            <div><label className="label">المسمى الوظيفي</label><input className="input" {...register('title')} /></div>
            <div><label className="label">القسم</label><input className="input" {...register('department')} /></div>
            <div><label className="label">الهاتف</label><input className="input" {...register('phone')} /></div>
            <div><label className="label">الجوال</label><input className="input" {...register('mobile')} /></div>
            <div><label className="label">البريد</label><input className="input" type="email" {...register('email')} dir="ltr" /></div>
          </div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-4 w-4" {...register('is_primary')} /> جهة اتصال رئيسية</label>
          <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={() => { setContactModal(false); setEditingContact(null); }}>إلغاء</button><button className="btn-primary" disabled={saveContactMutation.isPending}>حفظ</button></div>
        </form>
      </Modal>

      <Modal isOpen={addressModal} onClose={() => { setAddressModal(false); setEditingAddress(null); }} title={editingAddress ? 'تعديل عنوان' : 'إضافة عنوان'}>
        <form onSubmit={handleSubmit((d) => saveAddressMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">النوع</label>
              <select className="input" {...register('address_type')}><option value="billing">فوترة</option><option value="shipping">شحن</option><option value="other">أخرى</option></select>
            </div>
            <div><label className="label">المدينة</label><input className="input" {...register('city')} /></div>
            <div><label className="label">المنطقة</label><input className="input" {...register('region')} /></div>
            <div><label className="label">الدولة</label><input className="input" {...register('country')} /></div>
            <div><label className="label">الرمز البريدي</label><input className="input" {...register('postal_code')} /></div>
          </div>
          <div><label className="label">السطر الأول</label><input className="input" {...register('address_line1')} /></div>
          <div><label className="label">السطر الثاني</label><input className="input" {...register('address_line2')} /></div>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" className="h-4 w-4" {...register('is_primary')} /> عنوان رئيسي</label>
          <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={() => { setAddressModal(false); setEditingAddress(null); }}>إلغاء</button><button className="btn-primary" disabled={saveAddressMutation.isPending}>حفظ</button></div>
        </form>
      </Modal>

      <Modal isOpen={loyaltyModal} onClose={() => setLoyaltyModal(false)} title="تعديل نقاط الولاء">
        <form onSubmit={handleSubmit((d) => adjustLoyaltyMutation.mutate(Number(d.points)))} className="space-y-4">
          <div><label className="label">النقاط (موجب للإضافة، سالب للخصم)</label><input className="input" type="number" step="1" {...register('points', { required: true })} /></div>
          <div className="flex justify-end gap-2"><button type="button" className="btn-ghost" onClick={() => setLoyaltyModal(false)}>إلغاء</button><button className="btn-primary">حفظ</button></div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={!!deletingContact} onClose={() => setDeletingContact(null)} onConfirm={() => deletingContact && deleteContactMutation.mutate(deletingContact.id)} title="حذف جهة اتصال" message="هل أنت متأكد من حذف جهة الاتصال؟" confirmText="حذف" />
      <ConfirmDialog isOpen={!!deletingAddress} onClose={() => setDeletingAddress(null)} onConfirm={() => deletingAddress && deleteAddressMutation.mutate(deletingAddress.id)} title="حذف عنوان" message="هل أنت متأكد من حذف العنوان؟" confirmText="حذف" />
    </div>
  );
}
