import { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useNavigate } from 'react-router-dom';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageHeader } from '@/components/ui/PageHeader';
import { getDailyReport } from '@/api/sales';
import { getEmployees, getDepartments, getLeaves, getPayroll } from '@/api/hr';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate, getCommandShortcutLabel } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useCommandPaletteStore } from '@/stores/commandPaletteStore';
import { useUIStore } from '@/stores/uiStore';
import { usePermissions } from '@/hooks/usePermissions';

export default function DashboardPage() {
  const navigate = useNavigate();
  const openCommand = useCommandPaletteStore((s) => s.open);
  const isDark = useUIStore((s) => s.theme) === 'dark';
  const today = new Date().toISOString().split('T')[0];
  const { hasPermission, hasAnyPermission, isAdmin } = usePermissions();
  const canViewSales = hasAnyPermission(['VIEW_SALE']);
  const canViewPurchases = hasAnyPermission(['VIEW_PURCHASE']);
  const canViewReports = hasPermission('VIEW_REPORTS');
  const canViewJournal = hasPermission('VIEW_JOURNAL');
  const canManageHR = hasAnyPermission(['MANAGE_HR', 'VIEW_HR']);
  const canManageInventory = hasAnyPermission(['MANAGE_INVENTORY', 'VIEW_INVENTORY']);
  const canCreateSale = hasPermission('CREATE_SALE');
  const canCreatePurchase = hasPermission('CREATE_PURCHASE');
  const canManageAssets = hasPermission('MANAGE_ASSETS');
  const canManageBudgets = hasPermission('MANAGE_BUDGETS');

  const { data: dailyReport, isLoading } = useQuery({
    queryKey: ['dashboard', 'daily', today],
    queryFn: () => getDailyReport(today),
    enabled: canViewSales || canViewReports || isAdmin,
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 1 }], queryFn: () => getEmployees({ pageSize: 1 }), enabled: canManageHR || isAdmin });
  const { data: deptData } = useQuery({ queryKey: ['departments'], queryFn: getDepartments, enabled: canManageHR || isAdmin });
  const { data: leavesData } = useQuery({ queryKey: ['leaves', { pageSize: 1, status: 'pending' }], queryFn: () => getLeaves({ pageSize: 1, status: 'pending' }), enabled: canManageHR || isAdmin });
  const { data: payrollData } = useQuery({ queryKey: ['payroll', { pageSize: 1, status: 'draft' }], queryFn: () => getPayroll({ pageSize: 1, status: 'draft' }), enabled: canManageHR || isAdmin });

  const sparkSales = useMemo(() => (dailyReport?.salesByHour || []).map((h) => h.amount), [dailyReport]);

  const salesTrend = dailyReport?.vsYesterday
    ? { value: dailyReport.vsYesterday.sales, isPositive: dailyReport.vsYesterday.sales >= 0, label: 'عن الأمس' }
    : undefined;
  const invoicesTrend = dailyReport?.vsYesterday
    ? { value: dailyReport.vsYesterday.invoices, isPositive: dailyReport.vsYesterday.invoices >= 0, label: 'عن الأمس' }
    : undefined;

  const stats = useMemo(
    () => [
      {
        title: 'مبيعات اليوم',
        value: dailyReport?.totalSales || 0,
        currency: true,
        color: 'green' as const,
        sparkData: sparkSales,
        ...(salesTrend ? { trend: salesTrend } : {}),
        icon: (
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        ),
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
        ...(invoicesTrend ? { trend: invoicesTrend } : {}),
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
    [dailyReport, sparkSales, salesTrend, invoicesTrend]
  );

  if (isLoading) return <PageLoader />;

  const chartData = dailyReport?.salesByHour || [];
  const PIE_COLORS: Record<string, string> = {
    cash: '#10b981',
    bank: '#3b82f6',
    cheque: '#f59e0b',
    credit: '#8b5cf6',
    other: '#6b7280',
  };
  const PIE_LABELS: Record<string, string> = {
    cash: 'نقداً',
    bank: 'بنكي',
    cheque: 'شيك',
    credit: 'آجل',
    other: 'أخرى',
  };
  const rawPaymentMethods = dailyReport?.paymentMethods || [];
  const pieData = rawPaymentMethods
    .filter((pm) => pm.value > 0)
    .map((pm) => ({
      name: PIE_LABELS[pm.name] || pm.name,
      value: pm.value,
      color: PIE_COLORS[pm.name] || '#6b7280',
    }));
  const hasPaymentData = pieData.length > 0;
  const totalPayments = pieData.reduce((sum, entry) => sum + entry.value, 0);

  const pendingTasks = [
    { title: 'طلبات اعتماد فواتير', count: dailyReport?.approvalPending || 0, path: '/sales', color: 'text-primary-600', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' },
    { title: 'طلبات إجازة معلقة', count: leavesData?.total || 0, path: '/hr/leaves', color: 'text-amber-600', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' },
    { title: 'كشوف رواتب مسودة', count: payrollData?.total || 0, path: '/hr/payroll', color: 'text-blue-600', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
  ];

  const quickActions = [
    { title: 'فاتورة بيع جديدة', path: '/sales/new', color: 'bg-emerald-500', icon: 'M12 4v16m8-8H4' },
    { title: 'عرض سعر', path: '/quotations/new', color: 'bg-blue-500', icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z' },
    { title: 'أمر شراء', path: '/purchases/new', color: 'bg-amber-500', icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z' },
    { title: 'دفعة عميل', path: '/payments/customers', color: 'bg-purple-500', icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z' },
    { title: 'موظف جديد', path: '/hr/employees', color: 'bg-pink-500', icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z' },
    { title: 'الدفتر الأكبر', path: '/accounting/journal', color: 'bg-rose-500', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' },
  ];

  return (
    <div className="space-y-6">
      {/* Hero / welcome strip */}
      <div className="card-gradient p-6 rounded-2xl border border-gray-200 dark:border-zinc-800 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="page-title">لوحة التحكم</h1>
          <p className="page-subtitle">{formatDate(today)} — ملخص يومي شامل لأداء النظام</p>
        </div>
        <button
          onClick={openCommand}
          className="btn-secondary w-full justify-between md:w-auto md:min-w-72"
        >
          <span className="flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
            بحث سريع في النظام...
          </span>
          <kbd className="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-xs dark:border-zinc-600 dark:bg-zinc-700">
            {getCommandShortcutLabel()}
          </kbd>
        </button>
      </div>

      {/* Stats */}
      {(canViewSales || canViewReports || isAdmin) && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {stats.map((stat, idx) => (
            <StatsCard key={idx} {...stat} />
          ))}
        </div>
      )}

      {/* Quick Actions */}
      {(canCreateSale || canCreatePurchase || canViewJournal || canManageHR || isAdmin) && (
        <div className="card p-5">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">إجراءات سريعة</h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {(canCreateSale ? [{ title: 'فاتورة بيع جديدة', path: '/sales/new', color: 'bg-emerald-500', icon: 'M12 4v16m8-8H4' }] : [])
              .concat(canViewJournal ? [{ title: 'عرض سعر', path: '/quotations/new', color: 'bg-blue-500', icon: 'M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z' }] : [])
              .concat(canCreatePurchase ? [{ title: 'أمر شراء', path: '/purchases/new', color: 'bg-amber-500', icon: 'M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z' }] : [])
              .concat([{ title: 'دفعة عميل', path: '/payments/customers', color: 'bg-purple-500', icon: 'M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z' }])
              .concat((canManageHR || isAdmin) ? [{ title: 'موظف جديد', path: '/hr/employees', color: 'bg-pink-500', icon: 'M18 9v3m0 0v3m0-3h3m-3 0h-3m-2-5a4 4 0 11-8 0 4 4 0 018 0zM3 20a6 6 0 0112 0v1H3v-1z' }] : [])
              .concat(canViewJournal ? [{ title: 'الدفتر الأكبر', path: '/accounting/journal', color: 'bg-rose-500', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253' }] : [])
              .filter((a, i, arr) => arr.findIndex(x => x.path === a.path) === i)
              .map((action) => (
                <button
                  key={action.title}
                  onClick={() => navigate(action.path)}
                  className="flex flex-col items-center gap-2 p-4 rounded-xl border border-gray-200 dark:border-zinc-800 hover:border-primary-400 dark:hover:border-primary-500 hover:shadow-md transition-all group"
                >
                  <div className={`${action.color} text-white p-2.5 rounded-xl group-hover:scale-110 transition-transform`}>
                    <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={action.icon} /></svg>
                  </div>
                  <span className="text-xs font-medium text-gray-700 dark:text-zinc-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 text-center">{action.title}</span>
                </button>
              ))}
          </div>
        </div>
      )}

      {/* HR Summary + Tasks */}
      {(canManageHR || isAdmin) && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* HR Quick Stats */}
          <div>
            <PageHeader
              title="الموارد البشرية"
              subtitle="نظرة سريعة على القوى العاملة"
              actions={<button onClick={() => navigate('/hr/employees')} className="btn-ghost btn-sm">عرض الكل</button>}
            />
            <div className="grid grid-cols-2 gap-3">
              <button onClick={() => navigate('/hr/employees')} className="text-right">
                <StatsCard title="الموظفون" value={empData?.total || 0} color="green" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" /></svg>} />
              </button>
              <button onClick={() => navigate('/hr/departments')} className="text-right">
                <StatsCard title="الأقسام" value={deptData?.total || 0} color="blue" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>} />
              </button>
              <button onClick={() => navigate('/hr/leaves')} className="text-right">
                <StatsCard title="إجازات معلقة" value={leavesData?.total || 0} color="yellow" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>} />
              </button>
              <button onClick={() => navigate('/hr/payroll')} className="text-right">
                <StatsCard title="رواتب مسودة" value={payrollData?.total || 0} color="purple" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} />
              </button>
            </div>
          </div>

          {/* Tasks requiring approval */}
          {(canViewSales || canManageHR || isAdmin) && (
            <div className="card p-5">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">مهام بانتظار موافقتك</h3>
              <div className="space-y-3">
                {(canViewSales ? [{ title: 'طلبات اعتماد فواتير', count: dailyReport?.approvalPending || 0, path: '/sales', color: 'text-primary-600', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' }] : [])
                  .concat((canManageHR || isAdmin) ? [{ title: 'طلبات إجازة معلقة', count: leavesData?.total || 0, path: '/hr/leaves', color: 'text-amber-600', icon: 'M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' }, { title: 'كشوف رواتب مسودة', count: payrollData?.total || 0, path: '/hr/payroll', color: 'text-blue-600', icon: 'M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' }] : [])
                  .map((task) => (
                    <button
                      key={task.title}
                      onClick={() => navigate(task.path)}
                      className="w-full flex items-center justify-between p-4 rounded-xl border border-gray-200 dark:border-zinc-800 hover:border-primary-400 dark:hover:border-primary-500 hover:shadow-sm transition-all group"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-gray-100 dark:bg-zinc-800 group-hover:bg-primary-50 dark:group-hover:bg-primary-500/10 transition-colors">
                          <svg className={`h-5 w-5 ${task.color}`} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={task.icon} /></svg>
                        </div>
                        <span className="text-sm text-gray-700 dark:text-zinc-300 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">{task.title}</span>
                      </div>
                      <span className={`text-2xl font-bold ${task.color}`}>{task.count}</span>
                    </button>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Charts */}
      {(canViewSales || canViewReports || isAdmin) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 card">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">المبيعات خلال اليوم</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={chartData}>
              <defs>
                <linearGradient id="salesGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid
                strokeDasharray="3 3"
                stroke={isDark ? '#27272a' : '#eef2f7'}
                vertical={false}
              />
              <XAxis
                dataKey="hour"
                tickFormatter={(h) => `${h}:00`}
                tick={{ fill: isDark ? '#a1a1aa' : '#64748b', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                width={64}
                tick={{ fill: isDark ? '#a1a1aa' : '#64748b', fontSize: 12 }}
                axisLine={false}
                tickLine={false}
                tickFormatter={(value) =>
                  new Intl.NumberFormat('ar-EG', {
                    notation: 'compact',
                    maximumFractionDigits: 1,
                  }).format(Number(value))
                }
              />
              <Tooltip
                cursor={{ stroke: isDark ? '#3f3f46' : '#e2e8f0' }}
                formatter={(value: number) => formatCurrency(value)}
                contentStyle={{
                  backgroundColor: isDark ? '#18181b' : '#ffffff',
                  border: `1px solid ${isDark ? '#3f3f46' : '#e5e7eb'}`,
                  borderRadius: 12,
                  boxShadow: '0 10px 30px -12px rgb(0 0 0 / 0.35)',
                }}
                labelStyle={{ color: isDark ? '#e4e4e7' : '#111827', fontWeight: 600 }}
                itemStyle={{ color: isDark ? '#34d399' : '#059669' }}
              />
              <Area
                type="monotone"
                dataKey="amount"
                stroke="#10b981"
                fill="url(#salesGradient)"
                strokeWidth={2}
                activeDot={{ r: 5, strokeWidth: 2, stroke: isDark ? '#18181b' : '#ffffff' }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">طرق الدفع</h3>
          {hasPaymentData ? (
            <>
              <div className="relative">
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={64}
                      outerRadius={102}
                      paddingAngle={4}
                      stroke="none"
                      dataKey="value"
                    >
                      {pieData.map((entry, idx) => (
                        <Cell key={idx} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value: number) => formatCurrency(value)}
                      contentStyle={{
                        backgroundColor: isDark ? '#18181b' : '#ffffff',
                        border: `1px solid ${isDark ? '#3f3f46' : '#e5e7eb'}`,
                        borderRadius: 12,
                        boxShadow: '0 10px 30px -12px rgb(0 0 0 / 0.35)',
                      }}
                      labelStyle={{ color: isDark ? '#e4e4e7' : '#111827', fontWeight: 600 }}
                      itemStyle={{ color: isDark ? '#e4e4e7' : '#374151' }}
                    />
                  </PieChart>
                </ResponsiveContainer>
                <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[11px] text-gray-500 dark:text-zinc-400">إجمالي اليوم</span>
                  <span className="text-sm font-bold tabular-nums text-gray-900 dark:text-zinc-100">
                    {new Intl.NumberFormat('ar-EG', {
                      notation: 'compact',
                      maximumFractionDigits: 1,
                    }).format(totalPayments)}
                  </span>
                </div>
              </div>
              <div className="mt-2 flex flex-wrap justify-center gap-3">
                {pieData.map((entry) => (
                  <div key={entry.name} className="flex items-center gap-1.5 text-sm">
                    <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                    <span className="text-gray-600 dark:text-zinc-400">{entry.name}</span>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-center text-gray-500 dark:text-zinc-400 py-12">لا توجد مدفوعات اليوم</p>
          )}
        </div>
      </div>
      )}

      {/* Recent Sales */}
      {(canViewSales || isAdmin) && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100">آخر المبيعات</h3>
          <button onClick={() => navigate('/sales')} className="btn-ghost btn-sm">عرض الكل</button>
        </div>
        {dailyReport?.recentSales && dailyReport.recentSales.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px]" aria-label="آخر المبيعات">
              <thead>
                <tr className="table-header">
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold">رقم الفاتورة</th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold">العميل</th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold">المبلغ</th>
                  <th scope="col" className="px-4 py-3 text-right text-xs font-semibold">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {dailyReport.recentSales.map((sale: any) => (
                  <tr
                    key={sale.id}
                    className="table-row cursor-pointer"
                    onClick={() => navigate(`/sales/${sale.id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-medium">
                      <Link
                        to={`/sales/${sale.id}`}
                        onClick={(event) => event.stopPropagation()}
                        className="text-primary-600 hover:underline dark:text-primary-400"
                      >
                        {sale.invoiceNumber || '—'}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700 dark:text-zinc-300">
                      {sale.customerName || '—'}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium tabular-nums">
                      {formatCurrency(sale.total)}
                    </td>
                    <td className="px-4 py-3"><StatusBadge status={sale.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-center text-gray-500 dark:text-zinc-400 py-8">لا توجد مبيعات اليوم</p>
        )}
        </div>
      )}

      {!canViewSales && !canViewReports && !canManageHR && !canViewJournal && !canCreateSale && !canCreatePurchase && !isAdmin && (
        <div className="card p-8 text-center">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-2">مرحباً بك</h3>
          <p className="text-sm text-gray-600 dark:text-zinc-400">لا توجد أقسام متاحة لك لعرضها في لوحة التحكم حالياً. يرجى التواصل مع المسؤول لطلب الصلاحيات المناسبة.</p>
        </div>
      )}
    </div>
  );
}
