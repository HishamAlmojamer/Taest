import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import {
  getJournalEntries,
  createJournalEntry,
  updateJournalEntry,
  postJournalEntry,
  voidJournalEntry,
  deleteJournalEntry,
  getAccountsFlat,
  getCostCenters,
} from '@/api/accounting';
import { formatDate, formatDateTime, formatCurrency, getStatusLabel, getStatusColor } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EditableTable } from '@/components/ui/EditableTable';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import ExcelExportButton from '@/components/excel/ExcelExportButton';
import ExcelImportButton from '@/components/excel/ExcelImportButton';
import type { JournalEntry, Account, CostCenter } from '@/types';

interface JournalLineRow {
  accountId: string;
  accountCode: string;
  debit: number;
  credit: number;
  description: string;
  costCenterId: string;
}

function todayLocal(): string {
  const d = new Date();
  const off = d.getTimezoneOffset();
  return new Date(d.getTime() - off * 60000).toISOString().slice(0, 10);
}

function emptyLines(): JournalLineRow[] {
  return [
    { accountId: '', accountCode: '', debit: 0, credit: 0, description: '', costCenterId: '' },
    { accountId: '', accountCode: '', debit: 0, credit: 0, description: '', costCenterId: '' },
  ];
}

export default function JournalEntriesPage() {
  const queryClient = useQueryClient();
  const company = useCompany();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showModal, setShowModal] = useState(false);
  const [modalMode, setModalMode] = useState<'create' | 'edit'>('create');
  const [editingEntry, setEditingEntry] = useState<JournalEntry | null>(null);
  const [entryDate, setEntryDate] = useState(todayLocal());
  const [description, setDescription] = useState('');
  const [lines, setLines] = useState<JournalLineRow[]>(emptyLines());
  const [viewEntry, setViewEntry] = useState<JournalEntry | null>(null);
  const [showPrint, setShowPrint] = useState(false);
  const [voidModalEntry, setVoidModalEntry] = useState<JournalEntry | null>(null);
  const [voidReason, setVoidReason] = useState('');
  const [deleteTarget, setDeleteTarget] = useState<JournalEntry | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['journal-entries', page, search, statusFilter],
    queryFn: () => getJournalEntries({ page, perPage: 10, search, status: statusFilter || undefined }),
  });

  const accountsQuery = useQuery({
    queryKey: ['accounts-flat'],
    queryFn: () => getAccountsFlat(),
    staleTime: 60_000,
  });
  const accounts = accountsQuery.data || [];

  const costCentersQuery = useQuery({
    queryKey: ['cost-centers'],
    queryFn: getCostCenters,
    staleTime: 60_000,
  });
  const costCenters = costCentersQuery.data || [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['journal-entries'] });

  const postMutation = useMutation({
    mutationFn: postJournalEntry,
    onSuccess: () => { invalidate(); toast.success('تم ترحيل القيد بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const saveMutation = useMutation({
    mutationFn: ({ mode, id, payload }: { mode: 'create' | 'edit'; id: string; payload: any }) =>
      mode === 'edit' ? updateJournalEntry(id, payload) : createJournalEntry(payload),
    onSuccess: () => {
      invalidate();
      setShowModal(false);
      toast.success(modalMode === 'edit' ? 'تم تعديل القيد بنجاح' : 'تم إنشاء القيد بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteJournalEntry,
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
      toast.success('تم حذف القيد بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const voidMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => voidJournalEntry(id, reason),
    onSuccess: () => {
      invalidate();
      setVoidModalEntry(null);
      setVoidReason('');
      toast.success('تم إبطال القيد بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const totalDebit = useMemo(() => lines.reduce((s, l) => s + (l.debit || 0), 0), [lines]);
  const totalCredit = useMemo(() => lines.reduce((s, l) => s + (l.credit || 0), 0), [lines]);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;
  const effectiveLines = useMemo(() => lines.filter((l) => l.accountId || String(l.accountCode || '').trim()), [lines]);
  const canSave = effectiveLines.length >= 2 && isBalanced;

  function resolveAccount(term: string): Account | null {
    const t = (term || '').trim().toLowerCase();
    if (!t) return null;
    return (
      accounts.find((a) => String(a.code).toLowerCase() === t) ||
      accounts.find((a) => String(a.name).toLowerCase() === t) ||
      accounts.find((a) => String(a.id) === t) ||
      null
    );
  }

  function updateLine(index: number, patch: Partial<JournalLineRow>) {
    setLines((prev) => prev.map((l, i) => (i === index ? { ...l, ...patch } : l)));
  }

  function validateLineAccount(account: Account | null, rawCode: string): string | null {
    if (account) {
      if (account.isControl) {
        return `الحساب ${account.code} حساب علبة (تجمعي) ولا يقبل الترحيل مباشرة`;
      }
      if (!account.isActive) {
        return `الحساب ${account.code} غير نشط`;
      }
      return null;
    }
    if (String(rawCode || '').trim()) {
      return `الحساب غير معروف: ${String(rawCode).trim()}`;
    }
    return null;
  }

  function buildPayload(): any | null {
    if (!entryDate) {
      toast.error('أدخل تاريخ القيد');
      return null;
    }
    if (!description.trim()) {
      toast.error('أدخل وصف القيد');
      return null;
    }
    if (effectiveLines.length < 2) {
      toast.error('أدخل سطرين على الأقل');
      return null;
    }
    if (!isBalanced) {
      toast.error('القيد غير متوازن: المدين والدائن مختلفان');
      return null;
    }
    for (const l of effectiveLines) {
      const account = l.accountId ? accounts.find((a) => String(a.id) === String(l.accountId)) || null : resolveAccount(l.accountCode);
      const err = validateLineAccount(account, l.accountCode);
      if (err) {
        toast.error(err);
        return null;
      }
      if ((l.debit || 0) <= 0 && (l.credit || 0) <= 0) {
        toast.error('كل سطر يجب أن يحتوي على مدين أو دائن');
        return null;
      }
      if ((l.debit || 0) > 0 && (l.credit || 0) > 0) {
        toast.error('لا يمكن أن يحتوي السطر على مدين ودائن معاً');
        return null;
      }
    }
    return {
      entryDate,
      description: description.trim(),
      lines: effectiveLines.map((l) => ({
        accountId: String(l.accountId || resolveAccount(l.accountCode)?.id || ''),
        debit: l.debit || 0,
        credit: l.credit || 0,
        description: l.description,
        ...(l.costCenterId ? { costCenterId: l.costCenterId } : {}),
      })),
    };
  }

  function openCreate() {
    setModalMode('create');
    setEditingEntry(null);
    setEntryDate(todayLocal());
    setDescription('');
    setLines(emptyLines());
    setShowModal(true);
  }

  function openEdit(entry: JournalEntry) {
    setModalMode('edit');
    setEditingEntry(entry);
    setEntryDate(String(entry.entryDate || '').slice(0, 10));
    setDescription(entry.description || '');
    const mapped: JournalLineRow[] = (entry.lines || []).map((l) => ({
      accountId: String(l.accountId ?? ''),
      accountCode: l.accountCode || '',
      debit: Number(l.debit || 0),
      credit: Number(l.credit || 0),
      description: l.description || '',
      costCenterId: l.costCenterId ? String(l.costCenterId) : '',
    }));
    while (mapped.length < 2) {
      mapped.push({ accountId: '', accountCode: '', debit: 0, credit: 0, description: '', costCenterId: '' });
    }
    setLines(mapped);
    setShowModal(true);
  }

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'entryNumber', header: 'رقم القيد', render: (item) => <span className="font-medium text-primary-600 dark:text-primary-400">{String(item.entryNumber)}</span> },
    { key: 'entryDate', header: 'التاريخ', render: (item) => formatDate(String(item.entryDate)) },
    { key: 'description', header: 'الوصف', render: (item) => String(item.description) },
    { key: 'totalDebit', header: 'المدين', render: (item) => formatCurrency((item.lines as any[] || []).reduce((s: number, l: any) => s + Number(l.debit || 0), 0)) },
    { key: 'totalCredit', header: 'الدائن', render: (item) => formatCurrency((item.lines as any[] || []).reduce((s: number, l: any) => s + Number(l.credit || 0), 0)) },
    {
      key: 'status', header: 'الحالة', render: (item) => {
        const s = String(item.status);
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(s)}`}>
            {getStatusLabel(s, 'ar')}
          </span>
        );
      },
    },
    {
      key: 'actions', header: 'إجراءات', render: (item) => {
        const entry = item as unknown as JournalEntry;
        const s = String(item.status);
        return (
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => { e.stopPropagation(); setViewEntry(entry); }}
              className="text-sky-600 hover:text-sky-700 dark:text-sky-400 text-xs font-medium"
            >
              عرض
            </button>
            {s === 'Draft' && (
              <>
                <button
                  onClick={(e) => { e.stopPropagation(); openEdit(entry); }}
                  className="text-gray-600 hover:text-gray-700 dark:text-zinc-300 text-xs font-medium"
                >
                  تعديل
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); postMutation.mutate(String(entry.id)); }}
                  className="text-emerald-600 hover:text-emerald-700 dark:text-emerald-400 text-xs font-medium"
                >
                  ترحيل
                </button>
                <button
                  onClick={(e) => { e.stopPropagation(); setDeleteTarget(entry); }}
                  className="text-red-600 hover:text-red-700 dark:text-red-400 text-xs font-medium"
                >
                  حذف
                </button>
              </>
            )}
            {s === 'Posted' && (
              <button
                onClick={(e) => { e.stopPropagation(); setVoidModalEntry(entry); setVoidReason(''); }}
                className="text-orange-600 hover:text-orange-700 dark:text-orange-400 text-xs font-medium"
              >
                إبطال
              </button>
            )}
          </div>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader title="القيود اليومية" subtitle="إدارة القيود اليومية والترحيل" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} actions={<>
        <ExcelExportButton url="/excel/exports/journal-entries" params={{ status: statusFilter || undefined }} filename="journal-entries.xlsx" />
        <ExcelImportButton
          url="/excel/imports/journal-entries"
          label="استيراد قيود Excel"
          helpText="حمّل قالب الاستيراد من صفحة شجرة الحسابات أو أنشئ ملفاً بالأعمدة: entry_reference, entry_date, description, account_code, cost_center_code, currency_code, debit, credit"
          onSuccess={() => invalidate()}
        />
        <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2" disabled={(data?.items || []).length === 0}>
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          طباعة / PDF
        </button>
        <button onClick={openCreate} className="btn-primary">+ قيد جديد</button>
      </>} />
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600 dark:text-zinc-400">الحالة:</label>
          <select value={statusFilter} onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }} className="input w-40">
            <option value="">الكل</option>
            <option value="Draft">مسودة</option>
            <option value="Posted">مرحّل</option>
            <option value="Voided">ملغي</option>
          </select>
        </div>
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
        searchPlaceholder="بحث برقم/وصف القيد أو كود/اسم الحساب..."
      />

      {/* ── Create / Edit modal ─────────────────────────────────────── */}
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title={modalMode === 'edit' ? `تعديل القيد ${editingEntry?.entryNumber || ''}` : 'قيد يومي جديد'} size="lg">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            const payload = buildPayload();
            if (payload) {
              saveMutation.mutate({ mode: modalMode, id: String(editingEntry?.id || ''), payload });
            }
          }}
          className="space-y-4"
        >
          <datalist id="je-account-options">
            {accounts.map((a) => (
              <option key={a.id} value={String(a.code)}>{`${a.code} - ${a.name}`}</option>
            ))}
          </datalist>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">التاريخ</label>
              <input type="date" value={entryDate} onChange={(e) => setEntryDate(e.target.value)} className="input" />
            </div>
            <div>
              <label className="label">الوصف</label>
              <input value={description} onChange={(e) => setDescription(e.target.value)} className="input" placeholder="وصف القيد..." />
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 dark:text-zinc-100 mb-2">بنود القيد</h4>
            <EditableTable
              columns={[
                {
                  key: 'accountCode',
                  header: 'الحساب (كود / اسم)',
                  render: (row, index) => {
                    const account = resolveAccount(String((row as unknown as JournalLineRow).accountCode || ''));
                    const invalid = String((row as unknown as JournalLineRow).accountCode || '').trim() && !(row as unknown as JournalLineRow).accountId;
                    return (
                      <div className="relative">
                        <input
                          list="je-account-options"
                          className="input py-1 text-sm w-full"
                          value={String((row as unknown as JournalLineRow).accountCode || '')}
                          onChange={(e) => {
                            const acc = resolveAccount(e.target.value);
                            updateLine(index, {
                              accountCode: e.target.value,
                              accountId: acc ? String(acc.id) : '',
                            });
                          }}
                          placeholder="أدخل كود الحساب أو اختر..."
                        />
                        {invalid && <span className="text-xs text-red-500">غير معروف</span>}
                        {account && !invalid && account.isControl && (
                          <span className="text-xs text-orange-500">حساب علبة!</span>
                        )}
                      </div>
                    );
                  },
                },
                {
                  key: 'costCenterId',
                  header: 'مركز التكلفة',
                  render: (row, index) => (
                    <select
                      className="input py-1 text-sm w-full"
                      value={String((row as unknown as JournalLineRow).costCenterId || '')}
                      onChange={(e) => updateLine(index, { costCenterId: e.target.value })}
                    >
                      <option value="">بدون</option>
                      {costCenters.map((cc: CostCenter) => (
                        <option key={cc.id} value={cc.id}>
                          {cc.code ? `${cc.code} - ${cc.name}` : cc.name}
                        </option>
                      ))}
                    </select>
                  ),
                },
                { key: 'debit', header: 'مدين', type: 'number' },
                { key: 'credit', header: 'دائن', type: 'number' },
                { key: 'description', header: 'الوصف', type: 'text' },
              ]}
              data={lines as unknown as Record<string, unknown>[]}
              onChange={(newData) => setLines(newData as unknown as typeof lines)}
              onAddRow={() => setLines([...lines, { accountId: '', accountCode: '', debit: 0, credit: 0, description: '', costCenterId: '' }])}
              onDeleteRow={(idx) => setLines(lines.filter((_, i) => i !== idx))}
              addRowLabel="+ إضافة بند"
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
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">إلغاء</button>
            <button type="submit" disabled={!canSave || saveMutation.isPending} className="btn-primary disabled:opacity-50">
              {saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>

      {/* ── View modal ──────────────────────────────────────────────── */}
      {viewEntry && (
        <Modal isOpen onClose={() => setViewEntry(null)} title={`القيد ${viewEntry.entryNumber}`} size="lg">
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <label className="text-xs text-gray-500 dark:text-zinc-400 block">التاريخ</label>
                <span className="font-medium">{formatDate(String(viewEntry.entryDate))}</span>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-zinc-400 block">الحالة</label>
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getStatusColor(String(viewEntry.status))}`}>
                  {getStatusLabel(String(viewEntry.status), 'ar')}
                </span>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-zinc-400 block">تاريخ الإنشاء</label>
                <span className="font-medium">{viewEntry.createdAt ? formatDateTime(String(viewEntry.createdAt)) : '-'}</span>
              </div>
              <div>
                <label className="text-xs text-gray-500 dark:text-zinc-400 block">ترحيل</label>
                <span className="font-medium">{viewEntry.postedAt ? formatDateTime(String(viewEntry.postedAt)) : '-'}</span>
              </div>
            </div>
            {viewEntry.description && (
              <div className="text-sm">
                <span className="text-gray-500 dark:text-zinc-400">الوصف: </span>
                <span className="font-medium">{viewEntry.description}</span>
              </div>
            )}
            {viewEntry.referenceType && (
              <div className="text-sm">
                <span className="text-gray-500 dark:text-zinc-400">المرجع: </span>
                <span className="font-medium">{viewEntry.referenceType}{viewEntry.referenceId ? ` رقم ${viewEntry.referenceId}` : ''}</span>
              </div>
            )}
            {viewEntry.voidReason && (
              <div className="text-sm text-orange-600 dark:text-orange-400">
                <span>سبب الإبطال: </span>
                <span className="font-medium">{viewEntry.voidReason}</span>
              </div>
            )}

            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-zinc-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 dark:bg-zinc-800 text-gray-700 dark:text-zinc-300">
                    <th className="px-3 py-2 text-right font-semibold">الحساب</th>
                    <th className="px-3 py-2 text-right font-semibold">مركز التكلفة</th>
                    <th className="px-3 py-2 text-right font-semibold">الوصف</th>
                    <th className="px-3 py-2 text-right font-semibold">مدين</th>
                    <th className="px-3 py-2 text-right font-semibold">دائن</th>
                  </tr>
                </thead>
                <tbody>
                  {(viewEntry.lines || []).map((l, idx) => (
                    <tr key={l.id || idx} className="border-t border-gray-100 dark:border-zinc-700">
                      <td className="px-3 py-2">
                        {l.accountCode ? (
                          <>
                            <span className="font-mono text-xs text-gray-500 dark:text-zinc-400">{l.accountCode}</span>
                            <span className="block">{l.accountName || '-'}</span>
                          </>
                        ) : (
                          <span className="block">{l.accountName || `#${l.accountId}`}</span>
                        )}
                      </td>
                      <td className="px-3 py-2">{l.costCenterName ? `${l.costCenterCode ? `${l.costCenterCode} - ` : ''}${l.costCenterName}` : '-'}</td>
                      <td className="px-3 py-2">{l.description || '-'}</td>
                      <td className="px-3 py-2">{Number(l.debit || 0) > 0 ? formatCurrency(Number(l.debit)) : ''}</td>
                      <td className="px-3 py-2">{Number(l.credit || 0) > 0 ? formatCurrency(Number(l.credit)) : ''}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-gray-200 dark:border-zinc-600 bg-gray-50 dark:bg-zinc-800 font-bold">
                    <td className="px-3 py-2" colSpan={3}>الإجمالي</td>
                    <td className="px-3 py-2">{formatCurrency((viewEntry.lines || []).reduce((s, l) => s + Number(l.debit || 0), 0))}</td>
                    <td className="px-3 py-2">{formatCurrency((viewEntry.lines || []).reduce((s, l) => s + Number(l.credit || 0), 0))}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {String(viewEntry.status) === 'Draft' && (
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => {
                    setViewEntry(null);
                    openEdit(viewEntry);
                  }}
                >
                  تعديل
                </button>
              </div>
            )}

            <div className="flex justify-start">
              <button type="button" onClick={() => setViewEntry(null)} className="btn-secondary">إغلاق</button>
            </div>
          </div>
        </Modal>
      )}

      <PrintPreviewModal
        isOpen={showPrint}
        onClose={() => setShowPrint(false)}
        title="القيود اليومية"
        filename="القيود-اليومية"
      >
        <PrintDocument company={company} title="تقرير القيود اليومية" meta={[
          { label: 'تاريخ التقرير', value: formatDateTime(new Date().toISOString()) },
          { label: 'عدد القيود', value: String(data?.total || 0) },
        ]}>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">#</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">رقم القيد</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">التاريخ</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الوصف</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المدين</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الدائن</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الحالة</th>
              </tr>
            </thead>
            <tbody>
              {(data?.items || []).map((item: any, idx: number) => (
                <tr key={item.id || idx}>
                  <td className="px-3 py-2 border border-gray-300">{idx + 1}</td>
                  <td className="px-3 py-2 border border-gray-300 font-mono">{String(item.entryNumber)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatDate(String(item.entryDate))}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(item.description)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency((item.lines || []).reduce((s: number, l: any) => s + Number(l.debit || 0), 0))}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency((item.lines || []).reduce((s: number, l: any) => s + Number(l.credit || 0), 0))}</td>
                  <td className="px-3 py-2 border border-gray-300">{getStatusLabel(String(item.status), 'ar')}</td>
                </tr>
              ))}
              <tr className="bg-gray-100 font-bold">
                <td className="px-3 py-2 border border-gray-300" colSpan={4}>الإجمالي</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency((data?.items || []).reduce((s: number, it: any) => s + (it.lines || []).reduce((x: number, l: any) => x + Number(l.debit || 0), 0), 0))}</td>
                <td className="px-3 py-2 border border-gray-300">{formatCurrency((data?.items || []).reduce((s: number, it: any) => s + (it.lines || []).reduce((x: number, l: any) => x + Number(l.credit || 0), 0), 0))}</td>
                <td className="px-3 py-2 border border-gray-300"></td>
              </tr>
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>

      {voidModalEntry && (
        <Modal isOpen onClose={() => { setVoidModalEntry(null); setVoidReason(''); }} title="إبطال القيد" size="sm">
          <div className="space-y-4">
            <p className="text-sm text-gray-600 dark:text-zinc-400">هل أنت متأكد من إبطال القيد رقم <strong>{String(voidModalEntry.entryNumber)}</strong>؟ سيتم إنشاء قيد عكسي بتاريخ القيد نفسه.</p>
            <div>
              <label className="label">سبب الإبطال</label>
              <textarea value={voidReason} onChange={(e) => setVoidReason(e.target.value)} className="input" rows={3} placeholder="أدخل سبب الإبطال..." />
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => { setVoidModalEntry(null); setVoidReason(''); }} className="btn-secondary">إلغاء</button>
              <button type="button" onClick={() => { if (voidReason.trim()) voidMutation.mutate({ id: String(voidModalEntry.id), reason: voidReason }); }} disabled={!voidReason.trim() || voidMutation.isPending} className="btn-primary bg-orange-600 hover:bg-orange-700 disabled:opacity-50">تأكيد الإبطال</button>
            </div>
          </div>
        </Modal>
      )}

      <ConfirmDialog
        isOpen={!!deleteTarget}
        onClose={() => setDeleteTarget(null)}
        onConfirm={() => { if (deleteTarget) deleteMutation.mutate(String(deleteTarget.id)); }}
        title="حذف القيد"
        message={`هل أنت متأكد من حذف القيد رقم ${deleteTarget ? String(deleteTarget.entryNumber) : ''}؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        cancelText="إلغاء"
      />
    </div>
  );
}