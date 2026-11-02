import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { getLeads, createLead, updateLead, deleteLead, convertLead, createFollowup, type Lead } from '@/api/crm';
import { getEmployees } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { IconZap, IconRefresh } from '@/components/ui/Icons';
import type { HREmployee } from '@/types';

const LEAD_STATUSES = [
  { key: '', label: 'الكل', color: 'bg-gray-100 text-gray-700' },
  { key: 'new', label: 'جديد', color: 'bg-sky-100 text-sky-700' },
  { key: 'contacted', label: 'تم التواصل', color: 'bg-indigo-100 text-indigo-700' },
  { key: 'qualified', label: 'مؤهل', color: 'bg-violet-100 text-violet-700' },
  { key: 'proposal', label: 'عرض سعر', color: 'bg-amber-100 text-amber-700' },
  { key: 'negotiation', label: 'تفاوض', color: 'bg-orange-100 text-orange-700' },
  { key: 'won', label: 'فوز', color: 'bg-emerald-100 text-emerald-700' },
  { key: 'lost', label: 'خسارة', color: 'bg-red-100 text-red-700' },
];

export default function LeadsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [status, setStatus] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Lead | null>(null);
  const [deleting, setDeleting] = useState<Lead | null>(null);
  const [converting, setConverting] = useState<Lead | null>(null);
  const [followupTarget, setFollowupTarget] = useState<Lead | null>(null);

  const { register, handleSubmit, reset } = useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['leads', page, search, status],
    queryFn: () => getLeads({ page, pageSize: 10, search: search || undefined, status: status || undefined }),
  });

  const { data: leadsAll } = useQuery({
    queryKey: ['leads-all'],
    queryFn: () => getLeads({ pageSize: 100 }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees-options'], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees: HREmployee[] = empData?.items || [];
  const empName = (id?: number) => employees.find((e) => e.id === id)?.full_name || (id ? `#${id}` : '-');

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['leads'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateLead(editing.id, payload) : createLead(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteLead(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const convertMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => convertLead(converting!.id, payload),
    onSuccess: () => { invalidate(); setConverting(null); reset(); },
  });

  const followupMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => createFollowup(payload),
    onSuccess: () => { setFollowupTarget(null); reset(); },
  });

  const openCreate = () => { setEditing(null); reset({ status: 'new', lead_score: 0, is_active: true }); setShowModal(true); };
  const openEdit = (item: Lead) => {
    setEditing(item);
    reset({
      lead_name: item.leadName, company: item.company, contact_person: item.contactPerson,
      phone: item.phone, email: item.email, source: item.source, status: item.status,
      industry: item.industry, city: item.city, expected_amount: item.expectedAmount,
      budget: item.budget, lead_score: item.leadScore, assigned_to: item.assignedTo,
      expected_close_date: item.expectedCloseDate, next_follow_up: item.nextFollowUp,
      tags: item.tags, notes: item.notes, is_active: item.isActive,
    });
    setShowModal(true);
  };

  const countForStatus = (key: string) => {
    if (key === '') return leadsAll?.total ?? 0;
    const counts: Record<string, number> = {};
    for (const l of (leadsAll?.items || [])) counts[l.status || 'new'] = (counts[l.status || 'new'] || 0) + 1;
    return counts[key] || 0;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'leadName', header: 'الاسم', render: (item) => (
      <div className="flex items-center gap-2">
        <span className="font-medium">{String(item.leadName)}</span>
        {Number(item.leadScore) >= 5 && <span className="badge-warning">عالٍ</span>}
      </div>
    )},
    { key: 'company', header: 'الشركة', render: (item) => String(item.company || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'source', header: 'المصدر', render: (item) => String(item.source || '-') },
    { key: 'expectedAmount', header: 'القيمة المتوقعة', render: (item) => formatCurrency(Number(item.expectedAmount)) },
    { key: 'assignedTo', header: 'المسؤول', render: (item) => empName(Number(item.assignedTo)) },
    { key: 'nextFollowUp', header: 'المتابعة القادمة', render: (item) => formatDate(String(item.nextFollowUp)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button className="btn-ghost px-2 py-1 text-xs text-emerald-600" onClick={(e) => { e.stopPropagation(); setConverting(item as unknown as Lead); }}>تحويل</button>
        <button className="btn-ghost px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); setFollowupTarget(item as unknown as Lead); reset({ entity_type: 'lead', entity_id: Number(item.id), type: 'call', priority: 'medium', status: 'OPEN' }); }}>متابعة</button>
        <button className="btn-ghost px-2 py-1 text-xs" onClick={(e) => { e.stopPropagation(); openEdit(item as unknown as Lead); }}>تعديل</button>
        <button className="btn-ghost px-2 py-1 text-xs text-red-600" onClick={(e) => { e.stopPropagation(); setDeleting(item as unknown as Lead); }}>حذف</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="العملاء المحتملون"
        subtitle="إدارة العملاء المحتملين وخط أنابيب البيع"
        icon={<IconZap className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}><span className="ml-2">+</span> عميل محتمل جديد</button>
        }
      />

      <div className="flex flex-wrap gap-2">
        {LEAD_STATUSES.map((s) => (
          <button
            key={s.key}
            onClick={() => { setStatus(s.key); setPage(1); }}
            className={cn('px-3 py-1.5 rounded-full text-sm font-medium transition-colors', status === s.key ? 'bg-primary-600 text-white' : s.color)}
          >
            {s.label} ({countForStatus(s.key)})
          </button>
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <input className="input w-64" placeholder="بحث بالاسم أو الشركة أو البريد..." value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} />
        {isLoading && <IconRefresh className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      {!data?.items?.length && !isLoading ? (
        <EmptyState title="لا يوجد عملاء محتملون" description="ابدأ بإضافة أول عميل محتمل" />
      ) : (
        <DataTable
          columns={columns}
          data={(data?.items || []) as unknown as Record<string, unknown>[]}
          loading={isLoading}
          totalItems={data?.total || 0}
          page={page}
          pageSize={10}
          onPageChange={setPage}
          emptyTitle="لا يوجد عملاء محتملون"
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل عميل محتمل' : 'عميل محتمل جديد'} size="xl">
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div><label className="label">الاسم *</label><input className="input" {...register('lead_name', { required: true })} /></div>
            <div><label className="label">الشركة</label><input className="input" {...register('company')} /></div>
            <div><label className="label">مسؤول الاتصال</label><input className="input" {...register('contact_person')} /></div>
            <div><label className="label">الهاتف</label><input className="input" {...register('phone')} /></div>
            <div><label className="label">البريد</label><input className="input" type="email" {...register('email')} dir="ltr" /></div>
            <div><label className="label">المصدر</label>
              <select className="input" {...register('source')}>
                <option value="">اختر المصدر</option>
                <option value="website">الموقع الإلكتروني</option>
                <option value="social">وسائل التواصل</option>
                <option value="referral">إحالة</option>
                <option value="walkin">زيارة مباشرة</option>
                <option value="phone">اتصال هاتفي</option>
                <option value="other">أخرى</option>
              </select>
            </div>
            <div><label className="label">الحالة</label>
              <select className="input" {...register('status')}>
                <option value="new">جديد</option>
                <option value="contacted">تم التواصل</option>
                <option value="qualified">مؤهل</option>
                <option value="proposal">عرض سعر</option>
                <option value="negotiation">تفاوض</option>
                <option value="won">فوز</option>
                <option value="lost">خسارة</option>
              </select>
            </div>
            <div><label className="label">القطاع</label><input className="input" {...register('industry')} /></div>
            <div><label className="label">المدينة</label><input className="input" {...register('city')} /></div>
            <div><label className="label">القيمة المتوقعة</label><input className="input" type="number" step="0.01" {...register('expected_amount')} /></div>
            <div><label className="label">الميزانية</label><input className="input" type="number" step="0.01" {...register('budget')} /></div>
            <div><label className="label">درجة العميل (0-10)</label><input className="input" type="number" min="0" max="10" {...register('lead_score')} /></div>
            <div><label className="label">المسؤول</label>
              <select className="input" {...register('assigned_to')}>
                <option value="">بدون مسؤول</option>
                {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
              </select>
            </div>
            <div><label className="label">تاريخ الإغلاق المتوقع</label><input className="input" type="date" {...register('expected_close_date')} /></div>
            <div><label className="label">المتابعة القادمة</label><input className="input" type="date" {...register('next_follow_up')} /></div>
            <div><label className="label">الوسوم</label><input className="input" {...register('tags')} placeholder="مفصولة بفواصل" /></div>
          </div>
          <div><label className="label">ملاحظات</label><textarea className="input" rows={2} {...register('notes')} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={!!converting} onClose={() => setConverting(null)} title={`تحويل: ${converting?.leadName}`}>
        <form onSubmit={handleSubmit((d) => convertMutation.mutate({ ...d, create_opportunity: true }))} className="space-y-4">
          <p className="text-sm text-gray-500">سيتم إنشاء عميل جديد من بيانات العميل المحتمل وإنشاء فرصة بيع.</p>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">نوع العميل</label>
              <select className="input" {...register('customer_type')}><option value="customer">عميل</option><option value="company">شركة</option></select>
            </div>
            <div><label className="label">الرقم الضريبي</label><input className="input" {...register('tax_id')} /></div>
            <div><label className="label">حد الائتمان</label><input className="input" type="number" step="0.01" {...register('credit_limit')} defaultValue={0} /></div>
            <div><label className="label">القيمة المتوقعة للفرصة</label><input className="input" type="number" step="0.01" {...register('expected_amount')} defaultValue={converting?.expectedAmount || 0} /></div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setConverting(null)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={convertMutation.isPending}>{convertMutation.isPending ? 'جارٍ التحويل...' : 'تحويل'}</button>
          </div>
        </form>
      </Modal>

      <Modal isOpen={!!followupTarget} onClose={() => setFollowupTarget(null)} title="إضافة متابعة">
        <form onSubmit={handleSubmit((d) => followupMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div><label className="label">الموضوع</label><input className="input" {...register('subject')} /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">النوع</label>
              <select className="input" {...register('type')}><option value="call">اتصال</option><option value="email">بريد</option><option value="meeting">اجتماع</option><option value="task">مهمة</option><option value="whatsapp">واتساب</option></select>
            </div>
            <div><label className="label">الأولوية</label>
              <select className="input" {...register('priority')}><option value="low">منخفضة</option><option value="medium">متوسطة</option><option value="high">عالية</option></select>
            </div>
            <div><label className="label">الموعد</label><input className="input" type="datetime-local" {...register('due_date')} /></div>
            <div><label className="label">المسؤول</label>
              <select className="input" {...register('assigned_to')}>
                <option value="">بدون</option>
                {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
              </select>
            </div>
          </div>
          <div><label className="label">الوصف</label><textarea className="input" rows={2} {...register('description')} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setFollowupTarget(null)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={followupMutation.isPending}>إضافة</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف العميل المحتمل"
        message={`هل أنت متأكد من حذف "${deleting?.leadName}"؟`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
