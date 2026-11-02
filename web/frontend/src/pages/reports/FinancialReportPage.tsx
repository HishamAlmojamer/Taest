import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getFinancialReport } from '@/api/reports';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { PageHeader } from '@/components/ui/PageHeader';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatsCard } from '@/components/ui/StatsCard';
import { useCompany } from '@/hooks/useCompany';
import { useGeneralSettings } from '@/hooks/useGeneralSettings';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';

const TABLE_HEAD = 'px-3 py-2 text-right font-semibold border border-gray-300 bg-gray-100 text-sm';
const TABLE_CELL = 'px-3 py-2 border border-gray-300 text-sm';

export default function FinancialReportPage() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showPrint, setShowPrint] = useState(false);
  const company = useCompany();
  const settings = useGeneralSettings();

  const { data, isLoading } = useQuery({
    queryKey: ['financial-report', startDate, endDate],
    queryFn: () => getFinancialReport({ startDate: startDate || undefined, endDate: endDate || undefined }),
  });

  if (isLoading) return <PageLoader />;

  const report = data as any;

  return (
    <div className="space-y-6">
      <PageHeader
        title="التقرير المالي"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
        actions={<div className="flex items-center gap-3">
          <input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="input w-auto" />
          <span className="text-gray-500 dark:text-zinc-400">إلى</span>
          <input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="input w-auto" />
          <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            طباعة / PDF
          </button>
        </div>}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsCard title="الإيرادات" value={report?.revenue || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" /></svg>} color="green" />
        <StatsCard title="المصروفات" value={report?.expenses || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>} color="red" />
        <StatsCard title="صافي الدخل" value={report?.netIncome || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} color="blue" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 card">
          <h3 className="text-lg font-semibold mb-4">الإيرادات والمصروفات</h3>
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={report?.incomeByMonth || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Area type="monotone" dataKey="revenue" name="الإيرادات" stroke="#10b981" fill="#10b981" fillOpacity={0.2} />
              <Area type="monotone" dataKey="expenses" name="المصروفات" stroke="#ef4444" fill="#ef4444" fillOpacity={0.2} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">المركز المالي</h3>
          <div className="space-y-3">
            <div className="flex justify-between p-2 rounded-lg bg-gray-50 dark:bg-zinc-800">
              <span className="text-sm">الأصول</span>
              <span className="font-bold text-sm">{formatCurrency(report?.assets || 0)}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-gray-50 dark:bg-zinc-800">
              <span className="text-sm">الالتزامات</span>
              <span className="font-bold text-sm">{formatCurrency(report?.liabilities || 0)}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-gray-50 dark:bg-zinc-800">
              <span className="text-sm">حقوق الملكية</span>
              <span className="font-bold text-sm">{formatCurrency(report?.equity || 0)}</span>
            </div>
          </div>
        </div>
      </div>

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title="التقرير المالي"
        filename="التقرير-المالي"
      >
        <PrintDocument
          company={company}
          title="التقرير المالي"
          footerText={settings.receipt_footer}
          meta={[
            { label: 'من تاريخ', value: startDate ? formatDate(startDate) : '—' },
            { label: 'إلى تاريخ', value: endDate ? formatDate(endDate) : '—' },
            { label: 'تاريخ التقرير', value: formatDate(new Date().toISOString()) },
          ]}
        >
          <table className="w-full text-sm mb-6">
            <thead>
              <tr className="bg-gray-100">
                <th className={TABLE_HEAD}>البيان</th>
                <th className={`${TABLE_HEAD} text-center`}>القيمة</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className={TABLE_CELL}>الإيرادات</td>
                <td className={`${TABLE_CELL} text-center font-semibold text-green-600`}>{formatCurrency(report?.revenue || 0)}</td>
              </tr>
              <tr>
                <td className={TABLE_CELL}>المصروفات</td>
                <td className={`${TABLE_CELL} text-center font-semibold text-red-600`}>{formatCurrency(report?.expenses || 0)}</td>
              </tr>
              <tr className="bg-gray-50">
                <td className={`${TABLE_CELL} font-bold`}>صافي الدخل</td>
                <td className={`${TABLE_CELL} text-center font-bold text-primary-600`}>{formatCurrency(report?.netIncome || 0)}</td>
              </tr>
              <tr>
                <td className={TABLE_CELL}>الأصول</td>
                <td className={`${TABLE_CELL} text-center`}>{formatCurrency(report?.assets || 0)}</td>
              </tr>
              <tr>
                <td className={TABLE_CELL}>الالتزامات</td>
                <td className={`${TABLE_CELL} text-center`}>{formatCurrency(report?.liabilities || 0)}</td>
              </tr>
              <tr>
                <td className={TABLE_CELL}>حقوق الملكية</td>
                <td className={`${TABLE_CELL} text-center`}>{formatCurrency(report?.equity || 0)}</td>
              </tr>
            </tbody>
          </table>

          <h3 className="text-sm font-bold mb-2">الإيرادات والمصروفات شهرياً</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className={TABLE_HEAD}>الشهر</th>
                <th className={`${TABLE_HEAD} text-center`}>الإيرادات</th>
                <th className={`${TABLE_HEAD} text-center`}>المصروفات</th>
              </tr>
            </thead>
            <tbody>
              {(report?.incomeByMonth || []).map((row: any, i: number) => (
                <tr key={i}>
                  <td className={TABLE_CELL}>{row.month}</td>
                  <td className={`${TABLE_CELL} text-center text-green-600`}>{formatCurrency(row.revenue || 0)}</td>
                  <td className={`${TABLE_CELL} text-center text-red-600`}>{formatCurrency(row.expenses || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
