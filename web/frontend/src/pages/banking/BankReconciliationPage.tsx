import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getReconciliations,
  createReconciliation,
  getReconciliation,
  getUnmatchedTransactions,
  matchTransaction,
  unmatchTransaction,
  completeReconciliation,
} from '@/api/bankReconciliation';
import { getBanks } from '@/api/payments';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { cn } from '@/lib/utils';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { Bank } from '@/api/payments';

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'مسودة', IN_PROGRESS: 'قيد التنفيذ', COMPLETED: 'مكتمل', CANCELLED: 'ملغي',
};
const STATUS_COLORS: Record<string, string> = {
  DRAFT: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-500/20 dark:text-yellow-400',
  IN_PROGRESS: 'bg-blue-100 text-blue-800 dark:bg-blue-500/20 dark:text-blue-400',
  COMPLETED: 'bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400',
  CANCELLED: 'bg-red-100 text-red-800 dark:bg-red-500/20 dark:text-red-400',
};

export default function BankReconciliationPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [selectedBank, setSelectedBank] = useState<number | ''>('');
  const [selectedRecId, setSelectedRecId] = useState<number | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);

  // ── Queries ──
  const { data: banksData } = useQuery({
    queryKey: ['banks'],
    queryFn: getBanks,
  });
  const banks: Bank[] = banksData?.items || [];

  const { data: reconciliations, isLoading: loadingRecs } = useQuery({
    queryKey: ['reconciliations', selectedBank],
    queryFn: () => getReconciliations(selectedBank as number || undefined),
  });

  const { data: recDetail, isLoading: loadingDetail } = useQuery({
    queryKey: ['reconciliation', selectedRecId],
    queryFn: () => getReconciliation(selectedRecId!),
    enabled: !!selectedRecId,
  });

  const { data: unmatchedTxns } = useQuery({
    queryKey: ['unmatched-transactions', selectedRecId],
    queryFn: () => getUnmatchedTransactions(selectedRecId!),
    enabled: !!showMatchModal && !!selectedRecId,
  });

  // ── Mutations ──
  const createMutation = useMutation({
    mutationFn: createReconciliation,
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      toast.success('تم إنشاء التسوية بنجاح');
      setShowCreateModal(false);
      if (data?.id) setSelectedRecId(data.id);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const matchMutation = useMutation({
    mutationFn: ({ reconciliationId, data }: any) => matchTransaction(reconciliationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      queryClient.invalidateQueries({ queryKey: ['unmatched-transactions'] });
      toast.success('تم مطابقة المعاملة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const unmatchMutation = useMutation({
    mutationFn: ({ reconciliationId, itemId }: any) => unmatchTransaction(reconciliationId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      queryClient.invalidateQueries({ queryKey: ['unmatched-transactions'] });
      toast.success('تم إلغاء المطابقة');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const completeMutation = useMutation({
    mutationFn: (reconciliationId: number) => completeReconciliation(reconciliationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      toast.success('تم إكمال التسوية بنجاح');
      setSelectedRecId(null);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const selectedRec = reconciliations?.find((r: any) => r.id === selectedRecId);
  const matchedItems = recDetail?.items?.filter((i: any) => i.status === 'MATCHED') || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="التسوية البنكية"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 21h18M3 10h18M5 6l7-3 7 3M4 10v11m16-11v11M8 14v3m4-3v3m4-3v3" /></svg>}
        actions={
          <button
            onClick={() => setShowCreateModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-primary-600 hover:bg-primary-700 text-white rounded-lg text-sm font-medium transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
            تسوية جديدة
          </button>
        }
      />

      {/* Bank Filter */}
      <div className="bg-white dark:bg-zinc-900 p-4 rounded-lg border border-gray-200 dark:border-zinc-700 flex gap-4">
        <div className="flex-1 max-w-xs">
          <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">البنك</label>
          <select
            value={selectedBank}
            onChange={(e) => { setSelectedBank(e.target.value ? Number(e.target.value) : ''); setSelectedRecId(null); }}
            className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm"
          >
            <option value="">جميع البنوك</option>
            {banks.map((bank) => (
              <option key={bank.id} value={bank.id}>{bank.name}</option>
            ))}
          </select>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reconciliations List */}
        <div className="bg-white dark:bg-zinc-900 rounded-lg border border-gray-200 dark:border-zinc-700 overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-zinc-700">
            <h3 className="font-semibold text-gray-900 dark:text-zinc-100">التسويات البنكية</h3>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {loadingRecs ? (
              <div className="p-4"><LoadingSpinner /></div>
            ) : reconciliations?.length === 0 ? (
              <div className="p-4 text-center text-gray-500 dark:text-zinc-400 text-sm">لا توجد تسويات</div>
            ) : (
              reconciliations?.map((rec: any) => (
                <div
                  key={rec.id}
                  onClick={() => setSelectedRecId(rec.id)}
                  className={cn(
                    'p-4 border-b border-gray-100 dark:border-zinc-800 cursor-pointer transition-colors',
                    selectedRecId === rec.id
                      ? 'bg-primary-50 dark:bg-primary-500/10'
                      : 'hover:bg-gray-50 dark:hover:bg-zinc-800/50'
                  )}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-gray-900 dark:text-zinc-100 text-sm">{rec.statementDate || rec.statement_date || '-'}</p>
                      <p className="text-xs text-gray-500 dark:text-zinc-400 mt-1">
                        رصيد البنك: {(rec.statementBalance ?? rec.statement_balance ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', STATUS_COLORS[rec.status] || '')}>
                      {STATUS_LABELS[rec.status] || rec.status}
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Reconciliation Detail */}
        <div className="lg:col-span-2 bg-white dark:bg-zinc-900 rounded-lg border border-gray-200 dark:border-zinc-700 overflow-hidden">
          {selectedRecId ? (
            loadingDetail ? (
              <div className="p-8"><LoadingSpinner /></div>
            ) : recDetail ? (
              <>
                {/* Detail Header */}
                <div className="p-4 border-b border-gray-200 dark:border-zinc-700 flex justify-between items-center">
                  <h3 className="font-semibold text-gray-900 dark:text-zinc-100">
                    تفاصيل التسوية - {recDetail.statementDate || recDetail.statement_date || '-'}
                  </h3>
                  <div className="flex gap-2">
                    {recDetail.status === 'DRAFT' && (
                      <button
                        onClick={() => setShowMatchModal(true)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>
                        مطابقة
                      </button>
                    )}
                    {recDetail.status === 'DRAFT' && (
                      <button
                        onClick={() => completeMutation.mutate(recDetail.id)}
                        disabled={completeMutation.isPending || Math.abs(recDetail.difference) > 0.01}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                        إكمال التسوية
                      </button>
                    )}
                  </div>
                </div>

                {/* Summary Cards */}
                <div className="p-4 border-b border-gray-200 dark:border-zinc-700 bg-gray-50 dark:bg-zinc-800/50">
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-white dark:bg-zinc-800 rounded-lg border border-gray-200 dark:border-zinc-700">
                      <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">رصيد البنك</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-zinc-100">
                        {(recDetail.statementBalance ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-white dark:bg-zinc-800 rounded-lg border border-gray-200 dark:border-zinc-700">
                      <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">رصيد الدفتر</p>
                      <p className="text-lg font-bold text-gray-900 dark:text-zinc-100">
                        {(recDetail.bookBalance ?? 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-center p-3 bg-white dark:bg-zinc-800 rounded-lg border border-gray-200 dark:border-zinc-700">
                      <p className="text-xs text-gray-500 dark:text-zinc-400 mb-1">الفرق</p>
                      <p className={cn(
                        'text-lg font-bold',
                        Math.abs(recDetail.difference) < 0.01 ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
                      )}>
                        {recDetail.difference?.toLocaleString()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Matched Items Table */}
                <div className="p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-zinc-100 mb-3">المعاملات المطابقة ({matchedItems.length})</h4>
                  {matchedItems.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-gray-200 dark:border-zinc-700">
                            <th className="text-right py-2 text-gray-500 dark:text-zinc-400 font-medium">التاريخ</th>
                            <th className="text-right py-2 text-gray-500 dark:text-zinc-400 font-medium">الوصف</th>
                            <th className="text-right py-2 text-gray-500 dark:text-zinc-400 font-medium">المبلغ</th>
                            <th className="text-right py-2 text-gray-500 dark:text-zinc-400 font-medium">الإجراءات</th>
                          </tr>
                        </thead>
                        <tbody>
                          {matchedItems.map((item: any) => (
                            <tr key={item.id} className="border-b border-gray-100 dark:border-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-800/50">
                              <td className="py-2 text-gray-700 dark:text-zinc-300">{item.transactionDate || item.transaction_date || '-'}</td>
                              <td className="py-2 text-gray-700 dark:text-zinc-300">{item.description || '-'}</td>
                              <td className="py-2 text-gray-900 dark:text-zinc-100 font-medium">{item.amount?.toLocaleString()}</td>
                              <td className="py-2">
                                {recDetail.status !== 'COMPLETED' && (
                                  <button
                                    onClick={() => unmatchMutation.mutate({ reconciliationId: recDetail.id, itemId: item.id })}
                                    className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 text-xs font-medium"
                                  >
                                    إلغاء المطابقة
                                  </button>
                                )}
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-center text-gray-500 dark:text-zinc-400 py-8 text-sm">لا توجد معاملات مطابقة</p>
                  )}
                </div>
              </>
            ) : null
          ) : (
            <div className="p-8 text-center text-gray-500 dark:text-zinc-400">
              اختر تسوية لعرض التفاصيل
            </div>
          )}
        </div>
      </div>

      {/* Create Reconciliation Modal */}
      <Modal isOpen={showCreateModal} onClose={() => setShowCreateModal(false)} title="تسوية بنكية جديدة" size="md">
        <form onSubmit={(e) => {
          e.preventDefault();
          const fd = new FormData(e.target as HTMLFormElement);
          createMutation.mutate({
            bank_id: Number(fd.get('bank_id')),
            statement_date: fd.get('statement_date'),
            statement_balance: Number(fd.get('statement_balance')),
            notes: fd.get('notes'),
          });
        }} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">البنك *</label>
            <select name="bank_id" required className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm">
              <option value="">اختر البنك</option>
              {banks.map((bank) => (
                <option key={bank.id} value={bank.id}>{bank.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">تاريخ كشف الحساب *</label>
            <input name="statement_date" type="date" required className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">رصيد البنك (وفقاً لكشف الحساب) *</label>
            <input name="statement_balance" type="number" step="0.01" required className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-zinc-300 mb-1">ملاحظات</label>
            <textarea name="notes" rows={3} className="w-full px-3 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg bg-white dark:bg-zinc-800 text-gray-900 dark:text-zinc-100 text-sm resize-none" />
          </div>
          <div className="flex justify-end gap-2 pt-2 border-t border-gray-200 dark:border-zinc-700">
            <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg text-gray-700 dark:text-zinc-300 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800">إلغاء</button>
            <button type="submit" disabled={createMutation.isPending} className="px-4 py-2 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded-lg text-sm font-medium">
              {createMutation.isPending ? 'جاري الإنشاء...' : 'إنشاء'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Match Transaction Modal */}
      <Modal isOpen={showMatchModal} onClose={() => setShowMatchModal(false)} title="مطابقة معاملة بنكية" size="lg">
        <div className="space-y-4">
          <p className="text-sm text-gray-500 dark:text-zinc-400">اختر المعاملة البنكية التي تريد مطابقتها مع السجل الدفتري:</p>
          <div className="max-h-[400px] overflow-y-auto border border-gray-200 dark:border-zinc-700 rounded-lg">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-gray-50 dark:bg-zinc-800">
                <tr className="border-b border-gray-200 dark:border-zinc-700">
                  <th className="text-right py-2 px-3 text-gray-500 dark:text-zinc-400 font-medium">التاريخ</th>
                  <th className="text-right py-2 px-3 text-gray-500 dark:text-zinc-400 font-medium">الوصف</th>
                  <th className="text-right py-2 px-3 text-gray-500 dark:text-zinc-400 font-medium">المبلغ</th>
                  <th className="text-right py-2 px-3 text-gray-500 dark:text-zinc-400 font-medium">النوع</th>
                  <th className="text-right py-2 px-3 text-gray-500 dark:text-zinc-400 font-medium">الإجراء</th>
                </tr>
              </thead>
              <tbody>
                {unmatchedTxns?.map((txn: any) => (
                  <tr key={txn.id} className="border-b border-gray-100 dark:border-zinc-800 hover:bg-gray-50 dark:hover:bg-zinc-800/50">
                    <td className="py-2 px-3 text-gray-700 dark:text-zinc-300">{txn.transaction_date}</td>
                    <td className="py-2 px-3 text-gray-700 dark:text-zinc-300">{txn.description}</td>
                    <td className="py-2 px-3 text-gray-900 dark:text-zinc-100 font-medium">{txn.amount?.toLocaleString()}</td>
                    <td className="py-2 px-3">
                      <span className={cn(
                        'px-2 py-0.5 rounded text-xs font-medium',
                        txn.transaction_type === 'DEPOSIT'
                          ? 'bg-green-100 text-green-700 dark:bg-green-500/20 dark:text-green-400'
                          : 'bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-400'
                      )}>
                        {txn.transaction_type === 'DEPOSIT' ? 'وارد' : 'صادر'}
                      </span>
                    </td>
                    <td className="py-2 px-3">
                      <button
                        onClick={() => {
                          matchMutation.mutate({
                            reconciliationId: selectedRecId,
                            data: {
                              bank_transaction_id: txn.id,
                              journal_entry_id: txn.journal_entry_id,
                              amount: txn.amount,
                              transaction_type: txn.transaction_type,
                              description: txn.description,
                            },
                          });
                        }}
                        disabled={matchMutation.isPending}
                        className="px-2 py-1 bg-primary-600 hover:bg-primary-700 disabled:opacity-50 text-white rounded text-xs font-medium transition-colors"
                      >
                        مطابقة
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {unmatchedTxns?.length === 0 && (
              <p className="text-center text-gray-500 dark:text-zinc-400 py-8 text-sm">لا توجد معاملات للمطابقة</p>
            )}
          </div>
          <div className="flex justify-end">
            <button type="button" onClick={() => setShowMatchModal(false)} className="px-4 py-2 border border-gray-300 dark:border-zinc-600 rounded-lg text-gray-700 dark:text-zinc-300 text-sm hover:bg-gray-50 dark:hover:bg-zinc-800">إغلاق</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
