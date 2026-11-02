import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import ExcelExportButton from '@/components/excel/ExcelExportButton';
import ExcelImportButton from '@/components/excel/ExcelImportButton';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';
import { getTaxRates, createTaxRate, updateTaxRate, deleteTaxRate } from '@/api/taxes';

const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

const EMPTY_FORM = { code: '', name: '', nameAr: '', rate: '', taxType: 'VAT', appliesTo: 'BOTH', isRecoveryAllowed: false, glAccountCode: '', description: '' };

const TAX_TYPES: Record<string, string> = { VAT: 'ضريبة القيمة المضافة', GST: 'ضريبة السلع والخدمات', WITHHOLDING: 'ضريبة الاقتطاع', EXEMPT: 'معفى من الضريبة' };
const APPLIES_TO: Record<string, string> = { SALES: 'المبيعات', PURCHASE: 'المشتريات', BOTH: 'الكل' };

export default function TaxRatesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const { data: taxRates = [], isLoading } = useQuery({
    queryKey: ['tax-rates'],
    queryFn: () => getTaxRates(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['tax-rates'] });

  const saveMutation = useMutation({
    mutationFn: (payload: any) =>
      editing ? updateTaxRate(editing.id, payload) : createTaxRate(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_FORM); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteTaxRate(id),
    onSuccess: () => { invalidate(); setShowDeleteConfirm(false); setDeleteTarget(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const openCreate = () => { setEditing(null); setForm(EMPTY_FORM); setShowModal(true); };
  const openEdit = (item: any) => {
    setEditing(item);
    setForm({
      code: item.code || '',
      name: item.name || '',
      nameAr: item.nameAr || item.name_ar || '',
      rate: String(item.rate ?? ''),
      taxType: item.taxType || item.tax_type || 'VAT',
      appliesTo: item.appliesTo || item.applies_to || 'BOTH',
      isRecoveryAllowed: item.isRecoveryAllowed ?? item.is_recovery_allowed ?? false,
      glAccountCode: item.glAccountCode || item.gl_account_code || '',
      description: item.description || '',
    });
    setShowModal(true);
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-medium">{String(item.code)}</span> },
    { key: 'name', header: 'الاسم', render: (item) => String(item.name) },
    { key: 'rate', header: 'النسبة %', render: (item) => `${Number(item.rate || 0)}%` },
    { key: 'taxType', header: 'النوع', render: (item) => TAX_TYPES[String(item.taxType || item.tax_type)] || String(item.taxType || item.tax_type || '') },
    { key: 'appliesTo', header: 'ينطبق على', render: (item) => APPLIES_TO[String(item.appliesTo || item.applies_to)] || String(item.appliesTo || item.applies_to || '') },
    { key: 'isRecoveryAllowed', header: 'الاسترداد', render: (item) => (item.isRecoveryAllowed || item.is_recovery_allowed) ? <span className="badge-success">نعم</span> : <span className="text-gray-400">لا</span> },
    { key: 'glAccountCode', header: 'حساب الدفتر', render: (item) => <span className="font-mono text-sm">{String(item.glAccountCode || item.gl_account_code || '-')}</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => (item.isActive !== false) ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex items-center gap-2">
        <button onClick={() => openEdit(item)} className="text-blue-600 hover:underline text-sm">تعديل</button>
        <button onClick={() => { setDeleteTarget(item); setShowDeleteConfirm(true); }} className="text-red-600 hover:underline text-sm">حذف</button>
      </div>
    )},
  ];

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="نِسب الضرائب"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>}
        actions={<>
          <ExcelExportButton url="/excel/exports/tax-rates" filename="tax-rates.xlsx" label="تصدير النسب" />
          <ExcelImportButton url="/excel/imports/tax-rates" label="استيراد" onSuccess={invalidate} />
          <button onClick={openCreate} className="btn-primary">+ نسبة ضريبة جديدة</button>
        </>}
      />

      <DataTable
        columns={columns}
        data={taxRates as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={taxRates.length}
      />

      {/* Create/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل نسبة الضريبة' : 'نسبة ضريبة جديدة'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الكود *</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} placeholder="VAT15" disabled={!!editing} />
            </div>
            <div>
              <label className="label">الاسم *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} placeholder="VAT 15%" />
            </div>
            <div>
              <label className="label">الاسم بالعربي</label>
              <input value={form.nameAr} onChange={(e) => setForm({ ...form, nameAr: e.target.value })} className={inputClass} placeholder="ضريبة القيمة المضافة 15%" />
            </div>
            <div>
              <label className="label">النسبة (%) *</label>
              <input type="number" step="any" min="0" max="100" value={form.rate} onChange={(e) => setForm({ ...form, rate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">النوع *</label>
              <select value={form.taxType} onChange={(e) => setForm({ ...form, taxType: e.target.value })} className={inputClass}>
                <option value="VAT">ضريبة القيمة المضافة</option>
                <option value="GST">ضريبة السلع والخدمات</option>
                <option value="WITHHOLDING">ضريبة الاقتطاع</option>
                <option value="EXEMPT">معفى من الضريبة</option>
              </select>
            </div>
            <div>
              <label className="label">ينطبق على *</label>
              <select value={form.appliesTo} onChange={(e) => setForm({ ...form, appliesTo: e.target.value })} className={inputClass}>
                <option value="SALES">المبيعات</option>
                <option value="PURCHASE">المشتريات</option>
                <option value="BOTH">الكل</option>
              </select>
            </div>
            <div>
              <label className="label">حساب الدفتر</label>
              <input value={form.glAccountCode} onChange={(e) => setForm({ ...form, glAccountCode: e.target.value })} className={inputClass} placeholder="2110" />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input type="checkbox" id="recovery" checked={form.isRecoveryAllowed} onChange={(e) => setForm({ ...form, isRecoveryAllowed: e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
              <label htmlFor="recovery" className="text-sm text-gray-700 dark:text-zinc-300">يسمح بالاسترداد</label>
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={() => saveMutation.mutate({ code: form.code, name: form.name, name_ar: form.nameAr, rate: Number(form.rate), tax_type: form.taxType, applies_to: form.appliesTo, is_recovery_allowed: form.isRecoveryAllowed, gl_account_code: form.glAccountCode, description: form.description })} className="btn-primary" disabled={!form.code || !form.name || !form.rate || saveMutation.isPending}>
              {saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
        onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        title="حذف نسبة الضريبة"
        message={`هل أنت متأكد من حذف "${deleteTarget?.name || ''}"؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        isLoading={deleteMutation.isPending}
      />
    </div>
  );
}
