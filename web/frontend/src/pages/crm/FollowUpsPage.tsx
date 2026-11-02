import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { useForm } from 'react-hook-form';
import { getFollowups, createFollowup, updateFollowup, completeFollowup, deleteFollowup, type FollowUp } from '@/api/crm';
import { getEmployees } from '@/api/hr';
import { formatDateTime } from '@/lib/utils';
import { cn } from '@/lib/utils';
import { IconCalendarClock, IconPlus, IconRefresh } from '@/components/ui/Icons';
import type { HREmployee } from '@/types';

export default function FollowUpsPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<FollowUp | null>(null);
  const [deleting, setDeleting] = useState<FollowUp | null>(null);
  const [statusFilter, setStatusFilter] = useState('OPEN');
  const [overdueOnly, setOverdueOnly] = useState(false);
  const [typeFilter, setTypeFilter] = useState('');

  const { register, handleSubmit, reset } = useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['followups', statusFilter, overdueOnly, typeFilter],
    queryFn: () => getFollowups({ status: statusFilter || undefined, overdue: overdueOnly || undefined, type: typeFilter || undefined }),
  });
  const followups: FollowUp[] = data?.items || [];

  const { data: empData } = useQuery({ queryKey: ['employees-options'], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees: HREmployee[] = empData?.items || [];
  const empName = (id?: number) => employees.find((e) => e.id === id)?.full_name || (id ? `#${id}` : '-');

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['followups'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, unknown>) =>
      editing ? updateFollowup(editing.id, payload) : createFollowup(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const completeMutation = useMutation({
    mutationFn: (id: number) => completeFollowup(id),
    onSuccess: () => invalidate(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteFollowup(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const openCreate = () => { setEditing(null); reset({ status: 'OPEN', priority: 'medium', type: 'call' }); setShowModal(true); };
  const openEdit = (item: FollowUp) => {
    setEditing(item);
    reset({
      subject: item.subject, type: item.type, priority: item.priority,
      due_date: item.dueDate, assigned_to: item.assignedTo,
      description: item.description, status: item.status,
    });
    setShowModal(true);
  };

  const isOverdue = (f: FollowUp) => f.status === 'OPEN' && !!f.dueDate && new Date(f.dueDate) < new Date();

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'subject', header: 'الموضوع', render: (item) => (
      <div>
        <p className="font-medium">{String(item.subject || item.type || '-')}</p>
        {!!item.entityName && <p className="text-xs text-gray-400">{String(item.entityName)}</p>}
      </div>
    )},
    { key: 'type', header: 'النوع', render: (item) => String(item.type || '-') },
    { key: 'dueDate', header: 'الموعد', render: (item) => {
      const overdue = isOverdue(item as unknown as FollowUp);
      return <span className={cn(overdue && 'text-red-600 font-semibold')}>{formatDateTime(String(item.dueDate))}{overdue && ' (متأخرة)'}</span>;
    }},
    { key: 'priority', header: 'الأولوية', render: (item) => <StatusBadge status={String(item.priority).toUpperCase()} /> },
    { key: 'assignedTo', header: 'المسؤول', render: (item) => empName(Number(item.assignedTo)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        {item.status === 'OPEN' && (
          <button className="btn-ghost px-2 py-1 text-xs text-emerald-600" onClick={() => completeMutation.mutate(Number(item.id))}>إتمام</button>
        )}
        <button className="btn-ghost px-2 py-1 text-xs" onClick={() => openEdit(item as unknown as FollowUp)}>تعديل</button>
        <button className="btn-ghost px-2 py-1 text-xs text-red-600" onClick={() => setDeleting(item as unknown as FollowUp)}>حذف</button>
      </div>
    )},
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="المتابعات"
        subtitle="إدارة المهام والمتابعات والاتصالات"
        icon={<IconCalendarClock className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}>
            <IconPlus className="h-4 w-4 ml-1 inline" /> متابعة جديدة
          </button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        <select className="input w-36" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
          <option value="">كل الحالات</option>
          <option value="OPEN">مفتوحة</option>
          <option value="DONE">منجزة</option>
          <option value="CANCELLED">ملغاة</option>
        </select>
        <select className="input w-36" value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)}>
          <option value="">كل الأنواع</option>
          <option value="call">اتصال</option>
          <option value="email">بريد</option>
          <option value="meeting">اجتماع</option>
          <option value="task">مهمة</option>
          <option value="whatsapp">واتساب</option>
        </select>
        <label className="flex items-center gap-2 text-sm text-gray-600 dark:text-zinc-300">
          <input type="checkbox" className="h-4 w-4" checked={overdueOnly} onChange={(e) => setOverdueOnly(e.target.checked)} />
          المتأخرة فقط
        </label>
        {isLoading && <IconRefresh className="h-4 w-4 animate-spin text-gray-400" />}
      </div>

      {followups.length === 0 && !isLoading ? (
        <EmptyState title="لا توجد متابعات" description="أضف متابعة جديدة لمتابعة أعمالك" />
      ) : (
        <DataTable
          columns={columns}
          data={(followups as unknown) as Record<string, unknown>[]}
          loading={isLoading}
          emptyTitle="لا توجد متابعات"
          onRowClick={(item) => openEdit(item as unknown as FollowUp)}
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل متابعة' : 'متابعة جديدة'}>
        <form onSubmit={handleSubmit((d) => saveMutation.mutate(d as Record<string, unknown>))} className="space-y-4">
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
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف المتابعة"
        message="هل أنت متأكد من حذف هذه المتابعة؟"
        confirmText="حذف"
      />
    </div>
  );
}
