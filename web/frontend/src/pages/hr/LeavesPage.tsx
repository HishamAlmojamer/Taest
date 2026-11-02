import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getLeaves, createLeave, approveLeave, rejectLeave, getEmployees } from '@/api/hr';
import { formatNumber } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';

interface LeaveForm {
  employeeId: string;
  type: string;
  startDate: string;
  endDate: string;
  reason: string;
}

const leaveTypes: Record<string, string> = { ANNUAL: 'سنوية', SICK: 'مرضية', PERSONAL: 'شخصية', MATERNITY: 'أمومة', PATERNITY: 'أبوبة', UNPAID: 'بدون راتب' };

export default function LeavesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['leaves', page],
    queryFn: () => getLeaves({ page, pageSize: 10 }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const approveMutation = useMutation({
    mutationFn: approveLeave,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leaves'] }),
  });

  const rejectMutation = useMutation({
    mutationFn: rejectLeave,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['leaves'] }),
  });

  const { register, handleSubmit, reset, watch } = useForm<LeaveForm>();

  const startDate = watch('startDate');
  const endDate = watch('endDate');
  const selectedEmpId = watch('employeeId');

  const createMutation = useMutation({
    mutationFn: (formData: LeaveForm) => {
      const start = String(formData.startDate || '');
      const end = String(formData.endDate || '');
      let daysCount = 1;
      if (start && end) {
        const diff = new Date(end).getTime() - new Date(start).getTime();
        daysCount = Math.max(1, Math.ceil(diff / (1000 * 60 * 60 * 24)) + 1);
      }
      return createLeave({
        employee_id: Number(formData.employeeId),
        leave_type: formData.type || 'ANNUAL',
        start_date: formData.startDate,
        end_date: formData.endDate,
        days_count: daysCount,
        reason: formData.reason,
        status: 'pending',
      } as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['leaves'] });
      setShowModal(false);
      reset();
    },
  });

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId);
    return emp ? emp.full_name : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeId', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'leaveType', header: 'النوع', render: (item) => leaveTypes[String(item.leaveType || item.type)] || String(item.leaveType || item.type) },
    { key: 'startDate', header: 'من', render: (item) => String(item.startDate) },
    { key: 'endDate', header: 'إلى', render: (item) => String(item.endDate) },
    { key: 'daysCount', header: 'الأيام', render: (item) => formatNumber(Number(item.daysCount || item.days || 0)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => item.status === 'pending' ? (
      <div className="flex gap-1">
        <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد من اعتماد هذا الطلب؟')) { approveMutation.mutate(Number(item.id)); } }} className="text-green-600 hover:text-green-700 text-xs font-medium">اعتماد</button>
        <button onClick={(e) => { e.stopPropagation(); if (confirm('هل أنت متأكد من رفض هذا الطلب؟')) { rejectMutation.mutate(Number(item.id)); } }} className="text-red-600 hover:text-red-700 text-xs font-medium">رفض</button>
      </div>
    ) : null },
  ];

return (
    <div className="space-y-6">
      <PageHeader
        title="الإجازات"
        subtitle="إدارة طلبات إجازات الموظفين واعتمادها أو رفضها"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        }
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ طلب إجازة</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث في الإجازات..." keepPreviousData />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="طلب إجازة جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div>
            <label className="label">الموظف</label>
            <select {...register('employeeId', { required: true })} className="input">
              <option value="">اختر الموظف</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{e.full_name} ({e.code})</option>)}
            </select>
          </div>
          <div>
            <label className="label">نوع الإجازة</label>
            <select {...register('type', { required: true })} className="input">
              {Object.entries(leaveTypes).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">من تاريخ</label><input {...register('startDate', { required: true })} type="date" className="input" /></div>
            <div><label className="label">إلى تاريخ</label><input {...register('endDate', { required: true })} type="date" className="input" /></div>
          </div>
          {startDate && endDate && (
            <div className="bg-gray-50 dark:bg-zinc-800 p-3 rounded-lg text-center text-sm">
              <span className="text-gray-500 dark:text-zinc-400">عدد الأيام: </span>
              <span className="font-bold text-primary-600">
                {Math.max(1, Math.ceil((new Date(endDate).getTime() - new Date(startDate).getTime()) / (1000 * 60 * 60 * 24)) + 1)}
              </span>
            </div>
          )}
          <div><label className="label">السبب</label><textarea {...register('reason', { required: true })} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'جاري الإرسال...' : 'إرسال'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
