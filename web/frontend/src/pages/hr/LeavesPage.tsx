import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getLeaves, createLeave, approveLeave, rejectLeave } from '@/api/hr';
import { formatNumber } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';

export default function LeavesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['leaves', page],
    queryFn: () => getLeaves({ page, pageSize: 10 }),
  });

  const approveMutation = useMutation({
    mutationFn: approveLeave,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leaves'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: rejectLeave,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leaves'] }),
  });

  const { register, handleSubmit, reset, watch } = useForm();

  const startDate = watch('startDate');
  const endDate = watch('endDate');

  const createMutation = useMutation({
    mutationFn: (formData: Record<string, unknown>) => {
      const start = String(formData.startDate || '');
      const end = String(formData.endDate || '');
      let daysCount = 1;
      if (start && end) {
        const diff = new Date(end).getTime() - new Date(start).getTime();
        daysCount = Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
      }
      return createLeave({
        employeeId: Number(formData.employeeId),
        leaveType: formData.type || 'ANNUAL',
        startDate: formData.startDate,
        endDate: formData.endDate,
        daysCount,
        reason: formData.reason,
        status: 'pending',
      } as never);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leaves'] });
      setShowModal(false);
      reset();
    },
  });

  const leaveTypes: Record<string, string> = { ANNUAL: 'سنوية', SICK: 'مرضية', PERSONAL: 'شخصية', MATERNITY: 'أمومة', PATERNITY: 'أبوبة', UNPAID: 'بدون راتب' };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeId', header: 'الموظف', render: (item) => <span className="font-medium">موظف #{String(item.employeeId)}</span> },
    { key: 'leaveType', header: 'النوع', render: (item) => leaveTypes[String(item.leaveType || item.type)] || String(item.leaveType || item.type) },
    { key: 'startDate', header: 'من', render: (item) => String(item.startDate) },
    { key: 'endDate', header: 'إلى', render: (item) => String(item.endDate) },
    { key: 'daysCount', header: 'الأيام', render: (item) => formatNumber(Number(item.daysCount || item.days || 0)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => item.status === 'pending' ? (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد من اعتماد هذا الطلب؟')) { approveMutation.mutate(String(item.id)); } }} className="text-green-600 hover:text-green-700 text-xs">اعتماد</button>
        <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد من رفض هذا الطلب؟')) { rejectMutation.mutate(String(item.id)); } }} className="text-red-600 hover:text-red-700 text-xs">رفض</button>
      </div>
    ) : null },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الإجازات</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ طلب إجازة</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="طلب إجازة جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div><label className="label">رقم الموظف</label><input {...register('employeeId', { required: true })} type="number" className="input" /></div>
          <div>
            <label className="label">نوع الإجازة</label>
            <select {...register('type', { required: true })} className="input">
              {Object.entries(leaveTypes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div><label className="label">من تاريخ</label><input {...register('startDate', { required: true })} type="date" className="input" /></div>
          <div><label className="label">إلى تاريخ</label><input {...register('endDate', { required: true })} type="date" className="input" /></div>
          {startDate && endDate && (
            <div className="text-sm text-gray-500 dark:text-zinc-400">
              عدد الأيام: {Math.max(1, Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)) + 1)}
            </div>
          )}
          <div><label className="label">السبب</label><textarea {...register('reason', { required: true })} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">إرسال</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
