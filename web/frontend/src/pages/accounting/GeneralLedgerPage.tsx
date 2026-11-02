import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getGeneralLedger, getAccountsFlat } from '@/api/accounting';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatsCard } from '@/components/ui/StatsCard';
import { Modal } from '@/components/ui/Modal';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { PageHeader } from '@/components/ui/PageHeader';
import ExcelExportButton from '@/components/excel/ExcelExportButton';

const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

export default function GeneralLedgerPage() {
  const company = useCompany();
  const [accountId, setAccountId] = useState<number | ''>('');
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');
  const [partnerId, setPartnerId] = useState<string>('');
  const [showPrint, setShowPrint] = useState(false);
  const [searched, setSearched] = useState(false);

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts-flat'],
    queryFn: () => getAccountsFlat(),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['general-ledger', accountId, fromDate, toDate, partnerId],
    queryFn: () => getGeneralLedger({ account_id: accountId as number, from_date: fromDate, to_date: toDate, partner_id: partnerId ? Number(partnerId) : undefined }),
    enabled: false,
  });

  const transactions = data?.transactions || [];
  const openingBalance = data?.openingBalanceForPeriod ?? 0;
  const closingBalance = data?.closingBalance ?? 0;
  const totalDebit = transactions.reduce((s: number, t: any) => s + Number(t.debit || 0), 0);
  const totalCredit = transactions.reduce((s: number, t: any) => s + Number(t.credit || 0), 0);

  const handleSearch = () => {
    if (!accountId) return;
    setSearched(true);
    refetch();
  };

  return (
    <div className="space-y-6">
      <PageHeader title="دفتر الأستاذ العام" subtitle="عرض تفاصيل حسابات الأستاذ العام" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} actions={<>
          {searched && transactions.length > 0 && (
            <>
              <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2">
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
                طباعة / PDF
              </button>
              <ExcelExportButton
                url="/excel/exports/general-ledger"
                params={{
                  account_id: accountId as number,
                  from_date: fromDate || undefined,
                  to_date: toDate || undefined,
                }}
                filename={`general-ledger-${accountId}.xlsx`}
              />
            </>
          )}
        </>} />

      {/* Filter Card */}
      <div className="card p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="label">الحساب *</label>
            <select value={accountId} onChange={(e) => setAccountId(e.target.value ? Number(e.target.value) : '')} className={inputClass}>
              <option value="">اختر الحساب</option>
              {(accounts as any[]).map((acc: any) => (
                <option key={acc.id} value={acc.id}>{acc.code} - {acc.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">من تاريخ</label>
            <input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="label">إلى تاريخ</label>
            <input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className={inputClass} />
          </div>
          <div>
            <label className="label">معرف الشريك (اختياري)</label>
            <input type="number" value={partnerId} onChange={(e) => setPartnerId(e.target.value)} placeholder="partner_id" className={inputClass} />
          </div>
          <div className="flex items-end">
            <button onClick={handleSearch} disabled={!accountId || isLoading} className="btn-primary w-full disabled:opacity-50">
              {isLoading ? 'جاري التحميل...' : 'عرض'}
            </button>
          </div>
        </div>
      </div>

      {/* Stats */}
      {searched && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <StatsCard title="الرصيد الافتتاحي" value={openingBalance} currency color="blue" />
          <StatsCard title="إجمالي المدين" value={totalDebit} currency color="green" />
          <StatsCard title="إجمالي الدائن" value={totalCredit} currency color="red" />
        </div>
      )}

      {/* Transactions Table */}
      {searched && !isLoading && (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="table-header">
                  <th className="px-4 py-3 text-right text-xs font-semibold">التاريخ</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">رقم القيد</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">الوصف</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">الشريك</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">المشروع</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">مدين</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">دائن</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold">الرصيد الجاري</th>
                </tr>
              </thead>
              <tbody>
                <tr className="table-row bg-gray-50 dark:bg-zinc-800/50">
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400" colSpan={7}>الرصيد الافتتاحي</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-zinc-100">{formatCurrency(openingBalance)}</td>
                </tr>
                {transactions.map((tx: any, idx: number) => (
                  <tr key={tx.id || idx} className="table-row">
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{formatDate(tx.entryDate || tx.entry_date)}</td>
                    <td className="px-4 py-3 text-sm font-medium text-primary-600 dark:text-primary-400">{String(tx.entryNumber || tx.entry_number || '')}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{String(tx.description || '')}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{tx.partner_name ? String(tx.partner_name) : (tx.partnerId ? `#${tx.partnerId}` : '-')}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{tx.projectId ? String(tx.projectId) : '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-zinc-100">{Number(tx.debit || 0) > 0 ? formatCurrency(Number(tx.debit)) : '-'}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-zinc-100">{Number(tx.credit || 0) > 0 ? formatCurrency(Number(tx.credit)) : '-'}</td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-zinc-100">{formatCurrency(Number(tx.runningBalance || tx.running_balance || 0))}</td>
                  </tr>
                ))}
                {transactions.length === 0 && (
                  <tr>
                    <td colSpan={8} className="px-4 py-10 text-center text-gray-400 dark:text-zinc-500">
                      لا توجد معاملات في الفترة المحددة.
                    </td>
                  </tr>
                )}
                {transactions.length > 0 && (
                  <tr className="bg-gray-50 dark:bg-zinc-800/50 font-bold">
                    <td className="px-4 py-3 text-sm" colSpan={5}>الإجمالي</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-zinc-100">{formatCurrency(totalDebit)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-zinc-100">{formatCurrency(totalCredit)}</td>
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-zinc-100">
                      الرصيد الختامي: {formatCurrency(closingBalance)}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Print Modal */}
      <PrintPreviewModal isOpen={showPrint} onClose={() => setShowPrint(false)} title="دفتر الأستاذ العام" filename="دفتر-الأستاذ-العام">
        <PrintDocument company={company} title="تقرير دفتر الأستاذ العام" meta={[
          { label: 'الحساب', value: (accounts as any[]).find((a: any) => String(a.id) === accountId)?.name || '' },
          { label: 'من تاريخ', value: fromDate || '-' },
          { label: 'إلى تاريخ', value: toDate || '-' },
        ]}>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">التاريخ</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">رقم القيد</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الوصف</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الشريك</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المشروع</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">مدين</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">دائن</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الرصيد الجاري</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="px-3 py-2 border border-gray-300" colSpan={7}>الرصيد الافتتاحي</td>
                <td className="px-3 py-2 border border-gray-300 font-bold">{formatCurrency(openingBalance)}</td>
              </tr>
              {transactions.map((tx: any, idx: number) => (
                <tr key={tx.id || idx}>
                  <td className="px-3 py-2 border border-gray-300">{formatDate(tx.entryDate || tx.entry_date)}</td>
                  <td className="px-3 py-2 border border-gray-300 font-mono">{String(tx.entryNumber || tx.entry_number || '')}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(tx.description || '')}</td>
                  <td className="px-3 py-2 border border-gray-300">{tx.partner_name ? String(tx.partner_name) : (tx.partnerId ? `#${tx.partnerId}` : '-')}</td>
                  <td className="px-3 py-2 border border-gray-300">{tx.projectId ? String(tx.projectId) : '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{Number(tx.debit || 0) > 0 ? formatCurrency(Number(tx.debit)) : '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{Number(tx.credit || 0) > 0 ? formatCurrency(Number(tx.credit)) : '-'}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(Number(tx.runningBalance || tx.running_balance || 0))}</td>
                </tr>
              ))}
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={5}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(totalDebit)}</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency(totalCredit)}</td>
                <td className="px-3 py-2 border border-gray-300">الرصيد الختامي: {formatCurrency(closingBalance)}</td>
              </tr>
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
