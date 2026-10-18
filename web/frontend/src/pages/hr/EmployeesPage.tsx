import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getEmployees, createEmployee, getDepartments, getPositions } from '@/api/hr';
import { formatDate } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';

export default function EmployeesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['employees', page, search],
    queryFn: () => getEmployees({ page, pageSize: 10, search }),
  });

  const { data: departments } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const { data: positions } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions({}) });

  const { register, handleSubmit, reset } = useForm();

  const createMutation = useMutation({
    mutationFn: (formData: Record<string, unknown>) => {
      const firstName = String(formData.firstName || '');
      const lastName = String(formData.lastName || '');
      return createEmployee({
        code: `EMP-${Date.now()}`,
        fullName: `${firstName} ${lastName}`.trim(),
        email: formData.email,
        phone: formData.phone,
        departmentId: formData.departmentId ? Number(formData.departmentId) : undefined,
        positionId: formData.positionId ? Number(formData.positionId) : undefined,
        hireDate: formData.hireDate || new Date().toISOString().split('T')[0],
        gender: formData.gender || 'ذكر',
        employmentStatus: 'نشط',
        salaryType: 'شهري',
        basicSalary: formData.salary ? Number(formData.salary) : 0,
        totalSalary: formData.salary ? Number(formData.salary) : 0,
      } as never);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setShowModal(false);
      reset();
    },
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'رقم الموظف', render: (item) => <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">{String(item.code)}</span> },
    { key: 'fullName', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.fullName)}</span> },
    { key: 'departmentId', header: 'القسم', render: (item) => {
      const dept = departments?.items?.find((d: any) => d.id === item.departmentId);
      return dept ? dept.name : '-';
    }},
    { key: 'positionId', header: 'المنصب', render: (item) => {
      const pos = positions?.items?.find((p: any) => p.id === item.positionId);
      return pos ? pos.name : '-';
    }},
    { key: 'hireDate', header: 'تاريخ التعيين', render: (item) => formatDate(String(item.hireDate)) },
    { key: 'employmentStatus', header: 'الحالة', render: (item) => <StatusBadge status={String(item.employmentStatus || 'نشط')} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الموظفون</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ موظف جديد</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالاسم أو رقم الموظف..." />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="موظف جديد" size="lg">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">الاسم الأول</label><input {...register('firstName', { required: true })} className="input" /></div>
            <div><label className="label">اسم العائلة</label><input {...register('lastName', { required: true })} className="input" /></div>
            <div><label className="label">البريد الإلكتروني</label><input {...register('email', { required: true })} type="email" className="input" /></div>
            <div><label className="label">الهاتف</label><input {...register('phone')} className="input" /></div>
            <div>
              <label className="label">القسم</label>
              <select {...register('departmentId')} className="input">
                <option value="">اختر القسم</option>
                {departments?.items?.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">المنصب</label>
              <select {...register('positionId')} className="input">
                <option value="">اختر المنصب</option>
                {positions?.items?.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
            <div><label className="label">تاريخ التعيين</label><input {...register('hireDate')} type="date" className="input" defaultValue={new Date().toISOString().split('T')[0]} /></div>
            <div><label className="label">الراتب الأساسي</label><input {...register('salary', { valueAsNumber: true })} type="number" className="input" /></div>
            <div>
              <label className="label">الجنس</label>
              <select {...register('gender')} className="input" defaultValue="ذكر">
                <option value="ذكر">ذكر</option>
                <option value="أنثى">أنثى</option>
              </select>
            </div>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
