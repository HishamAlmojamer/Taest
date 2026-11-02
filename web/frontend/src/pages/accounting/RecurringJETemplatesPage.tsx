import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { EditableTable } from '@/components/ui/EditableTable';
import { formatDate, formatCurrency } from '@/lib/utils';
import {
  getRecurringJETemplates,
  createRecurringJETemplate,
  updateRecurringJETemplate,
  deleteRecurringJETemplate,
  runRecurringJETemplate,
  previewRecurringJETemplate,
  toggleRecurringJETemplate,
  getAccountsFlat,
} from '@/api/accounting';
import { getCurrencies } from '@/api/currencies';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

const EMPTY_FORM = { name: '', nameEn: '', description: '', frequency: 'MONTHLY', nextRunDate: '' };
const EMPTY_LINE = { accountId: '', debit: 0, credit: 0, description: '', partnerId: '', projectId: '', currencyId: '' };

const FREQUENCY_OPTIONS: Record<string, string> = {
  WEEKLY: 'أسبوعي',
  MONTHLY: 'شهري',
  QUARTERLY: 'ربع سنوي',
  YEARLY: 'سنوي',
  ANNUAL: 'سنوي',
};

function normalizeFreq(f: string): string {
  const up = String(f || 'MONTHLY').toUpperCase();
  if (up === 'WEEK') return 'WEEKLY';
  if (up === 'MONTH') return 'MONTHLY';
  if (up === 'QUARTER') return 'QUARTERLY';
  if (up === 'YEAR' || up === 'ANNUAL') return 'YEARLY';
  return up;
}

export default function RecurringJETemplatesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [lines, setLines] = useState<typeof EMPTY_LINE[]>([]);

  // Preview state
  const [previewTarget, setPreviewTarget] = useState<any>(null);
  const [previewData, setPreviewData] = useState<any>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [previewLoading, setPreviewLoading] = useState(false);

  const { data: templates = [], isLoading } = useQuery({
    queryKey: ['recurring-je-templates'],
    queryFn: () => getRecurringJETemplates(),
  });

  const { data: accounts = [] } = useQuery({
    queryKey: ['accounts-flat'],
    queryFn: () => getAccountsFlat(),
  });

  const { data: currencies = [] } = useQuery({
    queryKey: ['currencies'],
    queryFn: () => getCurrencies(),
  });

  const accountOptions = useMemo(
    () => (accounts as any[]).map((a: any) => ({ value: String(a.id), label: `${a.code} - ${a.name}` })),
    [accounts]
  );

  const currencyOptions = useMemo(
    () => (currencies as any[]).filter((c: any) => c.is_active !== false).map((c: any) => ({ value: String(c.id), label: `${c.code} - ${c.name || c.name_ar || ''}` })),
    [currencies]
  );

  const totalDebit = useMemo(() => lines.reduce((s, l) => s + (l.debit || 0), 0), [lines]);
  const totalCredit = useMemo(() => lines.reduce((s, l) => s + (l.credit || 0), 0), [lines]);
  const isBalanced = Math.abs(totalDebit - totalCredit) < 0.01;

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['recurring-je-templates'] });

  const saveMutation = useMutation({
    mutationFn: (payload: any) =>
      editing ? updateRecurringJETemplate(editing.id, payload) : createRecurringJETemplate(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_FORM); setLines([]); toast.success('تم حفظ القالب بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteRecurringJETemplate(id),
    onSuccess: () => { invalidate(); setShowDeleteConfirm(false); setDeleteTarget(null); toast.success('تم حذف القالب بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const runMutation = useMutation({
    mutationFn: (id: number) => runRecurringJETemplate(id),
    onSuccess: () => { invalidate(); setShowPreview(false); setPreviewTarget(null); setPreviewData(null); toast.success('تم تشغيل القالب وإنشاء القيد بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => toggleRecurringJETemplate(id),
    onSuccess: (res: any) => { invalidate(); toast.success(res?.is_active ? 'تم تفعيل القالب' : 'تم إيقاف القالب'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const parseTemplateData = (raw: string | null | undefined): typeof EMPTY_LINE[] => {
    if (!raw) return [];
    try {
      const parsed = JSON.parse(raw);
      const arr = parsed?.lines || [];
      return arr.map((l: any) => ({
        accountId: String(l.account_id ?? ''),
        debit: Number(l.debit || 0),
        credit: Number(l.credit || 0),
        description: l.description || '',
        partnerId: l.partner_id != null ? String(l.partner_id) : '',
        projectId: l.project_id != null ? String(l.project_id) : '',
        currencyId: l.currency_id != null ? String(l.currency_id) : '',
      }));
    } catch {
      return [];
    }
  };

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setLines([{ ...EMPTY_LINE }, { ...EMPTY_LINE }]); setShowModal(true); };
  const openEdit = (item: any) => {
    setEditing(item);
    const desc = item.description || '';
    setForm({
      name: item.name || '',
      nameEn: item.nameEn || item.name_en || '',
      description: desc,
      frequency: normalizeFreq(item.frequency || 'MONTHLY'),
      nextRunDate: item.nextRunDate || item.next_run_date || '',
    });
    const parsedLines = parseTemplateData(item.template_data);
    setLines(parsedLines.length ? parsedLines : [{ ...EMPTY_LINE }, { ...EMPTY_LINE }]);
    setShowModal(true);
  };

  const buildTemplateData = () => {
    const validLines = lines.filter((l) => l.accountId && (l.debit || l.credit));
    return {
      description: form.description || form.name,
      lines: validLines.map((l) => ({
        account_id: Number(l.accountId),
        debit: Number(l.debit || 0),
        credit: Number(l.credit || 0),
        description: l.description,
        partner_id: l.partnerId ? Number(l.partnerId) : null,
        project_id: l.projectId ? Number(l.projectId) : null,
        currency_id: l.currencyId ? Number(l.currencyId) : null,
      })),
    };
  };

  const handleSave = () => {
    const validLines = lines.filter((l) => l.accountId && (l.debit || l.credit));
    if (!validLines.length) {
      toast.error('يجب إضافة بند واحد على الأقل في بنود القيد');
      return;
    }
    saveMutation.mutate({
      name: form.name,
      name_en: form.nameEn,
      description: form.description,
      frequency: normalizeFreq(form.frequency),
      next_run_date: form.nextRunDate,
      template_data: buildTemplateData(),
    });
  };

  const handlePreview = async (item: any) => {
    setPreviewTarget(item);
    setPreviewData(null);
    setPreviewLoading(true);
    setShowPreview(true);
    try {
      const data = await previewRecurringJETemplate(Number(item.id));
      setPreviewData(data);
    } catch (e: any) {
      toast.error('خطأ: ' + (e?.response?.data?.detail || e.message));
      setShowPreview(false);
    } finally {
      setPreviewLoading(false);
    }
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'description', header: 'الوصف', render: (item) => <span className="text-gray-500 dark:text-zinc-400 text-sm">{String(item.description || '-')}</span> },
    { key: 'duration', header: 'عدد البنود', render: (item) => {
      try {
        const td = JSON.parse(String(item.template_data || '{}'));
        return <span className="text-sm">{Array.isArray(td.lines) ? td.lines.length : 0}</span>;
      } catch {
        return <span className="text-sm text-gray-400">0</span>;
      }
    }},
    { key: 'frequency', header: 'التكرار', render: (item) => {
      const freq = normalizeFreq(String(item.frequency || 'MONTHLY'));
      return <span className="px-2 py-1 rounded-full bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-400 text-xs font-medium">{FREQUENCY_OPTIONS[freq] || freq}</span>;
    }},
    { key: 'nextRunDate', header: 'التشغيل التالي', render: (item) => formatDate(String(item.nextRunDate || item.next_run_date || '')) },
    { key: 'lastRunDate', header: 'آخر تشغيل', render: (item) => formatDate(String(item.lastRunDate || item.last_run_date || '')) },
    { key: 'isActive', header: 'الحالة', render: (item) => (item.isActive !== false)
      ? <span className="badge-success">نشط</span>
      : <span className="badge-danger">موقوف</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex items-center gap-3">
        <button onClick={() => handlePreview(item)} className="text-blue-600 hover:underline text-sm">تشغيل الآن</button>
        <button onClick={() => toggleMutation.mutate(Number(item.id))} className="text-amber-600 hover:underline text-sm">{item.isActive !== false ? 'إيقاف' : 'تفعيل'}</button>
        <button onClick={() => openEdit(item)} className="text-blue-600 hover:underline text-sm">تعديل</button>
        <button onClick={() => { setDeleteTarget(item); setShowDeleteConfirm(true); }} className="text-red-600 hover:underline text-sm">حذف</button>
      </div>
    )},
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader title="قوالب القيود الدورية" subtitle="إدارة القوالب الدورية للقيود اليومية وتشغيلها تلقائياً أو يدوياً" icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>} actions={<button onClick={openCreate} className="btn-primary">+ قالب جديد</button>} />

      <DataTable
        columns={columns}
        data={templates as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={templates.length}
      />

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل قالب القيود الدورية' : 'قالب قيد دوري جديد'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الاسم *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} placeholder="إيجار شهري" />
            </div>
            <div>
              <label className="label">الاسم بالإنجليزية</label>
              <input value={form.nameEn} onChange={(e) => setForm({ ...form, nameEn: e.target.value })} className={inputClass} placeholder="Monthly Rent" />
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">التكرار *</label>
              <select value={form.frequency} onChange={(e) => setForm({ ...form, frequency: e.target.value })} className={inputClass}>
                <option value="WEEKLY">أسبوعي</option>
                <option value="MONTHLY">شهري</option>
                <option value="QUARTERLY">ربع سنوي</option>
                <option value="YEARLY">سنوي</option>
              </select>
            </div>
            <div>
              <label className="label">التشغيل التالي *</label>
              <input type="date" value={form.nextRunDate} onChange={(e) => setForm({ ...form, nextRunDate: e.target.value })} className={inputClass} />
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 dark:text-zinc-100 mb-2">بنود القيد</h4>
            <EditableTable
              columns={[
                { key: 'accountId', header: 'الحساب *', type: 'select', options: accountOptions },
                { key: 'debit', header: 'مدين', type: 'number' },
                { key: 'credit', header: 'دائن', type: 'number' },
                { key: 'description', header: 'الوصف', type: 'text' },
                { key: 'partnerId', header: 'الشريك (ID)', type: 'number' },
                { key: 'projectId', header: 'المشروع (ID)', type: 'number' },
                { key: 'currencyId', header: 'العملة', type: 'select', options: currencyOptions },
              ]}
              data={lines as unknown as Record<string, unknown>[]}
              onChange={(newData) => setLines(newData as typeof lines)}
              onAddRow={() => setLines([...lines, { ...EMPTY_LINE }])}
              onDeleteRow={(idx) => setLines(lines.filter((_, i) => i !== idx))}
            />
          </div>

          <div className="flex items-center justify-between p-3 rounded-lg bg-gray-50 dark:bg-zinc-800">
            <div className="flex gap-4 text-sm">
              <span className="text-gray-600 dark:text-zinc-400">المدين: <strong className="text-gray-900 dark:text-zinc-100">{formatCurrency(totalDebit)}</strong></span>
              <span className="text-gray-600 dark:text-zinc-400">الدائن: <strong className="text-gray-900 dark:text-zinc-100">{formatCurrency(totalCredit)}</strong></span>
            </div>
            <span className={`text-sm font-medium ${isBalanced ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
              {isBalanced ? 'متوازن' : 'غير متوازن'}
            </span>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={handleSave} className="btn-primary" disabled={!form.name || !form.nextRunDate || saveMutation.isPending}>
              {saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Preview & Run Modal */}
      <Modal isOpen={showPreview} onClose={() => { setShowPreview(false); setPreviewTarget(null); setPreviewData(null); }} title="معاينة القيد الناتج" size="lg">
        {previewLoading || !previewData ? (
          <div className="py-10 text-center text-gray-400 dark:text-zinc-500">جاري تحضير المعاينة...</div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-gray-500 dark:text-zinc-400">القالب:</span> <strong>{String(previewData.name)}</strong></div>
              <div><span className="text-gray-500 dark:text-zinc-400">الوصف:</span> <strong>{String(previewData.description)}</strong></div>
              <div><span className="text-gray-500 dark:text-zinc-400">تاريخ القيد:</span> <strong>{formatDate(String(previewData.entry_date))}</strong></div>
              <div><span className="text-gray-500 dark:text-zinc-400">الحالة:</span> <strong className="text-emerald-600">مرحّل (Posted)</strong></div>
            </div>

            <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-zinc-700">
              <table className="w-full text-sm">
                <thead>
                  <tr className="table-header">
                    <th className="px-4 py-2 text-right text-xs font-semibold">الحساب</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold">الوصف</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold">مدين</th>
                    <th className="px-4 py-2 text-right text-xs font-semibold">دائن</th>
                  </tr>
                </thead>
                <tbody>
                  {(previewData.lines || []).map((l: any, idx: number) => (
                    <tr key={idx} className="table-row">
                      <td className="px-4 py-2">
                        <AccountCell accountId={l.account_id} accounts={accounts} />
                      </td>
                      <td className="px-4 py-2 text-gray-600 dark:text-zinc-400">{String(l.description || '')}</td>
                      <td className="px-4 py-2 text-gray-900 dark:text-zinc-100">{Number(l.debit) > 0 ? formatCurrency(Number(l.debit)) : '-'}</td>
                      <td className="px-4 py-2 text-gray-900 dark:text-zinc-100">{Number(l.credit) > 0 ? formatCurrency(Number(l.credit)) : '-'}</td>
                    </tr>
                  ))}
                  <tr className="bg-gray-50 dark:bg-zinc-800/50 font-bold">
                    <td className="px-4 py-2" colSpan={2}>الإجمالي</td>
                    <td className="px-4 py-2 text-gray-900 dark:text-zinc-100">{formatCurrency(previewData.total_debit)}</td>
                    <td className="px-4 py-2 text-gray-900 dark:text-zinc-100">{formatCurrency(previewData.total_credit)}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="flex items-center justify-between">
              <span className={`text-sm font-medium ${previewData.balanced ? 'text-emerald-600 dark:text-emerald-400' : 'text-red-600 dark:text-red-400'}`}>
                {previewData.balanced ? 'القيد متوازن' : 'القيد غير متوازن — لا يمكن الترحيل'}
              </span>
              <span className="text-sm text-gray-500 dark:text-zinc-400">التشغيل التالي بعد التنفيذ: {formatDate(String(previewData.next_run_date || ''))}</span>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button type="button" onClick={() => setShowPreview(false)} className="btn-secondary">إلغاء</button>
              <button
                type="button"
                onClick={() => runMutation.mutate(Number(previewTarget.id))}
                disabled={!previewData.balanced || runMutation.isPending}
                className="btn-primary disabled:opacity-50"
              >
                {runMutation.isPending ? 'جاري التنفيذ...' : 'تأكيد وتشغيل القيد'}
              </button>
            </div>
          </div>
        )}
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="حذف القالب"
        message={`هل أنت متأكد من حذف "${deleteTarget?.name || ''}"؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}

function AccountCell({ accountId, accounts }: { accountId: number; accounts: any[] }) {
  const acc = (accounts as any[]).find((a: any) => String(a.id) === String(accountId));
  return <span className="font-medium text-primary-600 dark:text-primary-400">{acc ? `${acc.code} - ${acc.name}` : `#${accountId}`}</span>;
}
