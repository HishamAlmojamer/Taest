import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, put, post } from '@/api/client';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/lib/utils';

interface NumberingConfig {
  id: number;
  docType: string;
  name: string;
  nameAr?: string | null;
  prefix: string;
  suffix?: string | null;
  zeroPadding: number;
  includeYear: boolean;
  separator?: string | null;
  period: string;
  nextValue: number;
  isActive: boolean;
  preview: string;
}

const DOC_LABELS: Record<string, string> = {
  SALE: 'فاتورة مبيعات',
  PURCHASE: 'أمر شراء',
  CREDIT_NOTE: 'إشعار دائن',
  CUSTOMER_PAYMENT: 'سند قبض',
  SUPPLIER_PAYMENT: 'سند دفع',
  QUOTATION: 'عرض سعر',
  STOCK_TRANSFER: 'تحويل مخزني',
  SALES_RETURN: 'مرتجع مبيعات',
  PURCHASE_RETURN: 'مرتجع مشتريات',
};

interface EditForm {
  prefix: string;
  suffix: string;
  zeroPadding: number;
  includeYear: boolean;
  separator: string;
  period: string;
  isActive: boolean;
}

function toNumberingPayload(form: EditForm) {
  return {
    prefix: form.prefix,
    suffix: form.suffix || null,
    zero_padding: Number(form.zeroPadding),
    include_year: form.includeYear,
    separator: form.separator || '-',
    period: form.period,
    is_active: form.isActive,
  };
}

export default function NumberingPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [editing, setEditing] = useState<string | null>(null);
  const [form, setForm] = useState<EditForm | null>(null);
  const [resetValue, setResetValue] = useState<Record<string, string>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['settings-numbering'],
    queryFn: async () => get<{ items: NumberingConfig[]; total: number }>('/settings/numbering'),
  });

  const startEdit = (item: NumberingConfig) => {
    setEditing(item.docType);
    setForm({
      prefix: item.prefix ?? '',
      suffix: item.suffix ?? '',
      zeroPadding: item.zeroPadding,
      includeYear: item.includeYear,
      separator: item.separator ?? '-',
      period: item.period,
      isActive: item.isActive,
    });
  };

  const updateMutation = useMutation({
    mutationFn: ({ docType, payload }: { docType: string; payload: ReturnType<typeof toNumberingPayload> }) =>
      put(`/settings/numbering/${docType}`, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-numbering'] });
      toast.success('تم تحديث الترقيم بنجاح');
      setEditing(null);
      setForm(null);
    },
    onError: (error: any) => {
      toast.error('خطأ في الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const resetMutation = useMutation({
    mutationFn: ({ docType, nextValue }: { docType: string; nextValue: number }) =>
      post(`/settings/numbering/${docType}/reset`, { next_value: nextValue }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings-numbering'] });
      toast.success('تم إعادة تعيين العداد');
      setResetValue({});
    },
    onError: (error: any) => {
      toast.error('خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  if (isLoading) return <LoadingSpinner />;

  const items = data?.items || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="سياسة الترقيم"
        subtitle="تهيئة تسلسل أرقام المستندات لكل نوع (البادئة، السنة، عدد الخانات)"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        }
      />

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-100 dark:border-zinc-800 text-gray-500 dark:text-zinc-400 text-right">
                <th className="px-4 py-3 font-medium">المستند</th>
                <th className="px-4 py-3 font-medium">البادئة</th>
                <th className="px-4 py-3 font-medium">السنة</th>
                <th className="px-4 py-3 font-medium">الخانات</th>
                <th className="px-4 py-3 font-medium">التسلسل التالي</th>
                <th className="px-4 py-3 font-medium">المعاينة</th>
                <th className="px-4 py-3 font-medium">الحالة</th>
                <th className="px-4 py-3 font-medium">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.docType} className="border-b border-gray-50 dark:border-zinc-800/50 hover:bg-gray-50 dark:hover:bg-zinc-800/40">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-800 dark:text-zinc-200">{item.nameAr || DOC_LABELS[item.docType] || item.name}</div>
                    <div className="text-xs text-gray-400">{item.docType}</div>
                  </td>
                  <td className="px-4 py-3 font-mono text-gray-700 dark:text-zinc-300">{item.prefix}</td>
                  <td className="px-4 py-3">{item.includeYear ? 'نعم' : 'لا'}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-zinc-300">{item.zeroPadding}</td>
                  <td className="px-4 py-3 text-gray-700 dark:text-zinc-300">{item.nextValue}</td>
                  <td className="px-4 py-3">
                    <code className="px-2 py-0.5 bg-gray-100 dark:bg-zinc-800 rounded text-xs font-mono text-primary-700 dark:text-primary-400">
                      {item.preview}
                    </code>
                  </td>
                  <td className="px-4 py-3">
                    <span className={cn('px-2 py-0.5 rounded-full text-xs font-medium', item.isActive ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-400' : 'bg-gray-100 text-gray-500 dark:bg-zinc-800 dark:text-zinc-400')}>
                      {item.isActive ? 'مفعّل' : 'معطّل'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <button onClick={() => startEdit(item)} className="text-sm text-primary-600 hover:underline">
                        تعديل
                      </button>
                      {resetValue[item.docType] !== undefined && (
                        <button
                          onClick={() => resetMutation.mutate({ docType: item.docType, nextValue: Number(resetValue[item.docType]) })}
                          className={cn('text-sm px-2 py-1 rounded hover:underline', resetMutation.isPending ? 'text-gray-400' : 'text-amber-600')}
                        >
                          حفظ العداد: {resetValue[item.docType]}
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {editing && form && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
          <div className="bg-white dark:bg-zinc-900 rounded-2xl shadow-xl w-full max-w-lg p-6">
            <h3 className="text-lg font-semibold text-gray-800 dark:text-zinc-200 mb-4">
              تعديل الترقيم - {DOC_LABELS[editing] || editing}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="label">البادئة</label>
                <input className="input" value={form.prefix} onChange={(e) => setForm({ ...form, prefix: e.target.value })} placeholder="INV" />
              </div>
              <div>
                <label className="label">اللاحقة (اختياري)</label>
                <input className="input" value={form.suffix} onChange={(e) => setForm({ ...form, suffix: e.target.value })} />
              </div>
              <div>
                <label className="label">عدد الخانات</label>
                <input className="input" type="number" value={form.zeroPadding} onChange={(e) => setForm({ ...form, zeroPadding: Number(e.target.value) })} />
              </div>
              <div>
                <label className="label">الفاصل</label>
                <input className="input" value={form.separator} onChange={(e) => setForm({ ...form, separator: e.target.value })} />
              </div>
              <div>
                <label className="label">دورة الترقيم</label>
                <select className="input" value={form.period} onChange={(e) => setForm({ ...form, period: e.target.value })}>
                  <option value="YEAR">سنوية</option>
                  <option value="MONTH">شهرية</option>
                  <option value="NO_PERIOD">بدون دورة</option>
                </select>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <input id="inc-year" type="checkbox" checked={form.includeYear} onChange={(e) => setForm({ ...form, includeYear: e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-primary-600" />
                <label htmlFor="inc-year" className="text-sm text-gray-700 dark:text-zinc-300">تضمين السنة</label>
              </div>
              <div className="flex items-center gap-2 pt-6">
                <input id="is-active" type="checkbox" checked={form.isActive} onChange={(e) => setForm({ ...form, isActive: e.target.checked })} className="h-4 w-4 rounded border-gray-300 text-primary-600" />
                <label htmlFor="is-active" className="text-sm text-gray-700 dark:text-zinc-300">مفعل</label>
              </div>
            </div>
            <div className="mt-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">تعيين العداد التالي:</span>
                <input
                  className="input w-24"
                  type="number"
                  value={resetValue[editing] ?? ''}
                  onChange={(e) => setResetValue({ ...resetValue, [editing]: e.target.value })}
                  placeholder={String(items.find((i) => i.docType === editing)?.nextValue ?? 1)}
                />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => { setEditing(null); setForm(null); }} className="btn-secondary">إلغاء</button>
              <button
                onClick={() => updateMutation.mutate({ docType: editing, payload: toNumberingPayload(form) })}
                className="btn-primary"
                disabled={updateMutation.isPending}
              >
                {updateMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
