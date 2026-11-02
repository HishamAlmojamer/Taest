import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getEmployee, getPayroll, getAttendance, getLeaves, getDepartments, getPositions } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

export default function EmployeeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const empId = Number(id);
  const toast = useToast();

  const { data: emp, isLoading } = useQuery({
    queryKey: ['employee', empId],
    queryFn: () => getEmployee(empId),
    enabled: !!empId,
  });

  const { data: deptData } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const { data: posData } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions({}) });
  const departments = deptData?.items || [];
  const positions = posData?.items || [];
  const departmentName = departments.find((d: any) => d.id === emp?.department_id)?.name || emp?.departmentName || '-';
  const positionName = positions.find((p: any) => p.id === emp?.position_id)?.name || emp?.positionName || '-';

  const { data: payrollData } = useQuery({
    queryKey: ['payroll', { employee_id: empId }],
    queryFn: () => getPayroll({ employee_id: empId, pageSize: 10 }),
    enabled: !!empId,
  });

  const { data: attendanceData } = useQuery({
    queryKey: ['attendance', { employee_id: empId }],
    queryFn: () => getAttendance({ employee_id: empId, pageSize: 10 }),
    enabled: !!empId,
  });

  const { data: leavesData } = useQuery({
    queryKey: ['leaves', { employee_id: empId }],
    queryFn: () => getLeaves({ employee_id: empId, pageSize: 10 }),
    enabled: !!empId,
  });

  if (isLoading) return <LoadingSpinner />;
  if (!emp) return <div className="card p-8 text-center">الموظف غير موجود</div>;

  const InfoCard = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div className="card p-5">
      <h3 className="font-bold text-gray-900 dark:text-zinc-100 mb-3 pb-2 border-b border-gray-100 dark:border-zinc-700">{title}</h3>
      <div className="grid grid-cols-2 gap-3 text-sm">{children}</div>
    </div>
  );

  const Field = ({ label, value }: { label: string; value?: string | number | null }) => (
    <div>
      <span className="text-gray-500 dark:text-zinc-400">{label}</span>
      <p className="text-gray-900 dark:text-zinc-100 font-medium">{value || '-'}</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button onClick={() => navigate(-1)} className="text-gray-400 hover:text-gray-600 dark:hover:text-zinc-300">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
          </button>
          <PageHeader
            title={emp.full_name || 'تفاصيل الموظف'}
            subtitle={`${emp.code || ''} ${emp.full_name_en || ''}`}
            icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
            actions={<div className="flex items-center gap-2">
              <StatusBadge status={emp.is_active ? 'نشط' : 'غير نشط'} />
              <button onClick={() => navigate(`/hr/employees`)} className="btn-secondary text-sm px-3 py-1">تعديل</button>
            </div>}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <InfoCard title="المعلومات الشخصية">
          <Field label="الاسم الكامل" value={emp.full_name} />
          <Field label="الاسم بالإنجليزية" value={emp.full_name_en} />
          <Field label="البريد الإلكتروني" value={emp.email} />
          <Field label="الهاتف" value={emp.phone} />
          <Field label="الجوال" value={emp.mobile} />
          <Field label="الجنس" value={emp.gender} />
          <Field label="تاريخ الميلاد" value={emp.birth_date ? formatDate(emp.birth_date) : null} />
          <Field label="الجنسية" value={emp.nationality} />
          <Field label="الحالة الاجتماعية" value={emp.marital_status} />
          <Field label="العنوان" value={emp.address} />
        </InfoCard>

        <InfoCard title="الوظيفة">
          <Field label="القسم" value={<button onClick={() => navigate('/hr/departments')} className="text-primary-600 hover:underline">{departmentName}</button> as any} />
          <Field label="المنصب" value={positionName} />
          <Field label="تاريخ التعيين" value={emp.hire_date ? formatDate(emp.hire_date) : null} />
          <Field label="حالة التوظيف" value={emp.employment_status} />
          <Field label="نوع الراتب" value={emp.salary_type} />
        </InfoCard>

        <InfoCard title="الراتب">
          <Field label="الراتب الأساسي" value={formatCurrency(emp.basic_salary || 0)} />
          <Field label="بدل السكن" value={formatCurrency(emp.housing_allowance || 0)} />
          <Field label="بدل النقل" value={formatCurrency(emp.transportation_allowance || 0)} />
          <Field label="بدلات أخرى" value={formatCurrency(emp.other_allowances || 0)} />
          <Field label="الإجمالي" value={<span className="text-primary-600 font-bold">{formatCurrency(emp.total_salary || 0)}</span> as any} />
        </InfoCard>

        <InfoCard title="البنك">
          <Field label="اسم البنك" value={emp.bank_name} />
          <Field label="رقم الحساب" value={emp.bank_account} />
          <Field label="IBAN" value={emp.iban} />
        </InfoCard>

        <InfoCard title="الوثائق">
          <Field label="نوع الهوية" value={emp.id_type} />
          <Field label="رقم الهوية" value={emp.id_number} />
          <Field label="انتهاء صلاحية الهوية" value={emp.id_expiry ? formatDate(emp.id_expiry) : null} />
          <Field label="رقم جواز السفر" value={emp.passport_number} />
          <Field label="انتهاء صلاحية الجواز" value={emp.passport_expiry ? formatDate(emp.passport_expiry) : null} />
        </InfoCard>

        <InfoCard title="جهة الاتصال في الطوارئ">
          <Field label="الاسم" value={emp.emergency_contact_name} />
          <Field label="الهاتف" value={emp.emergency_contact_phone} />
        </InfoCard>

        <InfoCard title="التأمين">
          <Field label="مزود التأمين" value={emp.health_insurance_provider} />
          <Field label="رقم التأمين" value={emp.health_insurance_number} />
        </InfoCard>
      </div>

      {/* Activity */}
      <div className="card p-5">
        <h3 className="font-bold text-gray-900 dark:text-zinc-100 mb-3 pb-2 border-b border-gray-100 dark:border-zinc-700">السجل</h3>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mb-2">آخر الحضور</p>
            {attendanceData && attendanceData.items.length > 0 ? (
              <div className="space-y-1 text-sm">
                {attendanceData.items.slice(0, 5).map((a: any) => (
                  <div key={a.id} className="flex justify-between">
                    <span>{formatDate(a.date)}</span>
                    <StatusBadge status={a.status} />
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-400">لا توجد سجلات</p>}
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mb-2">الإجازات</p>
            {leavesData?.items && leavesData.items.length > 0 ? (
              <div className="space-y-1 text-sm">
                {leavesData.items.slice(0, 5).map((l: any) => (
                  <div key={l.id} className="flex justify-between">
                    <span>{l.leave_type}</span>
                    <StatusBadge status={l.status} />
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-400">لا توجد إجازات</p>}
          </div>
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400 mb-2">الرواتب</p>
            {payrollData?.items && payrollData.items.length > 0 ? (
              <div className="space-y-1 text-sm">
                {payrollData.items.slice(0, 5).map((p: any) => (
                  <div key={p.id} className="flex justify-between">
                    <span>{p.periodFrom}</span>
                    <span className="font-bold">{formatCurrency(p.netSalary)}</span>
                  </div>
                ))}
              </div>
            ) : <p className="text-sm text-gray-400">لا توجد رواتب</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
