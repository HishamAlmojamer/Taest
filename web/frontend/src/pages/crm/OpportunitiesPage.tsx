import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';
import {
  getOpportunityStages, getOpportunities, getCustomers,
  createOpportunity, updateOpportunity, deleteOpportunity,
  moveOpportunity, closeOpportunity,
  type OpportunityStage, type Opportunity, type Customer,
} from '@/api/crm';
import { getEmployees } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { IconTarget, IconPlus, IconPencil, IconTrash, IconChevronLeft, IconChevronRight, IconXCircle, IconCheckCircle } from '@/components/ui/Icons';
import type { HREmployee } from '@/types';

export default function OpportunitiesPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Opportunity | null>(null);
  const [deleting, setDeleting] = useState<Opportunity | null>(null);
  const [closing, setClosing] = useState<Opportunity | null>(null);
  const [stageFilter, setStageFilter] = useState<string>('');
  const [search, setSearch] = useState('');
  const [dragId, setDragId] = useState<number | null>(null);

  const { register, handleSubmit, reset } = useForm();

  const { data: stagesData } = useQuery({ queryKey: ['opp-stages'], queryFn: getOpportunityStages });
  const stages: OpportunityStage[] = (stagesData?.items || []).filter((s) => s.isActive);

  const { data: oppsData } = useQuery({
    queryKey: ['opportunities', stageFilter, search],
    queryFn: () => getOpportunities({ stageId: stageFilter || undefined, search: search || undefined }),
  });
  const opportunities: Opportunity[] = oppsData?.items || [];

  const { data: customersData } = useQuery({ queryKey: ['customers-options'], queryFn: () => getCustomers({ pageSize: 200 }) });
  const customers: Customer[] = customersData?.items || [];

  const { data: empData } = useQuery({ queryKey: ['employees-options'], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees: HREmployee[] = empData?.items || [];
  const empName = (id?: number) => employees.find((e) => e.id === id)?.full_name || (id ? `#${id}` : '-');

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['opportunities'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateOpportunity(editing.id, payload) : createOpportunity(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteOpportunity(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const moveMutation = useMutation({
    mutationFn: ({ id, stageId }: { id: number; stageId: number }) => moveOpportunity(id, stageId),
    onSuccess: () => invalidate(),
  });

  const closeMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) => closeOpportunity(closing!.id, payload),
    onSuccess: () => { invalidate(); setClosing(null); reset(); },
  });

  const openCreate = () => { setEditing(null); reset({ status: 'OPEN' }); setShowModal(true); };
  const openEdit = (item: Opportunity) => {
    setEditing(item);
    reset({
      name: item.name, customer_id: item.customerId, stage_id: item.stageId,
      source: item.source, expected_amount: item.expectedAmount,
      expected_close_date: item.expectedCloseDate, assigned_to: item.assignedTo,
      probability: item.probability, description: item.description,
    });
    setShowModal(true);
  };

  const byStage = (stageId: number) => opportunities.filter((o) => o.stageId === stageId);
  const stageOf = (o: Opportunity) => stages.find((s) => s.id === o.stageId);
  const moveTo = (o: Opportunity, stageId: number) => moveMutation.mutate({ id: o.id, stageId });

  const card = (o: Opportunity) => {
    const stage = stageOf(o);
    return (
      <div
        key={o.id}
        draggable
        onDragStart={() => setDragId(o.id)}
        onDragEnd={() => setDragId(null)}
        onClick={() => openEdit(o)}
        className="cursor-pointer rounded-xl border border-gray-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-3 shadow-sm hover:shadow-md transition-shadow space-y-2"
      >
        <div className="flex items-start justify-between gap-2">
          <p className="text-sm font-semibold text-gray-900 dark:text-zinc-100 leading-snug">{o.name}</p>
          <div className="flex gap-1 shrink-0">
            <button
              className="btn-ghost p-1"
              title="نقل للمرحلة السابقة"
              onClick={(e) => { e.stopPropagation(); const i = stages.findIndex((s) => s.id === o.stageId); if (i > 0) moveTo(o, stages[i - 1].id); }}
            ><IconChevronRight className="h-4 w-4" /></button>
            <button
              className="btn-ghost p-1"
              title="نقل للمرحلة التالية"
              onClick={(e) => { e.stopPropagation(); const i = stages.findIndex((s) => s.id === o.stageId); if (i >= 0 && i < stages.length - 1) moveTo(o, stages[i + 1].id); }}
            ><IconChevronLeft className="h-4 w-4" /></button>
            <button className="btn-ghost p-1 text-emerald-600" title="إغلاق كفوز" onClick={(e) => { e.stopPropagation(); setClosing(o); reset({ status: 'WON', won_amount: o.expectedAmount }); }}>
              <IconCheckCircle className="h-4 w-4" />
            </button>
            <button className="btn-ghost p-1 text-red-600" title="إغلاق كخسارة" onClick={(e) => { e.stopPropagation(); setClosing(o); reset({ status: 'LOST' }); }}>
              <IconXCircle className="h-4 w-4" />
            </button>
            <button className="btn-ghost p-1 text-red-600" title="حذف" onClick={(e) => { e.stopPropagation(); setDeleting(o); }}>
              <IconTrash className="h-4 w-4" />
            </button>
          </div>
        </div>
        {o.customerName && <p className="text-xs text-gray-500 dark:text-zinc-400">{o.customerName}</p>}
        <div className="flex items-center justify-between text-xs">
          <span className="font-bold text-gray-900 dark:text-zinc-100">{formatCurrency(o.expectedAmount)}</span>
          <span className="text-gray-400">{o.probability}%</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">{formatDate(o.expectedCloseDate)}</span>
          {o.status === 'WON' && <span className="badge-success">فوز</span>}
          {o.status === 'LOST' && <span className="badge-danger">خسارة</span>}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="فرص البيع"
        subtitle="إدارة خط أنابيب المبيعات والفرص"
        icon={<IconTarget className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}>
            <IconPlus className="h-4 w-4 ml-1 inline" /> فرصة جديدة
          </button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <input className="input w-64" placeholder="بحث في الفرص..." value={search} onChange={(e) => { setSearch(e.target.value); setStageFilter(''); }} />
        <select className="input w-44" value={stageFilter} onChange={(e) => setStageFilter(e.target.value)}>
          <option value="">كل المراحل</option>
          {stages.map((s) => <option key={s.id} value={s.id}>{s.nameAr || s.name}</option>)}
        </select>
      </div>

      {stageFilter ? (
        <div className="card p-5 space-y-2">
          {opportunities.length === 0 && <p className="text-gray-400 text-sm">لا توجد فرص في هذه المرحلة</p>}
          {opportunities.map((o) => card(o))}
        </div>
      ) : (
        <div className="grid gap-4 overflow-x-auto pb-2" style={{ gridTemplateColumns: `repeat(${stages.length}, minmax(260px, 1fr))` }}>
          {stages.map((s) => (
            <div
              key={s.id}
              onDragOver={(e) => e.preventDefault()}
              onDrop={() => { if (dragId != null) { moveTo({ id: dragId } as Opportunity, s.id); setDragId(null); } }}
              className="rounded-2xl bg-gray-50 dark:bg-zinc-800/60 p-3 min-h-[120px]"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className={cn('h-2.5 w-2.5 rounded-full', s.isWon ? 'bg-emerald-500' : s.isLost ? 'bg-red-500' : 'bg-primary-500')} />
                  <span className="text-sm font-bold text-gray-800 dark:text-zinc-200">{s.nameAr || s.name}</span>
                </div>
                <span className="text-xs text-gray-500 bg-white dark:bg-zinc-700 rounded-full px-2 py-0.5">{byStage(s.id).length}</span>
              </div>
              {s.probability != null && s.isWon === false && s.isLost === false && (
                <div className="mb-2 text-xs text-gray-400">{s.probability}% احتمالية</div>
              )}
              <div className="space-y-2">
                {byStage(s.id).map((o) => card(o))}
                {byStage(s.id).length === 0 && <p className="text-xs text-gray-400 text-center py-4">لا توجد فرص</p>}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create / Edit modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل فرصة' : 'فرصة جديدة'} size="lg">
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div><label className="label">اسم الفرصة *</label><input className="input" {...register('name', { required: true })} /></div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">العميل</label>
              <select className="input" {...register('customer_id')}>
                <option value="">بدون عميل</option>
                {customers.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div><label className="label">المرحلة</label>
              <select className="input" {...register('stage_id')}>
                {stages.map((s) => <option key={s.id} value={s.id}>{s.nameAr || s.name}</option>)}
              </select>
            </div>
            <div><label className="label">المصدر</label>
              <select className="input" {...register('source')}>
                <option value="manual">يدوي</option>
                <option value="lead">عميل محتمل</option>
                <option value="referral">إحالة</option>
                <option value="website">الموقع</option>
              </select>
            </div>
            <div><label className="label">المسؤول</label>
              <select className="input" {...register('assigned_to')}>
                <option value="">بدون</option>
                {employees.map((e) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
              </select>
            </div>
            <div><label className="label">القيمة المتوقعة</label><input className="input" type="number" step="0.01" {...register('expected_amount')} /></div>
            <div><label className="label">الاحتمالية %</label><input className="input" type="number" min="0" max="100" {...register('probability')} /></div>
            <div><label className="label">تاريخ الإغلاق المتوقع</label><input className="input" type="date" {...register('expected_close_date')} /></div>
          </div>
          <div><label className="label">الوصف</label><textarea className="input" rows={2} {...register('description')} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>

      {/* Close modal */}
      <Modal isOpen={!!closing} onClose={() => setClosing(null)} title={`إغلاق فرصة: ${closing?.name}`}>
        <form onSubmit={handleSubmit((d) => closeMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div><label className="label">الحالة</label>
              <select className="input" {...register('status')}><option value="WON">فوز</option><option value="LOST">خسارة</option></select>
            </div>
            <div><label className="label">قيمة الإغلاق</label><input className="input" type="number" step="0.01" {...register('won_amount')} /></div>
          </div>
          <div><label className="label">السبب / ملاحظات</label><textarea className="input" rows={2} {...register('won_lost_reason')} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setClosing(null)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={closeMutation.isPending}>{closeMutation.isPending ? 'جارٍ الحفظ...' : 'إغلاق'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف الفرصة"
        message="هل أنت متأكد من حذف هذه الفرصة؟"
        confirmText="حذف"
      />
    </div>
  );
}
