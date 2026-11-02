import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatsCard } from '@/components/ui/StatsCard';
import { getHRReportSummary } from '@/api/hr';
import { formatCurrency } from '@/lib/utils';
import { IconLayoutDashboard, IconUsers, IconBuilding, IconCalendarClock, IconZap, IconXCircle, IconTarget, IconLayers, IconCreditCard, IconTrendingUp, IconPieChart } from '@/components/ui/Icons';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, PieChart as RCPieChart, Pie, Legend } from 'recharts';

const COLORS = ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444', '#06b6d4', '#f97316'];

export default function HRDashboardPage() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);

  const { data, isLoading } = useQuery({
    queryKey: ['hr-report-summary', year],
    queryFn: () => getHRReportSummary({ year }),
  });

  const byDept = data?.employeesByDepartment || [];
  const byGender = data?.employeesByGender || [];
  const genderData = data?.genderDistribution || data?.employeesByGender.map((g) => ({ label: g.gender, value: g.count })) || [];
  const leaveSummary = data?.leaveSummary || [];

  return (
    <div className="space-y-6">
      <PageHeader title="لوحة الموارد البشرية" subtitle="نظرة شاملة على الموظفين والإجازات والرواتب" icon={<IconLayoutDashboard className="h-6 w-6" />} />

      <div className="flex items-center justify-end">
        <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm w-32">
          {[currentYear - 1, currentYear, currentYear + 1].map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
      </div>

      {isLoading ? (
        <div className="p-8 text-center text-gray-500">جارٍ التحميل...</div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard title="الموظفون النشطون" value={data?.activeEmployees ?? 0} icon={<IconUsers className="h-6 w-6" />} color="green" footer={<span className="text-xs text-gray-400">من أصل {data?.totalEmployees ?? 0} موظف · {data?.departments ?? 0} قسم</span>} />
            <StatsCard title="طلبات إجازة معلقة" value={data?.pendingLeaves ?? 0} icon={<IconCalendarClock className="h-6 w-6" />} color="blue" footer={<span className="text-xs text-gray-400">بانتظار الموافقة</span>} />
            <StatsCard title="إضافي معلق" value={data?.pendingOvertime ?? 0} icon={<IconZap className="h-6 w-6" />} color="yellow" footer={<span className="text-xs text-gray-400">سجلات بانتظار الاعتماد</span>} />
            <StatsCard title="استقالات معلقة" value={data?.pendingResignations ?? 0} icon={<IconXCircle className="h-6 w-6" />} color="red" footer={<span className="text-xs text-gray-400">بانتظار الاعتماد</span>} />
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard title="وظائف شاغرة" value={data?.openJobs ?? 0} icon={<IconTarget className="h-6 w-6" />} color="purple" footer={<span className="text-xs text-gray-400">معلن عنها</span>} />
            <StatsCard title="متقدمون جدد" value={data?.newCandidates ?? 0} icon={<IconUsers className="h-6 w-6" />} color="blue" footer={<span className="text-xs text-gray-400">{data?.openCandidates ?? 0} قيد التقييم</span>} />
            <StatsCard title="برامج تدريبية مخطط لها" value={data?.trainingPlanned ?? 0} icon={<IconLayers className="h-6 w-6" />} color="purple" footer={<span className="text-xs text-gray-400">برنامج</span>} />
            <StatsCard title="مسودة رواتب" value={data?.draftPayroll ?? 0} icon={<IconCreditCard className="h-6 w-6" />} color="red" footer={<span className="text-xs text-gray-400">إجمالي {formatCurrency(data?.payrollPaidTotal ?? 0)} مدفوع</span>} />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="card p-5 lg:col-span-2">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconBuilding className="h-4 w-4 text-primary-500" /> توزيع الموظفين حسب القسم</h3>
              {byDept.length === 0 ? (
                <p className="text-sm text-gray-400">لا توجد بيانات</p>
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={byDept} margin={{ left: 10, right: 10 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
                    <XAxis dataKey="department" fontSize={12} />
                    <YAxis allowDecimals={false} fontSize={12} />
                    <Tooltip cursor={{ fill: 'rgba(0,0,0,0.04)' }} />
                    <Bar dataKey="count" radius={[6, 6, 0, 0]} barSize={40}>
                      {byDept.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>

            <div className="card p-5">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconPieChart className="h-4 w-4 text-sky-500" /> توزيع الموظفين حسب الجنس</h3>
              {genderData.length === 0 ? (
                <p className="text-sm text-gray-400">لا توجد بيانات</p>
              ) : (
                <ResponsiveContainer width="100%" height={220}>
                  <RCPieChart>
                    <Pie data={genderData} dataKey="value" nameKey="label" innerRadius={45} outerRadius={80} paddingAngle={3}>
                      {genderData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend fontSize={11} />
                  </RCPieChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>

          <div className="card p-5">
            <h3 className="font-bold mb-4 flex items-center gap-2"><IconTrendingUp className="h-4 w-4 text-emerald-500" /> أيام الإجازات حسب النوع</h3>
            {leaveSummary.length === 0 ? (
              <p className="text-sm text-gray-400">لا توجد بيانات</p>
            ) : (
              <div className="space-y-3">
                {leaveSummary.map((l) => (
                  <div key={l.leaveType} className="flex items-center gap-3">
                    <div className="w-40 shrink-0 text-sm text-gray-600 dark:text-zinc-300">{l.leaveType}</div>
                    <div className="flex-1 h-6 bg-gray-100 dark:bg-zinc-800 rounded-lg overflow-hidden">
                      <div className="h-full bg-gradient-to-l from-emerald-500 to-teal-500 rounded-lg" style={{ width: `${Math.max(4, (l.days / Math.max(...leaveSummary.map((x) => x.days), 1)) * 100)}%` }} />
                    </div>
                    <div className="w-40 shrink-0 text-xs text-gray-500 text-left" dir="ltr">{l.days} يوم · {l.count} طلب</div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
