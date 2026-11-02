import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatsCard } from '@/components/ui/StatsCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import {
  getCrmDashboard, getPipelineFunnel, getLeadsBySource, getCustomersBySegment,
  type FollowUp,
} from '@/api/crm';
import { formatCurrency, formatDateTime } from '@/lib/utils';
import { IconLayoutDashboard, IconUsers, IconZap, IconTarget, IconCheckCircle, IconTrendingUp, IconPieChart, IconFilter, IconCalendarClock } from '@/components/ui/Icons';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid, Cell, PieChart as RCPieChart, Pie, Legend } from 'recharts';

const STAGE_COLORS = ['#6366f1', '#8b5cf6', '#a855f7', '#ec4899', '#f59e0b', '#10b981', '#ef4444'];

export default function CrmDashboardPage() {
  const { data: dashboard, isLoading } = useQuery({
    queryKey: ['crm-dashboard'],
    queryFn: () => getCrmDashboard(),
  });
  const { data: funnelData } = useQuery({ queryKey: ['crm-funnel'], queryFn: getPipelineFunnel });
  const { data: sourceData } = useQuery({ queryKey: ['crm-sources'], queryFn: getLeadsBySource });
  const { data: segmentData } = useQuery({ queryKey: ['crm-segments-report'], queryFn: getCustomersBySegment });

  const funnel = funnelData?.items || [];
  const sources = sourceData?.items || [];
  const segments = segmentData?.items || [];
  const upcoming: FollowUp[] = dashboard?.upcomingFollowups || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="لوحة CRM"
        subtitle="نظرة شاملة على العملاء والفرص وخط المبيعات"
        icon={<IconLayoutDashboard className="h-6 w-6" />}
      />

      {isLoading ? (
        <div className="p-8 text-center text-gray-500">جارٍ التحميل...</div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatsCard title="إجمالي العملاء" value={dashboard?.totalCustomers ?? 0} icon={<IconUsers className="h-6 w-6" />} color="green" footer={<span className="text-xs text-gray-400">عميل مسجل</span>} />
            <StatsCard title="العملاء المحتملون" value={dashboard?.totalLeads ?? 0} icon={<IconZap className="h-6 w-6" />} color="blue" footer={<span className="text-xs text-gray-400">عميل محتمل</span>} />
            <StatsCard title="الفرص المفتوحة" value={dashboard?.openOpportunities ?? 0} icon={<IconTarget className="h-6 w-6" />} color="purple" footer={<span className="text-xs text-gray-400">بقيمة {formatCurrency(dashboard?.pipelineValue ?? 0)}</span>} />
            <StatsCard title="الفرص المكسبة" value={formatCurrency(dashboard?.wonValue ?? 0)} icon={<IconCheckCircle className="h-6 w-6" />} color="red" footer={<span className="text-xs text-gray-400">قيمة الصفقات المغلقة</span>} />
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Pipeline funnel */}
            <div className="card p-5 lg:col-span-2">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconTrendingUp className="h-4 w-4 text-primary-500" /> خط أنابيب المبيعات</h3>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={funnel} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#e5e7eb" />
                  <XAxis type="number" tickFormatter={(v) => formatCurrency(Number(v)).replace(/\.00$/, '')} fontSize={11} />
                  <YAxis type="category" dataKey="name" width={90} fontSize={12} />
                  <Tooltip formatter={(v) => formatCurrency(Number(v))} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={28}>
                    {funnel.map((_, i) => <Cell key={i} fill={STAGE_COLORS[i % STAGE_COLORS.length]} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div className="mt-3 flex flex-wrap gap-2">
                {funnel.map((s) => (
                  <div key={s.stageId} className="flex items-center gap-1.5 text-xs text-gray-500">
                    <span className="h-2.5 w-2.5 rounded-full" style={{ background: STAGE_COLORS[0] }} />
                    {s.nameAr || s.name} ({s.count})
                  </div>
                ))}
              </div>
            </div>

            {/* Leads by source */}
            <div className="card p-5">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconPieChart className="h-4 w-4 text-sky-500" /> العملاء المحتملون حسب المصدر</h3>
              <ResponsiveContainer width="100%" height={220}>
                <RCPieChart>
                  <Pie data={sources} dataKey="count" nameKey="source" innerRadius={45} outerRadius={80} paddingAngle={3}>
                    {sources.map((_, i) => <Cell key={i} fill={STAGE_COLORS[i % STAGE_COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(v) => `${v}`} />
                  <Legend fontSize={11} />
                </RCPieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid gap-6 lg:grid-cols-3">
            {/* Customers by segment */}
            <div className="card p-5 lg:col-span-2">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconFilter className="h-4 w-4 text-emerald-500" /> العملاء حسب الشريحة</h3>
              {segments.length === 0 ? (
                <p className="text-sm text-gray-400">لا توجد بيانات</p>
              ) : (
                <div className="space-y-3">
                  {segments.map((s) => (
                    <div key={s.segmentId} className="flex items-center gap-3">
                      <div className="w-28 shrink-0 text-sm text-gray-600 dark:text-zinc-300">{s.nameAr || s.name}</div>
                      <div className="flex-1 h-6 bg-gray-100 dark:bg-zinc-800 rounded-lg overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-l from-primary-500 to-violet-500 rounded-lg"
                          style={{ width: `${segments.length ? Math.max(6, (s.customerCount / Math.max(...segments.map((x) => x.customerCount), 1)) * 100) : 0}%` }}
                        />
                      </div>
                      <div className="w-40 shrink-0 text-xs text-gray-500 text-left" dir="ltr">
                        {s.customerCount} عميل · {formatCurrency(s.totalSales)}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Upcoming follow-ups */}
            <div className="card p-5">
              <h3 className="font-bold mb-4 flex items-center gap-2"><IconCalendarClock className="h-4 w-4 text-amber-500" /> المتابعات القادمة</h3>
              {upcoming.length === 0 && <p className="text-sm text-gray-400">لا توجد متابعات قادمة</p>}
              <div className="space-y-2">
                {upcoming.slice(0, 6).map((f) => (
                  <Link key={f.id} to="/crm/follow-ups" className="flex items-center justify-between rounded-lg border border-gray-100 dark:border-zinc-800 p-2.5 hover:border-primary-300 transition-colors">
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate">{f.subject || f.type || '-'}</p>
                      <p className="text-xs text-gray-400">{f.entityName || ''} · {formatDateTime(f.dueDate)}</p>
                    </div>
                    <StatusBadge status={f.status === 'OPEN' ? 'pending' : String(f.status)} />
                  </Link>
                ))}
              </div>
              <div className="mt-4 text-center">
                <Link to="/crm/follow-ups" className="text-sm text-primary-600 hover:underline">عرض كل المتابعات</Link>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
