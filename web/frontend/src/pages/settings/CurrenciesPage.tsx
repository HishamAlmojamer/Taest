import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import ExcelExportButton from '@/components/excel/ExcelExportButton';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { useToast } from '@/components/ui/Toast';
import { getCurrencies, createCurrency, updateCurrency, deleteCurrency, getExchangeRates, createExchangeRate, convertCurrency } from '@/api/currencies';

const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

const EMPTY_CURRENCY = { code: '', name: '', nameAr: '', symbol: '', decimalPlaces: 2, isBaseCurrency: false };
const EMPTY_RATE = { fromCurrencyCode: '', toCurrencyCode: '', rate: '', effectiveDate: '', expiryDate: '' };

type Tab = 'currencies' | 'rates' | 'converter';

export default function CurrenciesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [activeTab, setActiveTab] = useState<Tab>('currencies');
  const [showModal, setShowModal] = useState(false);
  const [showRateModal, setShowRateModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [editing, setEditing] = useState<any>(null);
  const [deleteTarget, setDeleteTarget] = useState<any>(null);
  const [form, setForm] = useState(EMPTY_CURRENCY);
  const [rateForm, setRateForm] = useState(EMPTY_RATE);

  const [convertAmount, setConvertAmount] = useState('');
  const [convertFrom, setConvertFrom] = useState('');
  const [convertTo, setConvertTo] = useState('');
  const [convertResult, setConvertResult] = useState<any>(null);

  const { data: currencies = [], isLoading } = useQuery({
    queryKey: ['currencies'],
    queryFn: () => getCurrencies(),
  });

  const { data: rates = [] } = useQuery({
    queryKey: ['exchange-rates'],
    queryFn: () => getExchangeRates(),
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['currencies'] });
    queryClient.invalidateQueries({ queryKey: ['exchange-rates'] });
  };

  const saveCurrencyMutation = useMutation({
    mutationFn: (payload: any) =>
      editing ? updateCurrency(editing.id, payload) : createCurrency(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); setForm(EMPTY_CURRENCY); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteCurrencyMutation = useMutation({
    mutationFn: (id: number) => deleteCurrency(id),
    onSuccess: () => { invalidate(); setShowDeleteConfirm(false); setDeleteTarget(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const saveRateMutation = useMutation({
    mutationFn: (payload: any) => createExchangeRate(payload),
    onSuccess: () => { invalidate(); setShowRateModal(false); setRateForm(EMPTY_RATE); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const openCreate = () => { setEditing(null); setForm(EMPTY_CURRENCY); setShowModal(true); };
  const openEdit = (item: any) => {
    setEditing(item);
    setForm({ code: item.code || '', name: item.name || '', nameAr: item.nameAr || item.name_ar || '', symbol: item.symbol || '', decimalPlaces: item.decimalPlaces ?? item.decimal_places ?? 2, isBaseCurrency: item.isBaseCurrency ?? item.is_base_currency ?? false });
    setShowModal(true);
  };

  const currencyColumns: Column<Record<string, unknown>>[] = [
    { key: 'code', header: 'الكود', render: (item) => <span className="font-medium">{String(item.code)}</span> },
    { key: 'name', header: 'الاسم', render: (item) => String(item.name) },
    { key: 'symbol', header: 'الرمز', render: (item) => String(item.symbol || '-') },
    { key: 'decimalPlaces', header: 'الأرقام العشرية', render: (item) => String(item.decimalPlaces ?? item.decimal_places ?? 0) },
    { key: 'isBaseCurrency', header: 'أساسية', render: (item) => (item.isBaseCurrency || item.is_base_currency) ? <span className="badge-success">نعم</span> : <span className="text-gray-400">لا</span> },
    { key: 'isActive', header: 'الحالة', render: (item) => (item.isActive !== false) ? <span className="badge-success">نشط</span> : <span className="badge-danger">غير نشط</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex items-center gap-2">
        <button onClick={() => openEdit(item)} className="text-blue-600 hover:underline text-sm">تعديل</button>
        <button onClick={() => { setDeleteTarget(item); setShowDeleteConfirm(true); }} className="text-red-600 hover:underline text-sm">حذف</button>
      </div>
    )},
  ];

  const rateColumns: Column<Record<string, unknown>>[] = [
    { key: 'fromCurrencyCode', header: 'من', render: (item) => <span className="font-medium">{String(item.fromCurrencyCode || item.from_currency_code || '')}</span> },
    { key: 'toCurrencyCode', header: 'إلى', render: (item) => String(item.toCurrencyCode || item.to_currency_code || '') },
    { key: 'rate', header: 'السعر', render: (item) => Number(item.rate).toFixed(4) },
    { key: 'effectiveDate', header: 'ساري من', render: (item) => String(item.effectiveDate || item.effective_date || '-') },
    { key: 'expiryDate', header: 'ساري حتى', render: (item) => String(item.expiryDate || item.expiry_date || '-') },
  ];

  const tabs: { key: Tab; label: string }[] = [
    { key: 'currencies', label: 'العملات' },
    { key: 'rates', label: 'أسعار الصرف' },
    { key: 'converter', label: 'محوّل العملات' },
  ];

  const handleConvert = async () => {
    if (!convertAmount || !convertFrom || !convertTo) return;
    const res = await convertCurrency(Number(convertAmount), convertFrom, convertTo);
    setConvertResult(res);
  };

  if (isLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="العملات وأسعار الصرف"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        actions={<div className="flex items-center gap-2">
          <ExcelExportButton url="/excel/exports/currencies" filename="currencies.xlsx" label="تصدير العملات" />
        </div>}
      />

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl bg-gray-100 dark:bg-zinc-800 p-1">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-white dark:bg-zinc-700 text-gray-900 dark:text-zinc-100 shadow-sm'
                : 'text-gray-500 dark:text-zinc-400 hover:text-gray-700 dark:hover:text-zinc-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Currencies Tab */}
      {activeTab === 'currencies' && (
        <>
          <div className="flex justify-end">
            <button onClick={openCreate} className="btn-primary">+ عملة جديدة</button>
          </div>
          <DataTable
            columns={currencyColumns}
            data={currencies as unknown as Record<string, unknown>[]}
            loading={isLoading}
            totalItems={currencies.length}
          />
        </>
      )}

      {/* Exchange Rates Tab */}
      {activeTab === 'rates' && (
        <>
          <div className="flex justify-end">
            <button onClick={() => { setRateForm(EMPTY_RATE); setShowRateModal(true); }} className="btn-primary">+ سعر صرف جديد</button>
          </div>
          <DataTable
            columns={rateColumns}
            data={rates as unknown as Record<string, unknown>[]}
            loading={false}
            totalItems={rates.length}
          />
        </>
      )}

      {/* Converter Tab */}
      {activeTab === 'converter' && (
        <div className="card p-6 max-w-lg">
          <div className="space-y-4">
            <div>
              <label className="label">المبلغ</label>
              <input type="number" value={convertAmount} onChange={(e) => setConvertAmount(e.target.value)} className={inputClass} placeholder="0.00" />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">من عملة</label>
                <select value={convertFrom} onChange={(e) => setConvertFrom(e.target.value)} className={inputClass}>
                  <option value="">اختر</option>
                  {(currencies as any[]).map((c: any) => <option key={c.id} value={c.code}>{c.code} - {c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="label">إلى عملة</label>
                <select value={convertTo} onChange={(e) => setConvertTo(e.target.value)} className={inputClass}>
                  <option value="">اختر</option>
                  {(currencies as any[]).map((c: any) => <option key={c.id} value={c.code}>{c.code} - {c.name}</option>)}
                </select>
              </div>
            </div>
            <button onClick={handleConvert} disabled={!convertAmount || !convertFrom || !convertTo} className="btn-primary w-full disabled:opacity-50">
              تحويل
            </button>
            {convertResult && (
              <div className="p-4 rounded-xl bg-primary-50 dark:bg-primary-500/10 text-center">
                <p className="text-sm text-gray-500 dark:text-zinc-400">النتيجة</p>
                <p className="text-2xl font-bold text-primary-600 dark:text-primary-400">{Number(convertResult.result || convertResult.converted_amount || 0).toFixed(2)} {convertTo}</p>
                <p className="text-xs text-gray-400 dark:text-zinc-500 mt-1">السعر: {Number(convertResult.rate || 0).toFixed(4)}</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Currency Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل عملة' : 'عملة جديدة'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الكود *</label>
              <input value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className={inputClass} placeholder="USD" disabled={!!editing} />
            </div>
            <div>
              <label className="label">الاسم *</label>
              <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className={inputClass} placeholder="US Dollar" />
            </div>
            <div>
              <label className="label">الاسم بالعربي</label>
              <input value={form.nameAr} onChange={(e) => setForm({ ...form, nameAr: e.target.value })} className={inputClass} placeholder="دولار أمريكي" />
            </div>
            <div>
              <label className="label">الرمز</label>
              <input value={form.symbol} onChange={(e) => setForm({ ...form, symbol: e.target.value })} className={inputClass} placeholder="$" />
            </div>
            <div>
              <label className="label">الأرقام العشرية</label>
              <input type="number" value={form.decimalPlaces} onChange={(e) => setForm({ ...form, decimalPlaces: Number(e.target.value) })} className={inputClass} min={0} max={8} />
            </div>
            <div className="flex items-center gap-2 pt-6">
              <input type="checkbox" id="isBase" checked={form.isBaseCurrency} onChange={(e) => setForm({ ...form, isBaseCurrency: e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500" />
              <label htmlFor="isBase" className="text-sm text-gray-700 dark:text-zinc-300">العملة الأساسية</label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowModal(false); setEditing(null); }} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={() => saveCurrencyMutation.mutate(form)} className="btn-primary" disabled={!form.code || !form.name || saveCurrencyMutation.isPending}>
              {saveCurrencyMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Exchange Rate Modal */}
      <Modal isOpen={showRateModal} onClose={() => setShowRateModal(false)} title="سعر صرف جديد" size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">من عملة *</label>
              <select value={rateForm.fromCurrencyCode} onChange={(e) => setRateForm({ ...rateForm, fromCurrencyCode: e.target.value })} className={inputClass}>
                <option value="">اختر</option>
                {(currencies as any[]).map((c: any) => <option key={c.id} value={c.code}>{c.code} - {c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">إلى عملة *</label>
              <select value={rateForm.toCurrencyCode} onChange={(e) => setRateForm({ ...rateForm, toCurrencyCode: e.target.value })} className={inputClass}>
                <option value="">اختر</option>
                {(currencies as any[]).map((c: any) => <option key={c.id} value={c.code}>{c.code} - {c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">السعر *</label>
              <input type="number" step="any" value={rateForm.rate} onChange={(e) => setRateForm({ ...rateForm, rate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">ساري من</label>
              <input type="date" value={rateForm.effectiveDate} onChange={(e) => setRateForm({ ...rateForm, effectiveDate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">ساري حتى</label>
              <input type="date" value={rateForm.expiryDate} onChange={(e) => setRateForm({ ...rateForm, expiryDate: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => setShowRateModal(false)} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={() => saveRateMutation.mutate({ from_currency_code: rateForm.fromCurrencyCode, to_currency_code: rateForm.toCurrencyCode, rate: Number(rateForm.rate), effective_date: rateForm.effectiveDate, expiry_date: rateForm.expiryDate })} className="btn-primary" disabled={!rateForm.fromCurrencyCode || !rateForm.toCurrencyCode || !rateForm.rate || saveRateMutation.isPending}>
              {saveRateMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Delete Confirm */}
      <ConfirmDialog
        isOpen={showDeleteConfirm}
        onClose={() => { setShowDeleteConfirm(false); setDeleteTarget(null); }}
        onConfirm={() => deleteTarget && deleteCurrencyMutation.mutate(deleteTarget.id)}
        title="حذف العملة"
        message={`هل أنت متأكد من حذف العملة "${deleteTarget?.name || ''}"؟ لا يمكن التراجع عن هذا الإجراء.`}
        confirmText="حذف"
        isLoading={deleteCurrencyMutation.isPending}
      />
    </div>
  );
}
