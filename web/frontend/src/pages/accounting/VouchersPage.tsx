import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getVouchers, createVoucher, voidVoucher } from '@/api/accounting';
import type { Voucher } from '@/api/accounting';
import { getCustomers, getSuppliers } from '@/api/crm';
import { getBanks } from '@/api/payments';
import { StatsCard } from '@/components/ui/StatsCard';
import { Modal } from '@/components/ui/Modal';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/lib/utils';

const TYPE_LABELS: Record<string, string> = {
  RECEIPT: 'سند قبض',
  PAYMENT: 'سند صرف',
};

const METHOD_LABELS: Record<string, string> = {
  cash: 'نقداً',
  bank: 'بنك',
};

function statusBadge(status?: string | null) {
  if (status === 'Posted') {
    return <span className="badge-success">مرحّل</span>;
  }
  if (status === 'Voided') {
    return <span className="badge-danger">ملغي</span>;
  }
  return <span className="badge-secondary">{status || '—'}</span>;
}

export default function VouchersPage() {
  const toast = useToast();
  const queryClient = useQueryClient();
  const [voucherType, setVoucherType] = useState<'RECEIPT' | 'PAYMENT' | ''>('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const perPage = 15;
  const [showNewModal, setShowNewModal] = useState(false);
  const [voidTarget, setVoidTarget] = useState<Voucher | null>(null);
  const [voidReason, setVoidReason] = useState('');

  const params: Record<string, unknown> = { page, per_page: perPage };
  if (voucherType) params.voucher_type = voucherType;
  if (status) params.status = status;

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['vouchers', voucherType, status, page],
    queryFn: () => getVouchers(params),
  });

  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: getCustomers });
  const { data: suppliers } = useQuery({ queryKey: ['suppliers'], queryFn: getSuppliers });
  const { data: banks } = useQuery({ queryKey: ['banks'], queryFn: getBanks });

  const createMutation = useMutation({
    mutationFn: createVoucher,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      setShowNewModal(false);
      toast.success('تم إنشاء السند وترحيل قيده بنجاح');
      refetch();
    },
    onError: (err: any) => toast.error(err?.message || 'فشل إنشاء السند'),
  });

  const voidMutation = useMutation({
    mutationFn: (vars: { id: number; reason: string }) => voidVoucher(vars.id, vars.reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['vouchers'] });
      setVoidTarget(null);
      setVoidReason('');
      toast.success('تم إلغاء السند مع إنشاء قيد عكسي');
    },
    onError: (err: any) => toast.error(err?.message || 'فشل إلغاء السند'),
  });

  const items = data?.items || [];
  const totals = { RECEIPT: 0, PAYMENT: 0 };
  items.forEach((v) => {
    totals[v.voucher_type] += Number(v.amount || 0);
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="سندات القبض والصرف"
        subtitle="إنشاء وعرض سندات القبض (المدينون) والصرف (الدائنون) مع ترحيل فوري للقيود"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>}
        actions={<button onClick={() => setShowNewModal(true)} className="btn-primary">+ سند جديد</button>}
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatsCard title="إجمالي سندات القبض (المعروض)" value={totals.RECEIPT.toLocaleString()} />
        <StatsCard title="إجمالي سندات الصرف (المعروض)" value={totals.PAYMENT.toLocaleString()} />
        <StatsCard title="عدد السندات" value={String(data?.total ?? 0)} />
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap items-center gap-4">
        <label className="text-sm font-medium">نوع السند:</label>
        <select value={voucherType} onChange={(e) => { setVoucherType(e.target.value as any); setPage(1); }} className="select">
          <option value="">الكل</option>
          <option value="RECEIPT">سند قبض</option>
          <option value="PAYMENT">سند صرف</option>
        </select>
        <label className="text-sm font-medium">الحالة:</label>
        <select value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }} className="select">
          <option value="">الكل</option>
          <option value="Posted">مرحّل</option>
          <option value="Voided">ملغي</option>
        </select>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="table-header">
            <tr>
              <th className="px-4 py-3 text-right">رقم السند</th>
              <th className="px-4 py-3 text-right">النوع</th>
              <th className="px-4 py-3 text-right">التاريخ</th>
              <th className="px-4 py-3 text-right">الطرف</th>
              <th className="px-4 py-3 text-right">الطريقة</th>
              <th className="px-4 py-3 text-right">المبلغ</th>
              <th className="px-4 py-3 text-right">الحالة</th>
              <th className="px-4 py-3 text-right">إجراءات</th>
            </tr>
          </thead>
          <tbody>
            {items.map((v) => (
              <tr key={v.id} className="table-row">
                <td className="px-4 py-3 font-medium">{v.voucher_number}</td>
                <td className="px-4 py-3">{TYPE_LABELS[v.voucher_type]}</td>
                <td className="px-4 py-3">{v.voucher_date ? new Date(v.voucher_date).toLocaleDateString('ar') : '—'}</td>
                <td className="px-4 py-3">{v.partner_type === 'customer' ? 'عميل #' : v.partner_type === 'supplier' ? 'مورد #' : ''}{v.partner_id ?? ''}</td>
                <td className="px-4 py-3">{METHOD_LABELS[v.payment_method]}</td>
                <td className="px-4 py-3 font-medium">{Number(v.amount).toLocaleString()}</td>
                <td className="px-4 py-3">{statusBadge(v.status)}</td>
                <td className="px-4 py-3">
                  {v.status === 'Posted' && (
                    <button
                      onClick={() => setVoidTarget(v)}
                      className="btn-ghost btn-sm text-orange-600 dark:text-orange-400"
                    >
                      إلغاء
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {!isLoading && items.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-gray-500">لا توجد سندات</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {(data?.pages ?? 0) > 1 && (
        <div className="flex items-center justify-center gap-3">
          <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1} className="btn-secondary btn-sm disabled:opacity-40">السابق</button>
          <span>صفحة {page} من {data?.pages}</span>
          <button onClick={() => setPage((p) => p + 1)} disabled={page >= (data?.pages ?? 1)} className="btn-secondary btn-sm disabled:opacity-40">التالي</button>
        </div>
      )}

      {isLoading && <div className="text-center py-8 text-gray-600 dark:text-zinc-400">جاري التحميل...</div>}

      {/* New voucher modal */}
      <NewVoucherModal
        isOpen={showNewModal}
        onClose={() => setShowNewModal(false)}
        onSave={(payload) => createMutation.mutate(payload)}
        pending={createMutation.isPending}
        customers={customers?.items || []}
        suppliers={suppliers?.items || []}
        banks={banks?.items || []}
      />

      {/* Void confirmation */}
      <Modal isOpen={!!voidTarget} onClose={() => setVoidTarget(null)} title="إلغاء السند">
        <p className="text-sm text-gray-600 dark:text-zinc-400 mb-4">
          سيتم إلغاء السند <span className="font-bold">{voidTarget?.voucher_number}</span> مع إنشاء قيد عكسي تلقائياً. هل أنت متأكد؟
        </p>
        <textarea
          value={voidReason}
          onChange={(e) => setVoidReason(e.target.value)}
          rows={3}
          placeholder="سبب الإلغاء (إجباري)"
          className="input mb-4"
        />
        <div className="flex justify-end gap-2">
          <button type="button" onClick={() => setVoidTarget(null)} className="btn-secondary">إلغاء</button>
          <button
            type="button"
            disabled={!voidReason.trim() || voidMutation.isPending}
            onClick={() => voidTarget && voidMutation.mutate({ id: voidTarget.id, reason: voidReason })}
            className="btn-primary bg-orange-600 hover:bg-orange-700 disabled:opacity-50"
          >
            {voidMutation.isPending ? 'جاري الإلغاء...' : 'تأكيد الإلغاء'}
          </button>
        </div>
      </Modal>
    </div>
  );
}

interface NewVoucherModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (payload: Record<string, unknown>) => void;
  pending?: boolean;
  customers: any[];
  suppliers: any[];
  banks: any[];
}

function NewVoucherModal({ isOpen, onClose, onSave, pending, customers, suppliers, banks }: NewVoucherModalProps) {
  const [type, setType] = useState<'RECEIPT' | 'PAYMENT'>('RECEIPT');
  const [partnerId, setPartnerId] = useState('');
  const [amount, setAmount] = useState('');
  const [method, setMethod] = useState<'cash' | 'bank'>('cash');
  const [bankId, setBankId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [description, setDescription] = useState('');
  const [referenceNumber, setReferenceNumber] = useState('');

  const partnerOptions = type === 'RECEIPT' ? customers : suppliers;

  const reset = () => {
    setType('RECEIPT');
    setPartnerId('');
    setAmount('');
    setMethod('cash');
    setBankId('');
    setDate(new Date().toISOString().split('T')[0]);
    setDescription('');
    setReferenceNumber('');
  };

  const submit = () => {
    if (!partnerId || !amount || Number(amount) <= 0) return;
    const payload: Record<string, unknown> = {
      voucher_type: type,
      partner_type: type === 'RECEIPT' ? 'customer' : 'supplier',
      partner_id: Number(partnerId),
      amount: Number(amount),
      payment_method: method,
      voucher_date: date,
    };
    if (method === 'bank' && bankId) payload.bank_id = Number(bankId);
    if (description.trim()) payload.description = description.trim();
    if (referenceNumber.trim()) payload.reference_number = referenceNumber.trim();
    onSave(payload);
    reset();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="سند جديد">
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <label className="text-sm font-medium">نوع السند</label>
          <select value={type} onChange={(e) => setType(e.target.value as any)} className="select">
            <option value="RECEIPT">سند قبض (استلام حالي)</option>
            <option value="PAYMENT">سند صرف (دفع)</option>
          </select>
          <label className="text-sm font-medium">تاريخ السند</label>
          <input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="input" />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">الطرف</label>
          <select value={type === 'RECEIPT' ? 'customer' : 'supplier'} onChange={() => {}} disabled className="select w-full opacity-70">
            {type === 'RECEIPT'
              ? <option value="customer">عميل (مدين) — يُخصم من رصيد العميل</option>
              : <option value="supplier">مورد (دائن) — يُخصم من رصيد المورد</option>}
          </select>
          <select value={partnerId} onChange={(e) => setPartnerId(e.target.value)} className="select w-full mt-2">
            <option value="">اختر الطرف...</option>
            {partnerOptions.map((p: any) => (
              <option key={p.id} value={p.id}>{p.name || p.name_ar || `#${p.id}`}</option>
            ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium block mb-1">طريقة الدفع</label>
            <select value={method} onChange={(e) => setMethod(e.target.value as any)} className="select w-full">
              <option value="cash">نقداً (الصندوق 1111)</option>
              <option value="bank">بنك (1121)</option>
            </select>
          </div>
          {method === 'bank' && (
            <div>
              <label className="text-sm font-medium block mb-1">الحساب البنكي</label>
              <select value={bankId} onChange={(e) => setBankId(e.target.value)} className="select w-full">
                <option value="">—</option>
                {banks.map((b: any) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">المبلغ</label>
          <input type="number" min="0" step="0.01" value={amount} onChange={(e) => setAmount(e.target.value)} className="input w-full" placeholder="0.00" />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">المرجع (اختياري)</label>
          <input type="text" value={referenceNumber} onChange={(e) => setReferenceNumber(e.target.value)} className="input w-full" />
        </div>

        <div>
          <label className="text-sm font-medium block mb-1">البيان</label>
          <textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={2} className="input" />
        </div>

        <div className="flex justify-end gap-2 pt-2">
          <button type="button" className="btn-secondary" onClick={onClose}>إلغاء</button>
          <button type="button" className={cn('btn-primary', (!partnerId || !amount || Number(amount) <= 0 || pending) && 'disabled:opacity-50')} disabled={!partnerId || !amount || Number(amount) <= 0 || pending} onClick={submit}>
            {pending ? 'جاري الإنشاء...' : 'إنشاء وترحيل القيد'}
          </button>
        </div>
      </div>
    </Modal>
  );
}