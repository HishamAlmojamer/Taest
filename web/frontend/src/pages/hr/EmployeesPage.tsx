import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getEmployees, createEmployee, getDepartments, getPositions } from '@/api/hr';
import { formatDate, formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';

interface EmployeeForm {
  fullName: string;
  fullNameEn: string;
  email: string;
  phone: string;
  mobile: string;
  gender: string;
  nationality: string;
  maritalStatus: string;
  departmentId: string;
  positionId: string;
  hireDate: string;
  basicSalary: number;
  housingAllowance: number;
  transportationAllowance: number;
  otherAllowances: number;
  totalSalary: number;
  bankName: string;
  bankAccount: string;
  iban: string;
}

export default function EmployeesPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);

  const { data, isLoading } = useQuery({
    queryKey: ['employees', page, search],
    queryFn: () => getEmployees({ page, pageSize: 10, search }),
  });

  const { data: departments } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const { data: positions } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions({}) });

  const { register, handleSubmit, reset, watch, setValue } = useForm<EmployeeForm>();

  const watchBasicSalary = watch('basicSalary', 0);
  const watchHousing = watch('housingAllowance', 0);
  const watchTransport = watch('transportationAllowance', 0);
  const watchOther = watch('otherAllowances', 0);
  const totalCalc = Number(watchBasicSalary || 0) + Number(watchHousing || 0) + Number(watchTransport || 0) + Number(watchOther || 0);

  const createMutation = useMutation({
    mutationFn: (formData: EmployeeForm) => {
      const code = `EMP-${Date.now()}`;
      return createEmployee({
        code,
        full_name: formData.fullName,
        full_name_en: formData.fullNameEn || undefined,
        email: formData.email || undefined,
        phone: formData.phone || undefined,
        mobile: formData.mobile || undefined,
        gender: formData.gender || 'ذكر',
        nationality: formData.nationality || undefined,
        marital_status: formData.maritalStatus || 'أعزب',
        department_id: formData.departmentId ? Number(formData.departmentId) : undefined,
        position_id: formData.positionId ? Number(formData.positionId) : undefined,
        hire_date: formData.hireDate || new Date().toISOString().split('T')[0],
        employment_status: 'نشط',
        salary_type: 'شهري',
        basic_salary: Number(formData.basicSalary || 0),
        housing_allowance: Number(formData.housingAllowance || 0),
        transportation_allowance: Number(formData.transportationAllowance || 0),
        other_allowances: Number(formData.otherAllowances || 0),
        total_salary: totalCalc,
        bank_name: formData.bankName || undefined,
        bank_account: formData.bankAccount || undefined,
        iban: formData.iban || undefined,
      } as any);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['employees'] });
      setShowModal(false);
      reset();
    },
  });

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-1 rounded">{String(item.code)}</span> },
    { key: 'fullName', header: 'الاسم', render: (item) => <button onClick={() => navigate(`/hr/employees/${item.id}`)} className="font-medium text-primary-600 hover:underline">{String(item.fullName)}</button> },
    { key: 'departmentId', header: 'القسم', render: (item) => {
      const dept = departments?.items?.find((d: any) => d.id === item.departmentId);
      return <span className="text-sm">{dept ? dept.name : '-'}</span>;
    }},
    { key: 'positionId', header: 'المنصب', render: (item) => {
      const pos = positions?.items?.find((p: any) => p.id === item.positionId);
      return <span className="text-sm">{pos ? pos.name : '-'}</span>;
    }},
    { key: 'hireDate', header: 'تاريخ التعيين', render: (item) => formatDate(String(item.hireDate)) },
    { key: 'employmentStatus', header: 'الحالة', render: (item) => <StatusBadge status={String(item.employmentStatus || 'نشط')} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="الموظفون"
        subtitle="إدارة بيانات الموظفين والمسميات الوظيفية والرواتب"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        }
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ موظف جديد</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالاسم أو رقم الموظف..." />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="موظف جديد" size="xl">
        <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="space-y-4">
          <h3 className="font-semibold text-gray-900 dark:text-zinc-100 border-b pb-2">المعلومات الشخصية</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">الاسم الكامل *</label><input {...register('fullName', { required: true })} className="input" placeholder="مثال: محمد أحمد علي" /></div>
            <div><label className="label">الاسم بالإنجليزية</label><input {...register('fullNameEn')} className="input" placeholder="Mohammed Ahmed" /></div>
            <div><label className="label">البريد الإلكتروني</label><input {...register('email')} type="email" className="input" placeholder="email@domain.com" /></div>
            <div><label className="label">رقم الجوال</label><input {...register('mobile')} className="input" placeholder="05xxxxxxxx" /></div>
            <div><label className="label">رقم الهاتف</label><input {...register('phone')} className="input" /></div>
            <div>
              <label className="label">الجنس</label>
              <select {...register('gender')} className="input" defaultValue="ذكر">
                <option value="ذكر">ذكر</option>
                <option value="أنثى">أنثى</option>
              </select>
            </div>
            <div><label className="label">الجنسية</label><input {...register('nationality')} className="input" placeholder="سعودي" /></div>
            <div>
              <label className="label">الحالة الاجتماعية</label>
              <select {...register('maritalStatus')} className="input" defaultValue="أعزب">
                <option value="أعزب">أعزب</option>
                <option value="متزوج">متزوج</option>
                <option value="مطلق">مطلق</option>
              </select>
            </div>
          </div>

          <h3 className="font-semibold text-gray-900 dark:text-zinc-100 border-b pb-2">الوظيفة</h3>
          <div className="grid grid-cols-2 gap-4">
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
          </div>

          <h3 className="font-semibold text-gray-900 dark:text-zinc-100 border-b pb-2">الراتب</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">الراتب الأساسي</label><input {...register('basicSalary', { valueAsNumber: true })} type="number" className="input" /></div>
            <div><label className="label">بدل السكن</label><input {...register('housingAllowance', { valueAsNumber: true })} type="number" className="input" /></div>
            <div><label className="label">بدل النقل</label><input {...register('transportationAllowance', { valueAsNumber: true })} type="number" className="input" /></div>
            <div><label className="label">بدلات أخرى</label><input {...register('otherAllowances', { valueAsNumber: true })} type="number" className="input" /></div>
            <div className="col-span-2">
              <div className="bg-primary-50 dark:bg-primary-500/10 p-3 rounded-lg text-center">
                <span className="text-sm text-gray-500 dark:text-zinc-400">الإجمالي: </span>
                <span className="text-lg font-bold text-primary-600">{formatCurrency(totalCalc)}</span>
              </div>
            </div>
          </div>

          <h3 className="font-semibold text-gray-900 dark:text-zinc-100 border-b pb-2">معلومات البنك</h3>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">اسم البنك</label><input {...register('bankName')} className="input" /></div>
            <div><label className="label">رقم الحساب</label><input {...register('bankAccount')} className="input" /></div>
            <div><label className="label">IBAN</label><input {...register('iban')} className="input" placeholder="SA00xxxxxxxx" /></div>
          </div>

          <div className="flex justify-end gap-2 pt-3 border-t">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
