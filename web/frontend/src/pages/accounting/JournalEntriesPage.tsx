import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { getJournalEntries, createJournalEntry, postJournalEntry } from '@/api/accounting';
import { formatDate, formatCurrency } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { EditableTable } from '@/components/ui/EditableTable';
import { useForm } from 'react-hook-form';

export default function JournalEntriesPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [lines, setLines] = useState<{ accountId: string; debit: number; credit: number; description: string }[]>([
    { accountId: '', debit: 0, credit: 0, description: '' },
    { accountId: '', debit: 0, credit: 0, description: '' },
  ]);

  const { data, isLoading } = useQuery({
    queryKey: ['journal-entries', page, search],
    queryFn: () => getJournalEntries({ page, pageSize: 10, search }),
  });

  const postMutation = useMutation({
    mutationFn: postJournalEntry,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] }),
  });

  const createMutation = useMutation({
    mutationFn: createJournalEntry,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['journal-entries'] });
      setShowModal(false);
      reset();
      setLines([{ accountId: '', debit: 0, credit: 0, description: '' }, { accountId: '', debit: 0, credit: 0, description: '' }]);
    },
  });

  const { register, handleSubmit, reset } = useForm();

  const totalDebit = useMemo(() => lines.reduce((s, l) => s + (l.debit || 0), 0), [lines]);
  const totalCredit = useMemo(() => lines.reduce((s, l) => s + (l.credit || 0), 0), [lines]);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'entryNumber', header: 'رقم القيد', render: (item) => <span className="font-medium text-primary-600 dark:text-primary-400">{String(item.entryNumber)}</span> },
    { key: 'date', header: 'التاريخ', render: (item) => formatDate(String(item.date)) },
    { key: 'description', header: 'الوصف', render: (item) => String(item.description) },
    { key: 'totalDebit', header: 'المدين', render: (item) => formatCurrency(Number(item.totalDebit)) },
    { key: 'totalCredit', header: 'الدائن', render: (item) => formatCurrency(Number(item.totalCredit)) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => item.status === 'DRAFT' ? (
      <button onClick={(e) => { e.stopPropagation(); postMutation.mutate(String(item.id)); }} className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 text-sm font-medium">ترحيل</button>
    ) : null },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">القيود اليومية</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ قيد جديد</button>
      </div>
      <DataTable
        columns={columns}
        data={(data?.items || []) as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={data?.total || 0}
        page={page}
        pageSize={10}
        onPageChange={setPage}
        searchValue={search}
        onSearchChange={setSearch}
        searchPlaceholder="بحث..."
      />
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); setLines([]); }} title="قيد يومي جديد" size="lg">
        <form onSubmit={handleSubmit((d) => {
          createMutation.mutate({
            date: d.date,
            description: d.description,
            reference: '',
            status: 'DRAFT',
            totalDebit: totalDebit,
            totalCredit: totalCredit,
            createdBy: '',
            createdAt: new Date().toISOString(),
            lines: lines.filter((l) => l.accountId).map((l) => ({
              id: '',
              accountId: String(l.accountId),
              accountCode: '',
              accountName: '',
              debit: l.debit,
              credit: l.credit,
              description: l.description,
            })),
          });
        })} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">التاريخ</label>
              <input {...register('date')} type="date" className="input" />
            </div>
            <div>
              <label className="label">الوصف</label>
              <input {...register('description', { required: true })} className="input" />
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 dark:text-zinc-100 mb-2">بنود القيد</h4>
            <EditableTable
              columns={[
                { key: 'accountId', header: 'كود الحساب', type: 'text' },
                { key: 'debit', header: 'مدين', type: 'number' },
                { key: 'credit', header: 'دائن', type: 'number' },
                { key: 'description', header: 'الوصف', type: 'text' },
              ]}
              data={lines as unknown as Record<string, unknown>[]}
              onChange={(newData) => setLines(newData as typeof lines)}
              onAddRow={() => setLines([...lines, { accountId: '', debit: 0, credit: 0, description: '' }])}
              onDeleteRow={(idx) => setLines(lines.filter((_, i) => i !== idx))}
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-zinc-800">
            <div className="flex gap-6 text-sm">
              <span className="text-gray-600 dark:text-zinc-400">المدين: <strong className="text-gray-900 dark:text-zinc-100">{formatCurrency(totalDebit)}</strong></span>
              <span className="text-gray-600 dark:text-zinc-400">الدائن: <strong className="text-gray-900 dark:text-zinc-100">{formatCurrency(totalCredit)}</strong></span>
            </div>
            <span className={`text-sm font-medium ${isBalanced ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              {isBalanced ? 'متوازن' : 'غير متوازن'}
            </span>
          </div>

          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); setLines([]); }} className="btn-secondary">إلغاء</button>
            <button type="submit" disabled={!isBalanced} className="btn-primary disabled:opacity-50">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
