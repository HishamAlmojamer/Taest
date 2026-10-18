import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { StatsCard } from '@/components/ui/StatsCard';
import { getDailyReport, type DailyReportData } from '@/api/sales';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function DashboardPage() {
  const today = new Date().toISOString().split('T')[0];

  const { data: dailyReport, isLoading } = useQuery({
    queryKey: ['dashboard', 'daily', today],
    queryFn: () => getDailyReport(today),
  });

  const stats = useMemo(
    () => [
      {
        title: 'مبيعات اليوم',
        value: dailyReport?.totalSales || 0,
        currency: true,
        color: 'green' as const,
        icon: (
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
        trend: { value: 12, isPositive: true },
      },
      {
        title: 'عدد الفواتير',
        value: dailyReport?.totalInvoices || 0,
        color: 'blue' as const,
        icon: (
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
        trend: { value: 5, isPositive: true },
      },
      {
        title: 'العملاء',
        value: dailyReport?.totalCustomers || 0,
        color: 'purple' as const,
        icon: (
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
      },
    ],
    [dailyReport]
  );

  if (isLoading) return <PageLoader />;

  const chartData = dailyReport?.salesByHour || [];
  const pieData = [
    { name: 'نقداً', value: 4000, color: '#10b981' },
    { name: 'بنكي', value: 3000, color: '#3b82f6' },
    { name: 'شيك', value: 2000, color: '#f59e0b' },
    { name: 'آجل', value: 1000, color: '#8b5cf6' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">لوحة التحكم</h1>
          <p className="text-sm text-gray-500 dark:text-zinc-400 mt-1">{formatDate(today)} - ملخص يومي</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {stats.map((stat, idx) => (
          <StatsCard key={idx} {...stat} />
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">المبيعات خلال اليوم</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="hour" tickFormatter={(h) => `${h}:00`} />
              <YAxis />
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
              <Area type="monotone" dataKey="amount" stroke="#10b981" fill="#d1fae5" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">طرق الدفع</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={100} paddingAngle={5} dataKey="value">
                {pieData.map((entry, idx) => (
                  <Cell key={idx} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip formatter={(value: number) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
          <div className="flex flex-wrap gap-3 mt-2">
            {pieData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-1 text-sm">
                <div className="h-3 w-3 rounded-full" style={{ backgroundColor: entry.color }} />
                <span className="text-gray-600 dark:text-zinc-400">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Sales */}
      <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">آخر المبيعات</h3>
        {dailyReport?.recentSales && dailyReport.recentSales.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="px-4 py-3 text-right text-xs font-semibold">رقم الفاتورة</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">العميل</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">المبلغ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {dailyReport.recentSales.map((sale: any) => (
                  <tr key={sale.id} className="table-row">
                    <td className="px-4 py-3 text-sm font-medium text-primary-600">{sale.invoiceNumber}</td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-zinc-300">{sale.customerName}</td>
                    <td className="px-4 py-3 text-sm font-medium">{formatCurrency(sale.total)}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={sale.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-gray-500 dark:text-zinc-400 py-8">لا توجد مبيعات اليوم</p>
        )}
      </div>
    </div>
  );
}
