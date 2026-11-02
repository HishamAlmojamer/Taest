import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getAttendance, createAttendance, updateAttendance, deleteAttendance, getEmployees } from '@/api/hr';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { useForm } from 'react-hook-form';

interface AttForm { employee_id: number; date: string; check_in: string; check_out: string; status: string; notes: string; }

export default function AttendancePage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deleteId, setDeleteId] = useState<number | null>(null);
  const [dateFilter, setDateFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['attendance', page, search, dateFilter, statusFilter],
    queryFn: () => getAttendance({ page, pageSize: 10, search, date: dateFilter || undefined, status: statusFilter || undefined }),
  });
  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const { register, handleSubmit, reset, setValue } = useForm<AttForm>();

  const attendanceData = data?.items || [];
  const employees = empData?.items || [];

  const createMutation = useMutation({
    mutationFn: createAttendance,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['attendance'] }); setShowModal(false); reset(); },
  });
  const updateMutation = useMutation({
    mutationFn: (d: { id: number; data: Partial<AttForm> }) => updateAttendance(d.id, d.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['attendance'] }); setShowModal(false); setEditingId(null); reset(); },
  });
  const deleteMutation = useMutation({
    mutationFn: deleteAttendance,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['attendance'] }); setDeleteId(null); },
  });

  const openAdd = () => {
    setEditingId(null);
    reset({ employee_id: 0, date: new Date().toISOString().split('T')[0], check_in: '', check_out: '', status: 'حاضر', notes: '' });
    setShowModal(true);
  };
  const openEdit = (item: any) => {
    setEditingId(item.id);
    reset({ employee_id: item.employee_id, date: item.date, check_in: item.check_in || '', check_out: item.check_out || '', status: item.status || 'حاضر', notes: item.notes || '' });
    setShowModal(true);
  };
  const onSubmit = (d: AttForm) => {
    if (editingId) updateMutation.mutate({ id: editingId, data: d });
    else createMutation.mutate(d);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employee_id', header: 'الموظف', render: (item) => {
      const emp = employees.find((e: any) => e.id === item.employee_id);
      return <span className="font-medium">{emp ? emp.full_name : `#${item.employee_id}`}</span>;
    }},
    { key: 'date', header: 'التاريخ', render: (item) => String(item.date || '-') },
    { key: 'check_in', header: 'الحضور', render: (item) => String(item.check_in || '-') },
    { key: 'check_out', header: 'الانصراف', render: (item) => String(item.check_out || '-') },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'notes', header: 'ملاحظات', render: (item) => String(item.notes || '-') },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-2">
        <button onClick={() => openEdit(item)} className="text-primary-600 hover:text-primary-700 text-xs">تعديل</button>
        <button onClick={() => setDeleteId(Number(item.id))} className="text-red-600 hover:text-red-700 text-xs">حذف</button>
      </div>
    )},
  ];

  return (
<div className="space-y-6">
      <PageHeader
        title="الحضور والغياب"
        subtitle="سجّل دوام الموظفين وتتبّع الحضور والانصراف والغياب"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        }
        actions={<button onClick={openAdd} className="btn-primary">+ تسجيل حضور</button>}
      />
      <div className="flex gap-2 items-center">
        <input type="date" value={dateFilter} onChange={(e) => setDateFilter(e.target.value)} className="input text-sm w-40" placeholder="التاريخ" />
        <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input text-sm w-32">
          <option value="">كل الحالات</option>
          <option value="حاضر">حاضر</option>
          <option value="غائب">غائب</option>
          <option value="متأخر">متأخر</option>
          <option value="إجازة">إجازة</option>
        </select>
        {(dateFilter || statusFilter) && (
          <button onClick={() => { setDateFilter(''); setStatusFilter(''); }} className="text-xs text-primary-600 hover:underline">مسح الفلتر</button>
        )}
      </div>
      <DataTable columns={columns} data={attendanceData as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث..." keepPreviousData />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditingId(null); reset(); }} title={editingId ? 'تعديل الحضور' : 'تسجيل حضور'} size="sm">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div><label className="label">الموظف</label>
            <select {...register('employee_id', { required: true, valueAsNumber: true })} className="input">
              <option value="">اختر الموظف</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </select>
          </div>
          <div><label className="label">التاريخ</label><input type="date" {...register('date', { required: true })} className="input" /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">وقت الحضور</label><input type="time" {...register('check_in')} className="input" /></div>
            <div><label className="label">وقت الانصراف</label><input type="time" {...register('check_out')} className="input" /></div>
          </div>
          <div><label className="label">الحالة</label>
            <select {...register('status')} className="input">
              <option value="حاضر">حاضر</option>
              <option value="غائب">غائب</option>
              <option value="متأخر">متأخر</option>
              <option value="إجازة">إجازة</option>
            </select>
          </div>
          <div><label className="label">ملاحظات</label><textarea {...register('notes')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); setEditingId(null); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || updateMutation.isPending}>حفظ</button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog isOpen={deleteId !== null} onClose={() => setDeleteId(null)} onConfirm={() => { if (deleteId) deleteMutation.mutate(deleteId); }} title="حذف سجل الحضور" message="هل أنت متأكد من حذف هذا السجل؟" />
    </div>
  );
}
