import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getPurchasesReport } from '@/api/reports';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
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

export default function PurchasesReportPage() {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [showPrint, setShowPrint] = useState(false);
  const company = useCompany();
  const settings = useGeneralSettings();

  const { data, isLoading } = useQuery({
    queryKey: ['purchases-report', startDate, endDate],
    queryFn: () => getPurchasesReport({ startDate: startDate || undefined, endDate: endDate || undefined }),
  });

  if (isLoading) return <PageLoader />;

  const report = data as any;

  return (
    <div className="space-y-6">
      <PageHeader
        title="تقرير المشتريات"
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
        <StatsCard title="إجمالي المشتريات" value={report?.totalPurchases || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>} color="blue" />
        <StatsCard title="المرتجعات" value={report?.totalReturns || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z" /></svg>} color="red" />
        <StatsCard title="صافي المشتريات" value={report?.netPurchases || 0} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} color="green" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">المشتريات الشهرية</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={report?.purchasesByMonth || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip formatter={(v: number) => formatCurrency(v)} />
              <Bar dataKey="amount" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">أعلى الموردين</h3>
          {report?.topSuppliers && report.topSuppliers.length > 0 ? (
            <div className="space-y-3">
              {report.topSuppliers.map((s: any, idx: any) => (
                <div key={idx} className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-zinc-800">
                  <p className="font-medium text-sm">{s.name}</p>
                  <span className="font-bold text-sm">{formatCurrency(s.amount)}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-zinc-400 text-sm text-center py-8">لا توجد بيانات</p>
          )}
        </div>
      </div>

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title="تقرير المشتريات"
        filename="تقرير-المشتريات"
      >
        <PrintDocument
          company={company}
          title="تقرير المشتريات"
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
                <td className={TABLE_CELL}>إجمالي المشتريات</td>
                <td className={`${TABLE_CELL} text-center font-semibold`}>{formatCurrency(report?.totalPurchases || 0)}</td>
              </tr>
              <tr>
                <td className={TABLE_CELL}>المرتجعات</td>
                <td className={`${TABLE_CELL} text-center`}>{formatCurrency(report?.totalReturns || 0)}</td>
              </tr>
              <tr className="bg-gray-50">
                <td className={`${TABLE_CELL} font-bold`}>صافي المشتريات</td>
                <td className={`${TABLE_CELL} text-center font-bold text-primary-600`}>{formatCurrency(report?.netPurchases || 0)}</td>
              </tr>
            </tbody>
          </table>

          <h3 className="text-sm font-bold mb-2">المشتريات الشهرية</h3>
          <table className="w-full text-sm mb-6">
            <thead>
              <tr className="bg-gray-100">
                <th className={TABLE_HEAD}>الشهر</th>
                <th className={`${TABLE_HEAD} text-center`}>المبلغ</th>
              </tr>
            </thead>
            <tbody>
              {(report?.purchasesByMonth || []).map((row: any, i: number) => (
                <tr key={i}>
                  <td className={TABLE_CELL}>{row.month}</td>
                  <td className={`${TABLE_CELL} text-center`}>{formatCurrency(row.amount || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <h3 className="text-sm font-bold mb-2">أعلى الموردين</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className={TABLE_HEAD}>المورد</th>
                <th className={`${TABLE_HEAD} text-center`}>المبلغ</th>
              </tr>
            </thead>
            <tbody>
              {(report?.topSuppliers || []).map((row: any, i: number) => (
                <tr key={i}>
                  <td className={TABLE_CELL}>{row.name}</td>
                  <td className={`${TABLE_CELL} text-center`}>{formatCurrency(row.amount || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
