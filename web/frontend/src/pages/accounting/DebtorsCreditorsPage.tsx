import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getDebtorsCreditors } from '@/api/agingReports';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageHeader } from '@/components/ui/PageHeader';

const fmt = (n: number | string | undefined | null) =>
  (Number(n ?? 0)).toLocaleString(undefined, { maximumFractionDigits: 2 });

export default function DebtorsCreditorsPage() {
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [showAll, setShowAll] = useState(false);

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['debtors-creditors', asOfDate],
    queryFn: () => getDebtorsCreditors(asOfDate),
  });

  const debtors = (showAll ? data?.debtors?.items : (data?.debtors?.items || []).filter((i: any) => i.outstanding > 0)) || [];
  const creditors = (showAll ? data?.creditors?.items : (data?.creditors?.items || []).filter((i: any) => i.outstanding > 0)) || [];

  const netContractual = (data?.debtors?.total ?? 0) - (data?.creditors?.total ?? 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="المدينون والدائنون"
        subtitle="مركز الذمم الموحد — المدينون (العملاء) والدائنون (الموردون) مع مطابقة دفترية من الأستاذ العام"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
        actions={
          <div className="flex items-center gap-2">
            <label className="text-sm font-medium">حتى تاريخ:</label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="border rounded-lg px-3 py-2 dark:bg-zinc-800"
            />
            <button onClick={() => setShowAll(!showAll)} className="btn-secondary btn-sm">
              {showAll ? 'إخفاء الأرصدة الصفرية' : 'عرض الكل'}
            </button>
          </div>
        }
      />

      {/* Summary cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsCard title="إجمالي المدينين" value={fmt(data?.debtors?.total)} color="red" icon={null as any} />
        <StatsCard title="إجمالي الدائنين" value={fmt(data?.creditors?.total)} color="blue" icon={null as any} />
        <StatsCard title="الفرق (مدينون − دائنون)" value={fmt(netContractual)} color="purple" icon={null as any} />
        <StatsCard
          title="المركز الدفتري الصافي"
          value={fmt(data?.ledger?.net_position)}
          color="green"
          icon={null as any}
          footer={<span className="text-xs text-gray-400 dark:text-zinc-500">1201 − 2111 (من القيود المرحلة)</span>}
        />
      </div>

      {/* Ledger reconciliation */}
      {(data?.ledger?.ar_balance !== undefined) && (
        <div className="card p-4">
          <h3 className="font-bold mb-3 text-sm text-gray-600 dark:text-zinc-300">المطابقة مع الدفتر (مدين/دائن)</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="flex items-center justify-between border rounded-lg px-4 py-3">
              <span className="text-gray-500 dark:text-zinc-400">الذمم المدينة من الدفتر (1201)</span>
              <span className="font-bold text-red-600 dark:text-red-400">{fmt(data.ledger.ar_balance)}</span>
            </div>
            <div className="flex items-center justify-between border rounded-lg px-4 py-3">
              <span className="text-gray-500 dark:text-zinc-400">الذمم الدائنة من الدفتر (2111)</span>
              <span className="font-bold text-blue-600 dark:text-blue-400">{fmt(data.ledger.ap_balance)}</span>
            </div>
            <div className="flex items-center justify-between border rounded-lg px-4 py-3 bg-emerald-50 dark:bg-emerald-500/10">
              <span className="text-gray-600 dark:text-zinc-300 font-medium">صافي المركز</span>
              <span className="font-bold">{fmt(data.ledger.net_position)}</span>
            </div>
          </div>
        </div>
      )}

      {/* Debtors table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-bold">المدينون — الذمم المدينة عن العملاء</h3>
          <span className="text-sm text-gray-500 dark:text-zinc-400">{debtors.length} طرف</span>
        </div>
        <table className="w-full">
          <thead className="table-header">
            <tr>
              <th className="px-4 py-3 text-right">الطرف</th>
              <th className="px-4 py-3 text-right">الكود</th>
              <th className="px-4 py-3 text-right">الرصيد المستحق</th>
            </tr>
          </thead>
          <tbody>
            {debtors.map((c: any) => (
              <tr key={c.id} className="table-row">
                <td className="px-4 py-3">{c.name}</td>
                <td className="px-4 py-3">{c.code || '—'}</td>
                <td className="px-4 py-3 font-medium text-red-600 dark:text-red-400">{fmt(c.outstanding)}</td>
              </tr>
            ))}
            {debtors.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-500">لا يوجد مدينون حالياً</td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="font-bold border-t-2 bg-gray-50 dark:bg-zinc-800">
              <td className="px-4 py-3" colSpan={2}>الإجمالي</td>
              <td className="px-4 py-3 text-red-600 dark:text-red-400">{fmt(data?.debtors?.total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {/* Creditors table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b">
          <h3 className="font-bold">الدائنون — الذمم الدائنة عن الموردين</h3>
          <span className="text-sm text-gray-500 dark:text-zinc-400">{creditors.length} طرف</span>
        </div>
        <table className="w-full">
          <thead className="table-header">
            <tr>
              <th className="px-4 py-3 text-right">الطرف</th>
              <th className="px-4 py-3 text-right">الكود</th>
              <th className="px-4 py-3 text-right">الرصيد المستحق</th>
            </tr>
          </thead>
          <tbody>
            {creditors.map((s: any) => (
              <tr key={s.id} className="table-row">
                <td className="px-4 py-3">{s.name}</td>
                <td className="px-4 py-3">{s.code || '—'}</td>
                <td className="px-4 py-3 font-medium text-blue-600 dark:text-blue-400">{fmt(s.outstanding)}</td>
              </tr>
            ))}
            {creditors.length === 0 && (
              <tr>
                <td colSpan={3} className="px-4 py-8 text-center text-gray-500">لا يوجد دائنون حالياً</td>
              </tr>
            )}
          </tbody>
          <tfoot>
            <tr className="font-bold border-t-2 bg-gray-50 dark:bg-zinc-800">
              <td className="px-4 py-3" colSpan={2}>الإجمالي</td>
              <td className="px-4 py-3 text-blue-600 dark:text-blue-400">{fmt(data?.creditors?.total)}</td>
            </tr>
          </tfoot>
        </table>
      </div>

      {isLoading && <div className="text-center py-8 text-gray-600 dark:text-zinc-400">جاري التحميل...</div>}
      {isError && (
        <div className="text-center py-8">
          <p className="text-danger-600 dark:text-danger-400 mb-3">تعذر تحميل التقرير</p>
          <button onClick={() => refetch()} className="btn-primary">إعادة المحاولة</button>
        </div>
      )}
    </div>
  );
}