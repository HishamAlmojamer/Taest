import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatNumber } from '@/lib/utils';
import {
  getAnalyticsSummary, getCashFlowForecast, getAnomalies, getDuplicates,
  getAccountSuggestions, getReconciliationSuggestions,
  type AccountSuggestion,
} from '@/api/analytics';

const SEVERITY_LABEL: Record<string, string> = {
  high: 'عالي الخطورة',
  medium: 'متوسط',
  low: 'منخفض',
};
const SEVERITY_COLOR: Record<string, string> = {
  high: 'bg-red-100 text-red-700 dark:bg-red-500/10 dark:text-red-400',
  medium: 'bg-amber-100 text-amber-700 dark:bg-amber-500/10 dark:text-amber-400',
  low: 'bg-green-100 text-green-700 dark:bg-green-500/10 dark:text-green-400',
};

function SeverityBadge({ severity }: { severity: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${SEVERITY_COLOR[severity] || SEVERITY_COLOR.low}`}>
      {SEVERITY_LABEL[severity] || severity}
    </span>
  );
}

export default function AnalyticsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="التحليلات والذكاء الاصطناعي" subtitle="رؤى اقتصادية وفرز آلي للشاذ والمكرر والتنبؤ بالتدفق النقدي" />
      <AnalyticsTabs />
    </div>
  );
}

function AnalyticsTabs() {
  const [tab, setTab] = useState<'kpi' | 'forecast' | 'anomalies' | 'duplicates' | 'suggest'>('kpi');

  const { data: summary, isLoading } = useQuery({
    queryKey: ['analytics', 'summary'],
    queryFn: getAnalyticsSummary,
  });
  const { data: forecast } = useQuery({
    queryKey: ['analytics', 'forecast'],
    queryFn: () => getCashFlowForecast(6),
  });

  const currency = summary?.currency || 'SAR';

  const tabs = [
    { key: 'kpi' as const, label: 'المؤشرات الرئيسية' },
    { key: 'forecast' as const, label: 'التدفق النقدي' },
    { key: 'anomalies' as const, label: 'اكتشاف الشاذ' },
    { key: 'duplicates' as const, label: 'اكتشاف المكرر' },
    { key: 'suggest' as const, label: 'اقتراح حسابات' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-primary-600 text-white'
                : 'bg-white dark:bg-zinc-800 border border-gray-200 dark:border-zinc-700 text-gray-700 dark:text-zinc-300 hover:border-primary-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'kpi' && (
        <div className="space-y-6">
          {isLoading ? <PageLoader /> : (
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
              <StatsCard title="إيرادات الشهر" value={summary?.revenueMonth ?? 0} currency color="green" />
              <StatsCard title="مصاريف الشهر" value={summary?.expensesMonth ?? 0} currency color="red" />
              <StatsCard title="صافي ربح الشهر" value={summary?.netProfitMonth ?? 0} currency color="purple" />
              <StatsCard title="صافي ربح السنة" value={summary?.netProfitYear ?? 0} currency color="blue" />
              <StatsCard title="رصيد البنوك" value={summary?.bankBalance ?? 0} currency color="yellow" />
              <StatsCard title="مستحقات (عملاء)" value={summary?.receivables ?? 0} currency color="blue" />
            </div>
          )}

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-2">التدفق النقدي المتوقع (6 أشهر)</h3>
              {forecast && (
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={forecast.projections}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip formatter={(value: number) => formatCurrency(value, currency)} />
                    <Bar dataKey="forecastIn" name="داخل" fill="#10b981" />
                    <Bar dataKey="forecastOut" name="خارج" fill="#ef4444" />
                    <Bar dataKey="closingBalance" name="رصيد ختامي" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              )}
            </div>
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-4">بيانات إضافية</h3>
              {summary && (
                <dl className="space-y-3 text-sm">
                  <div className="flex justify-between"><dt className="text-gray-500 dark:text-zinc-400">إيرادات السنة</dt><dd className="font-medium">{formatCurrency(summary.revenueYear, currency)}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500 dark:text-zinc-400">مصاريف السنة</dt><dd className="font-medium">{formatCurrency(summary.expensesYear, currency)}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500 dark:text-zinc-400">مستحقات (موردين)</dt><dd className="font-medium">{formatCurrency(summary.payables, currency)}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500 dark:text-zinc-400">فواتير بيع بانتظار الاعتماد</dt><dd className="font-medium">{formatNumber(summary.pendingSales)}</dd></div>
                  <div className="flex justify-between"><dt className="text-gray-500 dark:text-zinc-400">أوامر شراء بانتظار الاعتماد</dt><dd className="font-medium">{formatNumber(summary.pendingPurchases)}</dd></div>
                </dl>
              )}
            </div>
          </div>
        </div>
      )}

      {tab === 'forecast' && <ForecastTab />}
      {tab === 'anomalies' && <AnomaliesTab />}
      {tab === 'duplicates' && <DuplicatesTab />}
      {tab === 'suggest' && <SuggestTab />}
    </div>
  );
}

function ForecastTab() {
  const { data: forecast, isLoading } = useQuery({
    queryKey: ['analytics', 'forecast'],
    queryFn: () => getCashFlowForecast(6),
  });

  if (isLoading) return <PageLoader />;
  if (!forecast) return null;

  const currency = forecast.currency || 'SAR';
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100">التنبؤ بالتدفق النقدي</h3>
        <span className="text-xs text-gray-500 dark:text-zinc-400">
          أساس: متوسط شهري {formatCurrency(forecast.averageMonthlyIn, currency)} داخل / {formatCurrency(forecast.averageMonthlyOut, currency)} خارج
        </span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="table-header">
              <th className="px-4 py-3 text-right text-xs font-semibold">الشهر</th>
              <th className="px-4 py-3 text-right text-xs font-semibold">تدفق داخل</th>
              <th className="px-4 py-3 text-right text-xs font-semibold">تدفق خارج</th>
              <th className="px-4 py-3 text-right text-xs font-semibold">الصافي</th>
              <th className="px-4 py-3 text-right text-xs font-semibold">رصيد ختامي</th>
            </tr>
          </thead>
          <tbody>
            {forecast.projections.map((p) => (
              <tr key={p.month} className="table-row">
                <td className="px-4 py-3 text-sm font-medium">{p.month}</td>
                <td className="px-4 py-3 text-sm text-emerald-600">{formatCurrency(p.forecastIn, currency)}</td>
                <td className="px-4 py-3 text-sm text-red-500">{formatCurrency(p.forecastOut, currency)}</td>
                <td className="px-4 py-3 text-sm">{formatCurrency(p.net, currency)}</td>
                <td className="px-4 py-3 text-sm font-semibold">{formatCurrency(p.closingBalance, currency)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AnomaliesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'anomalies'],
    queryFn: () => getAnomalies(90),
  });

  if (isLoading) return <PageLoader />;
  if (!data) return null;

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100">عمليات غير معتادة في دفاتر اليومية</h3>
        <span className="text-xs text-gray-500 dark:text-zinc-400">{data.notes}</span>
      </div>
      {data.anomalies.length === 0 ? (
        <p className="text-center text-gray-500 dark:text-zinc-400 py-10">لم تُرصد أي عمليات شاذة في النافذة الحالية</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="px-4 py-3 text-right text-xs font-semibold">القيد</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">التاريخ</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">الوصف</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">المبلغ</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">الخطورة</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">السبب</th>
              </tr>
            </thead>
            <tbody>
              {data.anomalies.map((a) => (
                <tr key={a.entryId} className="table-row">
                  <td className="px-4 py-3 text-sm font-medium text-primary-600">{a.entryNumber}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 dark:text-zinc-300">{a.entryDate}</td>
                  <td className="px-4 py-3 text-sm text-gray-700 dark:text-zinc-300 max-w-xs truncate">{a.description}</td>
                  <td className="px-4 py-3 text-sm font-medium">{formatCurrency(a.amount)}</td>
                  <td className="px-4 py-3"><SeverityBadge severity={a.severity} /></td>
                  <td className="px-4 py-3 text-sm text-gray-500 dark:text-zinc-400">{a.reason}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function DuplicatesTab() {
  const { data, isLoading } = useQuery({
    queryKey: ['analytics', 'duplicates'],
    queryFn: () => getDuplicates(120),
  });

  if (isLoading) return <PageLoader />;
  if (!data) return null;

  const jeDupes = data.journalEntries || [];
  const cpDupes = data.customerPayments || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-2">قيود يومية متكررة محتملة</h3>
        <p className="text-xs text-gray-500 dark:text-zinc-400 mb-3">نفس المبلغ في نفس اليوم لعدة قيود</p>
        {jeDupes.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-zinc-400 py-8">لا توجد تكرارات</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="px-4 py-3 text-right text-xs font-semibold">التاريخ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">المبلغ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">العدد</th>
                </tr>
              </thead>
              <tbody>
                {jeDupes.map((d, i) => (
                  <tr key={i} className="table-row">
                    <td className="px-4 py-3 text-sm">{d.date}</td>
                    <td className="px-4 py-3 text-sm font-medium">{formatCurrency(d.amount)}</td>
                    <td className="px-4 py-3"><span className="badge-danger">{d.count}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-2">دفعات عملاء متكررة محتملة</h3>
        <p className="text-xs text-gray-500 dark:text-zinc-400 mb-3">نفس المبلغ والطريقة في نفس اليوم</p>
        {cpDupes.length === 0 ? (
          <p className="text-center text-gray-500 dark:text-zinc-400 py-8">لا توجد تكرارات</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="px-4 py-3 text-right text-xs font-semibold">التاريخ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">المبلغ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">الطريقة</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">العدد</th>
                </tr>
              </thead>
              <tbody>
                {cpDupes.map((d, i) => (
                  <tr key={i} className="table-row">
                    <td className="px-4 py-3 text-sm">{d.date}</td>
                    <td className="px-4 py-3 text-sm font-medium">{formatCurrency(d.amount)}</td>
                    <td className="px-4 py-3 text-sm">{d.method}</td>
                    <td className="px-4 py-3"><span className="badge-danger">{d.count}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function SuggestTab() {
  const [text, setText] = useState('');
  const [type, setType] = useState('');
  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['analytics', 'suggest', text, type],
    queryFn: () => getAccountSuggestions(text, type || undefined, 10),
    enabled: false,
  });

  const run = () => {
    if (text.trim().length < 2) return;
    void refetch();
  };

  const typeOptions = [
    { value: '', label: 'كل الأنواع' },
    { value: 'asset', label: 'أصل' },
    { value: 'liability', label: 'التزام' },
    { value: 'equity', label: 'حقوق ملكية' },
    { value: 'revenue', label: 'إيراد' },
    { value: 'expense', label: 'مصروف' },
  ];

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-zinc-100 mb-2">اقتراح حساب من وصف عملية</h3>
      <p className="text-xs text-gray-500 dark:text-zinc-400 mb-4">اكتب وصفاً حراً (مثل: دفعة إيجار للمقر) ليُحلّل ويقترح حسابات من دليل الحسابات</p>
      <div className="flex flex-col sm:flex-row gap-3 items-end">
        <div className="flex-1">
          <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 mb-1">الوصف</label>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && run()}
            className="input"
            placeholder="مثال: إيجار المقر الشهري"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 dark:text-zinc-400 mb-1">نوع الحساب</label>
          <select value={type} onChange={(e) => setType(e.target.value)} className="input">
            {typeOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        </div>
        <button onClick={run} className="btn-primary" disabled={isFetching || text.trim().length < 2}>
          {isFetching ? '···' : 'حلّل واقترح'}
        </button>
      </div>

      {data && (
        <div className="mt-6">
          <h4 className="text-sm font-medium text-gray-700 dark:text-zinc-300 mb-3">نتائج البحث عن «{data.query}»</h4>
          {data.suggestions.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-zinc-400 py-6">لا تطابق — جرّب كلمات أخرى</p>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {data.suggestions.map((s: AccountSuggestion) => (
                <div key={s.id} className="p-3 rounded-xl border border-gray-200 dark:border-zinc-800 hover:border-primary-400 transition-colors">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-sm text-primary-600">{s.code}</span>
                    <span className="text-xs text-gray-400">{s.score} تطابق</span>
                  </div>
                  <div className="text-sm font-medium mt-1">{s.name}</div>
                  {s.nameEn && <div className="text-xs text-gray-500 dark:text-zinc-400">{s.nameEn}</div>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}