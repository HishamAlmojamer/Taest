import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTrialBalance } from '@/api/accounting';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate, cn } from '@/lib/utils';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { PageHeader } from '@/components/ui/PageHeader';
import { StatsCard } from '@/components/ui/StatsCard';
import ExcelExportButton from '@/components/excel/ExcelExportButton';

const typeMeta: Record<string, { label: string; badge: string }> = {
  asset: { label: 'أصل', badge: 'bg-blue-100 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400' },
  liability: { label: 'التزام', badge: 'bg-red-100 text-red-700 dark:bg-red-500/15 dark:text-red-400' },
  equity: { label: 'حقوق ملكية', badge: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400' },
  revenue: { label: 'إيراد', badge: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-500/15 dark:text-yellow-400' },
  expense: { label: 'مصروف', badge: 'bg-purple-100 text-purple-700 dark:bg-purple-500/15 dark:text-purple-400' },
};

function TypeBadge({ type }: { type?: string }) {
  const t = (type || '').toLowerCase();
  const meta = typeMeta[t] || { label: type || '—', badge: 'bg-gray-100 text-gray-600 dark:bg-zinc-700 dark:text-zinc-300' };
  return (
    <span className={cn('inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap', meta.badge)}>
      {meta.label}
    </span>
  );
}

export default function TrialBalancePage() {
  const company = useCompany();
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [search, setSearch] = useState('');
  const [accountType, setAccountType] = useState('');
  const [showPrint, setShowPrint] = useState(false);

  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['trial-balance', date, search, accountType],
    queryFn: () => getTrialBalance({ date, search: search || undefined, account_type: accountType || undefined }),
  });

  if (isLoading) return <PageLoader />;
  if (isError) {
    return (
      <div className="space-y-6">
        <PageHeader title="ميزان المراجعة" subtitle="تقرير ميزان المراجعة للحسابات" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} />
        <div className="card p-10 text-center">
          <p className="text-red-600 dark:text-red-400 font-medium mb-3">تعذر تحميل ميزان المراجعة</p>
          <button onClick={() => refetch()} className="btn-primary">إعادة المحاولة</button>
        </div>
      </div>
    );
  }

  const accounts = (data?.accounts || []) as any[];
  const totalDebit = data?.totalDebit || 0;
  const totalCredit = data?.totalCredit || 0;
  const isBalanced = data?.isBalanced ?? Math.abs(totalDebit - totalCredit) < 0.01;

  return (
    <div className="space-y-6">
      <PageHeader title="ميزان المراجعة" subtitle="عرض ميزان المراجعة للحسابات حتى تاريخ محدد" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} actions={<>
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm text-gray-600 dark:text-zinc-400">بتاريخ:</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="input w-auto" />
          <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2" disabled={accounts.length === 0}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            طباعة / PDF
          </button>
          <ExcelExportButton url="/excel/exports/trial-balance" params={{ date, account_type: accountType || undefined }} filename={`trial-balance-${date}.xlsx`} />
        </div>
      </>} />

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatsCard title="إجمالي المدين" value={totalDebit} currency color="blue" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1"></path></svg>} />
        <StatsCard title="إجمالي الدائن" value={totalCredit} currency color="red" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c1.657 0 3 .895 3 2s-1.343 2-3 2-3 .895-3 2 1.343 2 3 2m0-8c-1.11 0-2.08.402-2.599 1M12 8V7m0 1v8m0 0v1m0-1c1.11 0 2.08-.402 2.599 1"></path></svg>} />
        <StatsCard title="عدد الحسابات" value={accounts.length} color="purple" icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"></path></svg>} />
        <StatsCard
          title="حالة التوازن"
          value={isBalanced ? 'متوازن' : 'غير متوازن'}
          color={isBalanced ? 'green' : 'red'}
          icon={
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              {isBalanced ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
              )}
            </svg>
          }
          footer={<span className="text-xs">{formatCurrency(isBalanced ? 0 : Math.abs(totalDebit - totalCredit))} فرق</span>}
        />
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-col sm:flex-row gap-3">
        <div className="flex-1">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث بكود أو اسم الحساب..."
            className="input w-full"
          />
        </div>
        <select value={accountType} onChange={(e) => setAccountType(e.target.value)} className="input w-full sm:w-56">
          <option value="">كل الأنواع</option>
          <option value="asset">أصول</option>
          <option value="liability">التزامات</option>
          <option value="equity">حقوق ملكية</option>
          <option value="revenue">إيرادات</option>
          <option value="expense">مصروفات</option>
        </select>
      </div>

      <div className="card p-0 overflow-hidden">
        {isFetching && <div className="px-4 py-2 text-xs text-gray-400 animate-pulse">جارِ التحديث...</div>}
        <table className="w-full">
          <thead>
            <tr className="table-header">
              <th className="px-4 py-3 text-right text-xs">كود الحساب</th>
              <th className="px-4 py-3 text-right text-xs">اسم الحساب</th>
              <th className="px-4 py-3 text-right text-xs">النوع</th>
              <th className="px-4 py-3 text-right text-xs">رصيد افتتاحي</th>
              <th className="px-4 py-3 text-right text-xs">مدين</th>
              <th className="px-4 py-3 text-right text-xs">دائن</th>
              <th className="px-4 py-3 text-right text-xs">الرصيد</th>
            </tr>
          </thead>
          <tbody>
            {accounts.length === 0 && (
              <tr>
                <td colSpan={7} className="px-4 py-8 text-center text-sm text-gray-400">لا توجد حسابات مطابقة</td>
              </tr>
            )}
            {accounts.map((row: any, idx: number) => {
              return (
                <tr key={row.accountId ?? idx} className="table-row">
                  <td className="px-4 py-3 text-sm font-mono">{row.accountCode}</td>
                  <td className="px-4 py-3 text-sm font-medium">{row.accountName}</td>
                  <td className="px-4 py-3"><TypeBadge type={row.accountType} /></td>
                  <td className="px-4 py-3 text-sm">{formatCurrency(row.openingBalance || 0)}</td>
                  <td className="px-4 py-3 text-sm">{formatCurrency(row.debit || 0)}</td>
                  <td className="px-4 py-3 text-sm">{formatCurrency(row.credit || 0)}</td>
                  <td className={cn('px-4 py-3 text-sm font-semibold', (row.netBalance || 0) < 0 ? 'text-red-600' : 'text-gray-900 dark:text-zinc-100')}>
                    {formatCurrency(row.netBalance || 0)}
                  </td>
                </tr>
              );
            })}
            <tr className="bg-gray-50 dark:bg-zinc-800 font-bold">
              <td className="px-4 py-3 text-sm" colSpan={3}>الإجمالي</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(0)}</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(totalDebit)}</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(totalCredit)}</td>
              <td className="px-4 py-3 text-sm">
                {isBalanced
                  ? <span className="text-green-600">متوازن</span>
                  : <span className="text-red-600">فرق {formatCurrency(Math.abs(totalDebit - totalCredit))}</span>}
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title="ميزان المراجعة"
        filename={`ميزان-المراجعة-${date}`}
      >
        <PrintDocument company={company} title="ميزان المراجعة" meta={[
          { label: 'بتاريخ', value: formatDate(date) },
          ...(search ? [{ label: 'بحث', value: search }] : []),
        ]}>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">كود الحساب</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">اسم الحساب</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">نوع</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">رصيد افتتاحي</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">مدين</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">دائن</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الرصيد</th>
              </tr>
            </thead>
            <tbody>
              {accounts.map((row: any, idx: number) => (
                <tr key={row.accountId ?? idx}>
                  <td className="px-3 py-2 border border-gray-300 font-mono">{row.accountCode}</td>
                  <td className="px-3 py-2 border border-gray-300 font-medium">{row.accountName}</td>
                  <td className="px-3 py-2 border border-gray-300">{(typeMeta[(row.accountType || '').toLowerCase()] || {}).label || row.accountType}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(row.openingBalance || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(row.debit || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(row.credit || 0)}</td>
                  <td className="px-3 py-2 border border-gray-300 font-medium">{formatCurrency(row.netBalance || 0)}</td>
                </tr>
              ))}
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={3}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(0)}</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(totalDebit)}</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(totalCredit)}</td>
                <td className="px-3 py-2 border border-gray-300">{isBalanced ? 'متوازن' : `فرق ${formatCurrency(Math.abs(totalDebit - totalCredit))}`}</td>
              </tr>
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
