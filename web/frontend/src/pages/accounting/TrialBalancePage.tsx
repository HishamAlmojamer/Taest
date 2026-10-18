import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getTrialBalance } from '@/api/accounting';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency } from '@/lib/utils';

export default function TrialBalancePage() {
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const { data, isLoading } = useQuery({
    queryKey: ['trial-balance', date],
    queryFn: () => getTrialBalance({ date }),
  });

  if (isLoading) return <PageLoader />;

  const accounts = data?.accounts || [];
  const totalDebit = data?.totalDebit || 0;
  const totalCredit = data?.totalCredit || 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">ميزان المراجعة</h1>
        <div className="flex items-center gap-3">
          <label className="text-sm text-gray-600 dark:text-zinc-400">بتاريخ:</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="input w-auto" />
        </div>
      </div>
      <div className="card p-0 overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="table-header">
              <th className="px-4 py-3 text-right text-xs">كود الحساب</th>
              <th className="px-4 py-3 text-right text-xs">اسم الحساب</th>
              <th className="px-4 py-3 text-right text-xs">مدين</th>
              <th className="px-4 py-3 text-right text-xs">دائن</th>
              <th className="px-4 py-3 text-right text-xs">الرصيد</th>
            </tr>
          </thead>
          <tbody>
            {accounts.map((row: any, idx: number) => (
              <tr key={idx} className="table-row">
                <td className="px-4 py-3 text-sm font-mono">{row.accountCode}</td>
                <td className="px-4 py-3 text-sm font-medium">{row.accountName}</td>
                <td className="px-4 py-3 text-sm">{row.debit > 0 ? formatCurrency(row.debit) : '-'}</td>
                <td className="px-4 py-3 text-sm">{row.credit > 0 ? formatCurrency(row.credit) : '-'}</td>
                <td className="px-4 py-3 text-sm font-medium">{formatCurrency(row.netBalance)}</td>
              </tr>
            ))}
            <tr className="bg-gray-50 dark:bg-zinc-800 font-bold">
              <td className="px-4 py-3 text-sm" colSpan={2}>الإجمالي</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(totalDebit)}</td>
              <td className="px-4 py-3 text-sm">{formatCurrency(totalCredit)}</td>
              <td className="px-4 py-3 text-sm">{totalDebit === totalCredit ? <span className="text-green-600">متوازن</span> : <span className="text-red-600">غير متوازن</span>}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
