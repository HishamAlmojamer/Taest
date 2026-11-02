import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getBalanceSheet, getIncomeStatement, getCashFlowStatement, getEquityChanges, getComparativeStatement } from '@/api/financialStatements';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate } from '@/lib/utils';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { PageHeader } from '@/components/ui/PageHeader';
import ExcelExportButton from '@/components/excel/ExcelExportButton';

const tabs = [
  { key: 'balance-sheet', label: 'الميزانية العمومية' },
  { key: 'income-statement', label: 'قائمة الدخل' },
  { key: 'cash-flow', label: 'التدفقات النقدية' },
  { key: 'equity-changes', label: 'التغيرات في حقوق الملكية' },
  { key: 'comparative', label: 'بيانات مقارنة' },
];

export default function FinancialStatementsPage() {
  const company = useCompany();
  const [activeTab, setActiveTab] = useState('balance-sheet');
  const [fromDate, setFromDate] = useState(new Date().toISOString().split('T')[0]);
  const [toDate, setToDate] = useState(new Date().toISOString().split('T')[0]);
  const [showPrint, setShowPrint] = useState(false);
  const [p1From, setP1From] = useState(new Date().toISOString().split('T')[0]);
  const [p1To, setP1To] = useState(new Date().toISOString().split('T')[0]);
  const [p2From, setP2From] = useState(new Date().toISOString().split('T')[0]);
  const [p2To, setP2To] = useState(new Date().toISOString().split('T')[0]);
  const [compReportType, setCompReportType] = useState('income-statement');

  const { data, isLoading } = useQuery({
    queryKey: ['financial-statement', activeTab, fromDate, toDate, p1From, p1To, p2From, p2To, compReportType],
    queryFn: () => {
      if (activeTab === 'balance-sheet') return getBalanceSheet(fromDate);
      if (activeTab === 'income-statement') return getIncomeStatement(fromDate, toDate);
      if (activeTab === 'cash-flow') return getCashFlowStatement(fromDate, toDate);
      if (activeTab === 'equity-changes') return getEquityChanges(fromDate, toDate);
      if (activeTab === 'comparative') return getComparativeStatement(compReportType, p1From, p1To, p2From, p2To);
      return getCashFlowStatement(fromDate, toDate);
    },
  });

  if (isLoading) return <PageLoader />;

  const renderBalanceSheet = () => {
    const assets = data?.assets?.accounts || data?.assets || [];
    const liabilities = data?.liabilities?.accounts || data?.liabilities || [];
    const equity = data?.equity?.accounts || data?.equity || [];
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-0 overflow-hidden">
          <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-zinc-700">الأصول</h3>
          <table className="w-full">
            <thead><tr className="table-header"><th className="px-4 py-2 text-right text-xs">الحساب</th><th className="px-4 py-2 text-right text-xs">الرصيد</th></tr></thead>
            <tbody>{assets.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-2 text-sm">{item.account_name}</td><td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.balance)}</td></tr>)}</tbody>
          </table>
        </div>
        <div className="space-y-6">
          <div className="card p-0 overflow-hidden">
            <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-zinc-700">الخصوم</h3>
            <table className="w-full">
              <thead><tr className="table-header"><th className="px-4 py-2 text-right text-xs">الحساب</th><th className="px-4 py-2 text-right text-xs">الرصيد</th></tr></thead>
              <tbody>{liabilities.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-2 text-sm">{item.account_name}</td><td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.balance)}</td></tr>)}</tbody>
            </table>
          </div>
          <div className="card p-0 overflow-hidden">
            <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-zinc-700">حقوق الملكية</h3>
            <table className="w-full">
              <thead><tr className="table-header"><th className="px-4 py-2 text-right text-xs">الحساب</th><th className="px-4 py-2 text-right text-xs">الرصيد</th></tr></thead>
              <tbody>{equity.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-2 text-sm">{item.account_name}</td><td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.balance)}</td></tr>)}</tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const renderIncomeStatement = () => {
    const revenues = data?.revenue?.accounts || data?.revenues || [];
    const expenses = data?.expenses?.accounts || data?.expenses || [];
    const netIncome = data?.net_income || 0;
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card p-0 overflow-hidden">
          <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-zinc-700">الإيرادات</h3>
          <table className="w-full">
            <thead><tr className="table-header"><th className="px-4 py-2 text-right text-xs">الحساب</th><th className="px-4 py-2 text-right text-xs">المبلغ</th></tr></thead>
            <tbody>{revenues.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-2 text-sm">{item.account_name}</td><td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.amount)}</td></tr>)}</tbody>
          </table>
        </div>
        <div className="card p-0 overflow-hidden">
          <h3 className="text-lg font-semibold p-4 border-b border-gray-200 dark:border-zinc-700">المصروفات</h3>
          <table className="w-full">
            <thead><tr className="table-header"><th className="px-4 py-2 text-right text-xs">الحساب</th><th className="px-4 py-2 text-right text-xs">المبلغ</th></tr></thead>
            <tbody>{expenses.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-2 text-sm">{item.account_name}</td><td className="px-4 py-2 text-sm font-medium">{formatCurrency(item.amount)}</td></tr>)}</tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderCashFlow = () => {
    let items = data?.items || data?.cash_flows || [];
    if (!items.length && data?.operating_activities) {
      items = [
        { description: 'الأنشطة التشغيلية', amount: data.operating_activities.net },
        { description: '  إيرادات تشغيلية', amount: data.operating_activities.inflows },
        { description: '  مدفوعات تشغيلية', amount: -Math.abs(data.operating_activities.outflows) },
        { description: 'الأنشطة الاستثمارية', amount: data.investing_activities?.net || 0 },
        { description: '  إيرادات استثمارية', amount: data.investing_activities?.inflows || 0 },
        { description: '  مدفوعات استثمارية', amount: -Math.abs(data.investing_activities?.outflows || 0) },
        { description: 'الأنشطة التمويلية', amount: data.financing_activities?.net || 0 },
        { description: '  إيرادات تمويلية', amount: data.financing_activities?.inflows || 0 },
        { description: '  مدفوعات تمويلية', amount: -Math.abs(data.financing_activities?.outflows || 0) },
      ];
    }
    return (
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead><tr className="table-header"><th className="px-4 py-3 text-right text-xs">البيان</th><th className="px-4 py-3 text-right text-xs">المبلغ</th></tr></thead>
          <tbody>{items.map((item: any, i: number) => <tr key={i} className="table-row"><td className="px-4 py-3 text-sm">{item.description || item.account_name}</td><td className="px-4 py-3 text-sm font-medium">{formatCurrency(item.amount || item.balance)}</td></tr>)}</tbody>
        </table>
      </div>
    );
  };

  const renderEquityChanges = () => {
    const items = data?.items || data?.accounts || data?.sections || [];    return (
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead><tr className="table-header">
            <th className="px-4 py-3 text-right text-xs">الحساب</th>
            <th className="px-4 py-3 text-right text-xs">الافتتاحي</th>
            <th className="px-4 py-3 text-right text-xs">الزيادات</th>
            <th className="px-4 py-3 text-right text-xs">الخصوم</th>
            <th className="px-4 py-3 text-right text-xs">الختامي</th>
          </tr></thead>
          <tbody>
            {items.map((item: any, i: number) => (
              <tr key={i} className="table-row">
                <td className="px-4 py-3 text-sm">{item.account_name}</td>
                <td className="px-4 py-3 text-sm font-medium">{formatCurrency(item.opening_balance || item.opening || 0)}</td>
                <td className="px-4 py-3 text-sm font-medium text-emerald-600">{formatCurrency(item.increases || 0)}</td>
                <td className="px-4 py-3 text-sm font-medium text-red-600">{formatCurrency(item.decreases || 0)}</td>
                <td className="px-4 py-3 text-sm font-medium">{formatCurrency(item.closing_balance || item.closing || 0)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="bg-gray-50 dark:bg-zinc-800 font-bold">
              <td className="px-4 py-3 text-sm">الإجمالي</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(items.reduce((s: number, it: any) => s + (it.opening_balance || it.opening || 0), 0))}</td>
              <td className="px-4 py-3 text-sm text-emerald-600">{formatCurrency(items.reduce((s: number, it: any) => s + (it.increases || 0), 0))}</td>
              <td className="px-4 py-3 text-sm text-red-600">{formatCurrency(items.reduce((s: number, it: any) => s + (it.decreases || 0), 0))}</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(items.reduce((s: number, it: any) => s + (it.closing_balance || it.closing || 0), 0))}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    );
  };

  const renderComparative = () => {
    const items = data?.items || data?.rows || data?.comparison || [];
    return (
      <div className="space-y-4">
        <div className="flex items-center gap-4">
          <div>
            <label className="text-sm text-gray-600 dark:text-zinc-400">نوع التقرير:</label>
            <select value={compReportType} onChange={(e) => setCompReportType(e.target.value)} className="input w-auto mr-2">
              <option value="income-statement">قائمة الدخل</option>
              <option value="balance-sheet">الميزانية العمومية</option>
            </select>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 dark:text-zinc-400">الفترة 1:</label>
            <input type="date" value={p1From} onChange={(e) => setP1From(e.target.value)} className="input w-auto" />
            <span className="text-gray-400">-</span>
            <input type="date" value={p1To} onChange={(e) => setP1To(e.target.value)} className="input w-auto" />
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 dark:text-zinc-400">الفترة 2:</label>
            <input type="date" value={p2From} onChange={(e) => setP2From(e.target.value)} className="input w-auto" />
            <span className="text-gray-400">-</span>
            <input type="date" value={p2To} onChange={(e) => setP2To(e.target.value)} className="input w-auto" />
          </div>
        </div>
        <div className="card p-0 overflow-hidden">
          <table className="w-full">
            <thead><tr className="table-header">
              <th className="px-4 py-3 text-right text-xs">البند</th>
              <th className="px-4 py-3 text-right text-xs">الفترة الأولى</th>
              <th className="px-4 py-3 text-right text-xs">الفترة الثانية</th>
              <th className="px-4 py-3 text-right text-xs">الفرق</th>
              <th className="px-4 py-3 text-right text-xs">الفرق %</th>
            </tr></thead>
            <tbody>
              {items.map((item: any, i: number) => {
                const diff = (item.period2 || 0) - (item.period1 || 0);
                const pct = item.period1 ? ((diff / item.period1) * 100) : 0;
                return (
                  <tr key={i} className="table-row">
                    <td className="px-4 py-3 text-sm">{item.label || item.account_name}</td>
                    <td className="px-4 py-3 text-sm font-medium">{formatCurrency(item.period1 || 0)}</td>
                    <td className="px-4 py-3 text-sm font-medium">{formatCurrency(item.period2 || 0)}</td>
                    <td className={`px-4 py-3 text-sm font-medium ${diff > 0 ? 'text-emerald-600' : diff < 0 ? 'text-red-600' : ''}`}>{formatCurrency(diff)}</td>
                    <td className={`px-4 py-3 text-sm font-medium ${pct > 0 ? 'text-emerald-600' : pct < 0 ? 'text-red-600' : ''}`}>{pct.toFixed(1)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader title="القوائم المالية" subtitle="عرض القوائم المالية والإقارنات" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>} actions={<>
          <div className="flex items-center gap-3">
            <label className="text-sm text-gray-600 dark:text-zinc-400">من:</label>
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="input w-auto" />
            <label className="text-sm text-gray-600 dark:text-zinc-400">إلى:</label>
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="input w-auto" />
          </div>
          {(activeTab === 'balance-sheet' || activeTab === 'income-statement' || activeTab === 'cash-flow') && (
            (() => {
              const isBs = activeTab === 'balance-sheet';
              return (
                <ExcelExportButton
                  url={isBs ? '/excel/exports/balance-sheet' : activeTab === 'income-statement' ? '/excel/exports/income-statement' : '/excel/exports/cash-flow'}
                  params={isBs ? { as_of_date: fromDate } : { period_start: fromDate, period_end: toDate }}
                  filename={isBs ? `balance-sheet-${fromDate}.xlsx` : `${activeTab}-${fromDate}-${toDate}.xlsx`}
                  label={isBs ? 'تصدير الميزانية' : activeTab === 'income-statement' ? 'تصدير قائمة الدخل' : 'تصدير التدفقات'}
                />
              );
            })()
          )}
          <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            طباعة / PDF
          </button>
        </>} />

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'balance-sheet' && renderBalanceSheet()}
      {activeTab === 'income-statement' && renderIncomeStatement()}
      {activeTab === 'cash-flow' && renderCashFlow()}
      {activeTab === 'equity-changes' && renderEquityChanges()}
      {activeTab === 'comparative' && renderComparative()}

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title={tabs.find((t) => t.key === activeTab)?.label || 'القوائم المالية'}
        filename={`القوائم-المالية-${activeTab}`}
      >
        <PrintDocument company={company} title={tabs.find((t) => t.key === activeTab)?.label || 'القوائم المالية'} meta={[
          { label: 'الفترة من', value: formatDate(fromDate) },
          { label: 'إلى', value: formatDate(toDate) },
        ]}>
          {activeTab === 'balance-sheet' && (
            <div className="grid grid-cols-2 gap-6 text-sm">
              <div>
                <h3 className="font-bold text-gray-900 mb-2">الأصول</h3>
                <table className="w-full">
                  <tbody>
                    {(data?.assets?.accounts || []).map((item: any, i: number) => (
                      <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.balance)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="space-y-6">
                <div>
                  <h3 className="font-bold text-gray-900 mb-2">الخصوم</h3>
                  <table className="w-full">
                    <tbody>
                      {(data?.liabilities?.accounts || []).map((item: any, i: number) => (
                        <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.balance)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div>
                  <h3 className="font-bold text-gray-900 mb-2">حقوق الملكية</h3>
                  <table className="w-full">
                    <tbody>
                      {(data?.equity?.accounts || []).map((item: any, i: number) => (
                        <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.balance)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'income-statement' && (
            <div className="grid grid-cols-2 gap-6 text-sm">
              <div>
                <h3 className="font-bold text-gray-900 mb-2">الإيرادات</h3>
                <table className="w-full">
                  <tbody>
                    {(data?.revenue?.accounts || data?.revenues || []).map((item: any, i: number) => (
                      <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.amount)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h3 className="font-bold text-gray-900 mb-2">المصروفات</h3>
                <table className="w-full">
                  <tbody>
                    {(data?.expenses?.accounts || data?.expenses || []).map((item: any, i: number) => (
                      <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.amount)}</td></tr>
                    ))}
                  </tbody>
                </table>
                <div className="flex justify-between font-bold mt-4 pt-2 border-t-2 border-gray-800">
                  <span>صافي الدخل</span>
                  <span>{formatCurrency(data?.net_income || 0)}</span>
                </div>
              </div>
            </div>
          )}
          {activeTab === 'cash-flow' && (
            <table className="w-full text-sm">
              <tbody>
                {(data?.items || data?.cash_flows || []).map((item: any, i: number) => (
                  <tr key={i}><td className="py-1.5 border-b border-gray-200">{item.description || item.account_name}</td><td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.amount || item.balance)}</td></tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'equity-changes' && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-300">
                  <th className="py-1.5 text-right font-semibold">الحساب</th>
                  <th className="py-1.5 text-right font-semibold">الافتتاحي</th>
                  <th className="py-1.5 text-right font-semibold">الزيادات</th>
                  <th className="py-1.5 text-right font-semibold">الخصوم</th>
                  <th className="py-1.5 text-right font-semibold">الختامي</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items || data?.accounts || data?.sections || []).map((item: any, i: number) => (
                  <tr key={i}>
                    <td className="py-1.5 border-b border-gray-200">{item.account_name}</td>
                    <td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.opening_balance || item.opening || 0)}</td>
                    <td className="py-1.5 border-b border-gray-200 font-medium text-left text-emerald-600">{formatCurrency(item.increases || 0)}</td>
                    <td className="py-1.5 border-b border-gray-200 font-medium text-left text-red-600">{formatCurrency(item.decreases || 0)}</td>
                    <td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.closing_balance || item.closing || 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {activeTab === 'comparative' && (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b-2 border-gray-300">
                  <th className="py-1.5 text-right font-semibold">البند</th>
                  <th className="py-1.5 text-right font-semibold">الفترة الأولى</th>
                  <th className="py-1.5 text-right font-semibold">الفترة الثانية</th>
                  <th className="py-1.5 text-right font-semibold">الفرق</th>
                  <th className="py-1.5 text-right font-semibold">الفرق %</th>
                </tr>
              </thead>
              <tbody>
                {(data?.items || data?.rows || data?.comparison || []).map((item: any, i: number) => {
                  const diff = (item.period2 || 0) - (item.period1 || 0);
                  const pct = item.period1 ? ((diff / item.period1) * 100) : 0;
                  return (
                    <tr key={i}>
                      <td className="py-1.5 border-b border-gray-200">{item.label || item.account_name}</td>
                      <td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.period1 || 0)}</td>
                      <td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(item.period2 || 0)}</td>
                      <td className="py-1.5 border-b border-gray-200 font-medium text-left">{formatCurrency(diff)}</td>
                      <td className="py-1.5 border-b border-gray-200 font-medium text-left">{pct.toFixed(1)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
