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
  getUnreconciledTransactions,
} from '@/api/bankReconciliation';
import { getBanks } from '@/api/payments';
import { StatsCard } from '@/components/ui/StatsCard';
import { Modal } from '@/components/ui/Modal';

export default function BankReconciliationPage() {
  const queryClient = useQueryClient();
  const [selectedBank, setSelectedBank] = useState<number | ''>('');
  const [selectedReconciliation, setSelectedReconciliation] = useState<any>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showMatchModal, setShowMatchModal] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<any>(null);

  const { data: banks } = useQuery({
    queryKey: ['banks'],
    queryFn: getBanks,
  });

  const { data: reconciliations, isLoading } = useQuery({
    queryKey: ['reconciliations', selectedBank],
    queryFn: () => getReconciliations(selectedBank as number || undefined),
  });

  const { data: reconciliationDetail } = useQuery({
    queryKey: ['reconciliation', selectedReconciliation?.id],
    queryFn: () => getReconciliation(selectedReconciliation?.id),
    enabled: !!selectedReconciliation?.id,
  });

  const { data: unmatchedTransactions } = useQuery({
    queryKey: ['unmatched-transactions', selectedReconciliation?.id],
    queryFn: () => getUnmatchedTransactions(selectedReconciliation?.id),
    enabled: !!selectedReconciliation?.id,
  });

  const { data: unreconciledTransactions } = useQuery({
    queryKey: ['unreconciled-transactions', selectedBank],
    queryFn: () => getUnreconciledTransactions(selectedBank as number),
    enabled: !!selectedBank,
  });

  const createMutation = useMutation({
    mutationFn: createReconciliation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      setShowCreateModal(false);
    },
  });

  const matchMutation = useMutation({
    mutationFn: ({ reconciliationId, data }: any) => matchTransaction(reconciliationId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      queryClient.invalidateQueries({ queryKey: ['unmatched-transactions'] });
      setShowMatchModal(false);
    },
  });

  const unmatchMutation = useMutation({
    mutationFn: ({ reconciliationId, itemId }: any) => unmatchTransaction(reconciliationId, itemId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliation'] });
      queryClient.invalidateQueries({ queryKey: ['unmatched-transactions'] });
    },
  });

  const completeMutation = useMutation({
    mutationFn: (reconciliationId: number) => completeReconciliation(reconciliationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reconciliations'] });
      setSelectedReconciliation(null);
    },
  });

  const statusColors: Record<string, string> = {
    DRAFT: 'bg-yellow-100 text-yellow-800',
    IN_PROGRESS: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    CANCELLED: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">التسوية البنكية</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          تسوية جديدة
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <select
          value={selectedBank}
          onChange={(e) => setSelectedBank(e.target.value ? Number(e.target.value) : '')}
          className="border rounded-lg px-3 py-2"
        >
          <option value="">جميع البنوك</option>
          {banks?.map((bank: any) => (
            <option key={bank.id} value={bank.id}>{bank.name}</option>
          ))}
        </select>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reconciliations List */}
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <div className="p-4 border-b">
            <h3 className="font-bold">التسويات البنكية</h3>
          </div>
          <div className="max-h-[600px] overflow-y-auto">
            {reconciliations?.map((rec: any) => (
              <div
                key={rec.id}
                onClick={() => setSelectedReconciliation(rec)}
                className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                  selectedReconciliation?.id === rec.id ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-medium">{rec.statement_date}</p>
                    <p className="text-sm text-gray-500">رصيد البنك: {rec.bank_balance?.toLocaleString()}</p>
                  </div>
                  <span className={`px-2 py-1 rounded-full text-xs ${statusColors[rec.status] || ''}`}>
                    {rec.status === 'DRAFT' ? 'مسودة' : rec.status === 'IN_PROGRESS' ? 'قيد التنفيذ' : rec.status === 'COMPLETED' ? 'مكتمل' : 'ملغي'}
                  </span>
                </div>
              </div>
            ))}
            {reconciliations?.length === 0 && (
              <div className="p-4 text-center text-gray-500">لا توجد تسويات</div>
            )}
          </div>
        </div>

        {/* Reconciliation Detail */}
        <div className="lg:col-span-2 bg-white rounded-lg shadow overflow-hidden">
          {selectedReconciliation ? (
            <>
              <div className="p-4 border-b flex justify-between items-center">
                <h3 className="font-bold">تفاصيل التسوية - {selectedReconciliation.statement_date}</h3>
                <div className="flex gap-2">
                  {selectedReconciliation.status === 'DRAFT' && (
                    <button
                      onClick={() => setShowMatchModal(true)}
                      className="bg-green-600 text-white px-3 py-1 rounded text-sm"
                    >
                      مطابقة معاملة
                    </button>
                  )}
                  {selectedReconciliation.status === 'IN_PROGRESS' && (
                    <button
                      onClick={() => completeMutation.mutate(selectedReconciliation.id)}
                      className="bg-blue-600 text-white px-3 py-1 rounded text-sm"
                    >
                      إكمال التسوية
                    </button>
                  )}
                </div>
              </div>

              {/* Summary */}
              <div className="p-4 border-b bg-gray-50">
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">رصيد البنك:</span>
                    <p className="font-bold">{selectedReconciliation.bank_balance?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">رصيد الدفتر:</span>
                    <p className="font-bold">{selectedReconciliation.book_balance?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">الفرق:</span>
                    <p className={`font-bold ${
                      selectedReconciliation.difference === 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {selectedReconciliation.difference?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Matched Items */}
              <div className="p-4">
                <h4 className="font-bold mb-3">المعاملات المطابقة</h4>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b">
                      <th className="text-right py-2">التاريخ</th>
                      <th className="text-right py-2">الوصف</th>
                      <th className="text-right py-2">المبلغ</th>
                      <th className="text-right py-2">الإجراءات</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reconciliationDetail?.items?.filter((item: any) => item.status === 'MATCHED').map((item: any) => (
                      <tr key={item.id} className="border-b">
                        <td className="py-2">{item.transaction_date}</td>
                        <td className="py-2">{item.description}</td>
                        <td className="py-2">{item.amount?.toLocaleString()}</td>
                        <td className="py-2">
                          {selectedReconciliation.status !== 'COMPLETED' && (
                            <button
                              onClick={() => unmatchMutation.mutate({
                                reconciliationId: selectedReconciliation.id,
                                itemId: item.id,
                              })}
                              className="text-red-600 hover:underline text-xs"
                            >
                              إلغاء المطابقة
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {reconciliationDetail?.items?.filter((item: any) => item.status === 'MATCHED').length === 0 && (
                  <p className="text-center text-gray-500 py-4">لا توجد معاملات مطابقة</p>
                )}
              </div>
            </>
          ) : (
            <div className="p-8 text-center text-gray-500">
              اختر تسوية لعرض التفاصيل
            </div>
          )}
        </div>
      </div>

      {/* Create Reconciliation Modal */}
      {showCreateModal && (
        <Modal onClose={() => setShowCreateModal(false)} title="تسوية بنكية جديدة">
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            createMutation.mutate({
              bank_id: Number(formData.get('bank_id')),
              statement_date: formData.get('statement_date'),
              bank_balance: Number(formData.get('bank_balance')),
              book_balance: Number(formData.get('book_balance')),
              notes: formData.get('notes'),
            });
          }} className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">البنك</label>
              <select name="bank_id" required className="w-full border rounded-lg px-3 py-2">
                <option value="">اختر البنك</option>
                {banks?.map((bank: any) => (
                  <option key={bank.id} value={bank.id}>{bank.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">تاريخ كشف الحساب</label>
              <input name="statement_date" type="date" required className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">رصيد البنك (وفقاً لكشف الحساب)</label>
              <input name="bank_balance" type="number" step="0.01" required className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">رصيد الدفتر (وفقاً للسجل)</label>
              <input name="book_balance" type="number" step="0.01" required className="w-full border rounded-lg px-3 py-2" />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">ملاحظات</label>
              <textarea name="notes" className="w-full border rounded-lg px-3 py-2" rows={3} />
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 border rounded-lg">إلغاء</button>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">إنشاء</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Match Transaction Modal */}
      {showMatchModal && selectedReconciliation && (
        <Modal onClose={() => setShowMatchModal(false)} title="مطابقة معاملة">
          <div className="space-y-4">
            <div className="max-h-[400px] overflow-y-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-right py-2">التاريخ</th>
                    <th className="text-right py-2">الوصف</th>
                    <th className="text-right py-2">المبلغ</th>
                    <th className="text-right py-2">النوع</th>
                    <th className="text-right py-2">الإجراء</th>
                  </tr>
                </thead>
                <tbody>
                  {unmatchedTransactions?.map((txn: any) => (
                    <tr key={txn.id} className="border-b hover:bg-gray-50">
                      <td className="py-2">{txn.date}</td>
                      <td className="py-2">{txn.description}</td>
                      <td className="py-2">{txn.amount?.toLocaleString()}</td>
                      <td className="py-2">
                        <span className={`px-2 py-1 rounded text-xs ${
                          txn.type === 'CREDIT' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {txn.type === 'CREDIT' ? 'وارد' : 'صادر'}
                        </span>
                      </td>
                      <td className="py-2">
                        <button
                          onClick={() => {
                            setSelectedTransaction(txn);
                            matchMutation.mutate({
                              reconciliationId: selectedReconciliation.id,
                              data: {
                                journal_entry_id: txn.journal_entry_id,
                                transaction_type: txn.type,
                                amount: txn.amount,
                                transaction_date: txn.date,
                                description: txn.description,
                              },
                            });
                          }}
                          className="bg-blue-600 text-white px-2 py-1 rounded text-xs"
                        >
                          مطابقة
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {unmatchedTransactions?.length === 0 && (
                <p className="text-center text-gray-500 py-4">لا توجد معاملات للمطابقة</p>
              )}
            </div>
            <div className="flex justify-end">
              <button type="button" onClick={() => setShowMatchModal(false)} className="px-4 py-2 border rounded-lg">إغلاق</button>
            </div>
          </div>
        </Modal>
      )}

      {isLoading && <div className="text-center py-4">جاري التحميل...</div>}
    </div>
  );
}
