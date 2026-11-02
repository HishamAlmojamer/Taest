import { useState, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { useToast } from '@/components/ui/Toast';
import { formatCurrency, formatDate } from '@/lib/utils';
import {
  getCheques,
  getChequeSummary,
  createCheque,
  transitionCheque,
  bulkDepositCheques,
  type Cheque,
} from '@/api/cheques';
import { getBanks, type Bank } from '@/api/payments';

const STATUS_LABELS: Record<string, { label: string; badge: string }> = {
  on_hand: { label: 'مسجل', badge: 'badge-info' },
  deposited: { label: 'مودع بالبنك', badge: 'badge-warning' },
  under_collection: { label: 'قيد التحصيل', badge: 'badge-warning' },
  cleared: { label: 'محصل', badge: 'badge-success' },
  returned: { label: 'معاد', badge: 'badge-danger' },
  stopped: { label: 'موقوف', badge: 'badge-danger' },
  cancelled: { label: 'ملغي', badge: 'badge-danger' },
  replaced: { label: 'مستبدل', badge: 'badge-secondary' },
};

const TYPE_LABELS: Record<string, string> = {
  received: 'شيك مقبوض',
  issued: 'شيك مصروف',
};

export default function ChequesPage() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const [filterType, setFilterType] = useState<string>('');
  const [filterStatus, setFilterStatus] = useState<string>('');
  const [showCreate, setShowCreate] = useState(false);
  const [createType, setCreateType] = useState<'received' | 'issued'>('received');
  const [showTransition, setShowTransition] = useState<Cheque | null>(null);
  const [showBulk, setShowBulk] = useState(false);
  const [bulkSelected, setBulkSelected] = useState<number[]>([]);
  const [bulkBankId, setBulkBankId] = useState<number>(0);

  const { register, handleSubmit, reset } = useForm();

  const { data: cheques, isLoading } = useQuery({
    queryKey: ['cheques', filterType, filterStatus],
    queryFn: () => getCheques({ cheque_type: filterType || undefined, status: filterStatus || undefined, per_page: 100 }),
  });

  const { data: summary } = useQuery({ queryKey: ['cheques-summary'], queryFn: getChequeSummary });

  const { data: banksData } = useQuery({ queryKey: ['banks'], queryFn: getBanks });
  const banks: Bank[] = banksData?.items || [];

  const createMutation = useMutation({
    mutationFn: createCheque,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['cheques'] });
      queryClient.invalidateQueries({ queryKey: ['cheques-summary'] });
      setShowCreate(false);
      reset();
      toast.success(`تم إنشاء الشيك ${res.cheque_number} بنجاح`);
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const transitionMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Record<string, unknown> }) => transitionCheque(id, data),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['cheques'] });
      queryClient.invalidateQueries({ queryKey: ['cheques-summary'] });
      setShowTransition(null);
      toast.success(res.message);
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const bulkMutation = useMutation({
    mutationFn: bulkDepositCheques,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['cheques'] });
      queryClient.invalidateQueries({ queryKey: ['cheques-summary'] });
      setShowBulk(false);
      setBulkSelected([]);
      setBulkBankId(0);
      toast.success(res.message);
    },
    onError: (error: any) => {
      toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const items = cheques?.items || [];
  const rows = useMemo(
    () => items.map((c) => ({ ...c, statusBadge: STATUS_LABELS[c.status]?.badge, typeLabel: TYPE_LABELS[c.cheque_type] })),
    [items],
  );

  const receivableCheques = items.filter((c) => c.cheque_type === 'received' && c.status === 'on_hand');

  const summaryCards = useMemo(() => {
    const received = summary?.received || {};
    const issued = summary?.issued || {};
    return [
      { label: 'شيكات مقبوضة', value: Object.values(received).reduce((a, b) => a + b, 0), color: 'text-primary-600' },
      { label: 'شيكات مصروفة', value: Object.values(issued).reduce((a, b) => a + b, 0), color: 'text-amber-600' },
      { label: 'شيكات قيد التحصيل', value: (received.under_collection || 0) + (received.deposited || 0), color: 'text-emerald-600' },
      { label: 'شيكات محصلة', value: (received.cleared || 0) + (issued.cleared || 0), color: 'text-green-600' },
      { label: 'شيكات معادة/موقوفة', value: (received.returned || 0) + (issued.returned || 0) + (received.stopped || 0) + (issued.stopped || 0), color: 'text-red-600' },
    ];
  }, [summary]);

  const transitionTargets = showTransition
    ? Object.entries(TRANSITIONS[showTransition.status] || {}).map(([status, label]) => ({ status, label }))
    : [];

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'chequeNumber',
      header: 'رقم الشيك',
      render: (item) => (
        <div className="flex flex-col">
          <span className="font-mono font-medium">{String(item.chequeNumber)}</span>
          <span className="text-xs text-gray-500">{String(item.typeLabel)}</span>
        </div>
      ),
    },
    {
      key: 'party',
      header: 'الطرف',
      render: (item) => (
        <span className="font-medium">{String(item.payerName || item.payeeName || '—')}</span>
      ),
    },
    {
      key: 'amount',
      header: 'المبلغ',
      sortable: true,
      render: (item) => <span className="font-bold">{formatCurrency(Number(item.amount))}</span>,
    },
    {
      key: 'bankName',
      header: 'البنك',
      render: (item) => <span className="text-sm text-gray-700 dark:text-zinc-300">{String(item.bankName || '—')}</span>,
    },
    {
      key: 'dueDate',
      header: 'تاريخ الاستحقاق',
      render: (item) => <span className="text-sm">{item.dueDate ? formatDate(String(item.dueDate)) : '—'}</span>,
    },
    {
      key: 'status',
      header: 'الحالة',
      render: (item) => {
        const meta = STATUS_LABELS[String(item.status)];
        return meta ? <span className={meta.badge}>{meta.label}</span> : <span>{String(item.status)}</span>;
      },
    },
    {
      key: 'actions',
      header: 'إجراءات',
      render: (item) => {
        const cheque = item as unknown as Cheque;
        const transitions = TRANSITIONS[cheque.status] || {};
        const count = Object.keys(transitions).length;
        return count > 0 ? (
          <button
            onClick={() => setShowTransition(cheque)}
            className="btn-secondary btn-sm"
          >
            تغيير الحالة
          </button>
        ) : (
          <span className="text-xs text-gray-400">—</span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة الشيكات"
        subtitle="دورة حياة الشيكات المقبوضة والمصروفة"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        actions={
          <>
            {receivableCheques.length > 0 && (
              <button onClick={() => setShowBulk(true)} className="btn-secondary">
                إيداع مجمع ({receivableCheques.length})
              </button>
            )}
            <button onClick={() => { setCreateType('received'); setShowCreate(true); }} className="btn-primary">
              + شيك مقبوض
            </button>
            <button onClick={() => { setCreateType('issued'); setShowCreate(true); }} className="btn-primary">
              + شيك مصروف
            </button>
          </>
        }
      />

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
        {summaryCards.map((card) => (
          <div key={card.label} className="card p-4">
            <div className="text-sm text-gray-500 dark:text-zinc-400">{card.label}</div>
            <div className={`text-2xl font-bold ${card.color}`}>{card.value}</div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3">
        <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="input w-44">
          <option value="">كل الأنواع</option>
          <option value="received">شيكات مقبوضة</option>
          <option value="issued">شيكات مصروفة</option>
        </select>
        <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="input w-44">
          <option value="">كل الحالات</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v.label}</option>
          ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={rows as unknown as Record<string, unknown>[]}
        loading={isLoading}
        totalItems={items.length}
        page={1}
        pageSize={100}
        onPageChange={() => {}}
        emptyTitle="لا توجد شيكات"
        emptyDescription="أنشئ شيكاً جديداً من الأزرار أعلاه"
      />

      {/* Create modal */}
      <Modal isOpen={showCreate} onClose={() => { setShowCreate(false); reset(); }} title={createType === 'received' ? 'شيك مقبوض جديد' : 'شيك مصروف جديد'} size="lg">
        <form onSubmit={handleSubmit((d) => {
          createMutation.mutate({
            cheque_type: createType,
            cheque_number: d.chequeNumber || undefined,
            amount: Number(d.amount),
            payer_name: createType === 'received' ? d.partyName : undefined,
            payee_name: createType === 'issued' ? d.partyName : undefined,
            bank_id: d.bankId ? Number(d.bankId) : undefined,
            bank_name: d.bankId ? (banks.find((b) => b.id === Number(d.bankId))?.name || undefined) : undefined,
            issue_date: d.issueDate || undefined,
            due_date: d.dueDate || undefined,
            description: d.description || undefined,
          } as never);
        })} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">{createType === 'received' ? 'اسم الدافع (العميل)' : 'اسم المستفيد (المورد)'}</label>
              <input {...register('partyName', { required: true })} className="input" placeholder={createType === 'received' ? 'مثال: محمد علي' : 'مثال: شركة الأمل'} />
            </div>
            <div>
              <label className="label">المبلغ</label>
              <input {...register('amount', { required: true })} type="number" step="0.01" min="0" className="input" placeholder="0.00" />
            </div>
            <div>
              <label className="label">رقم الشيك (اختياري)</label>
              <input {...register('chequeNumber')} className="input" placeholder="يُولَّد تلقائياً إن تُرك" />
            </div>
            <div>
              <label className="label">البنك</label>
              <select {...register('bankId')} className="input" defaultValue="">
                <option value="">— اختر البنك —</option>
                {banks.map((b) => (
                  <option key={b.id} value={b.id}>{b.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">تاريخ الإصدار</label>
              <input {...register('issueDate')} type="date" className="input" />
            </div>
            <div>
              <label className="label">تاريخ الاستحقاق</label>
              <input {...register('dueDate')} type="date" className="input" />
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea {...register('description')} rows={2} className="input" placeholder="ملاحظات إضافية" />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowCreate(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'جارٍ الإنشاء...' : 'حفظ الشيك'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Transition modal */}
      {showTransition && (
        <Modal
          isOpen
          onClose={() => setShowTransition(null)}
          title={`تغيير حالة الشيك ${showTransition.cheque_number}`}
          size="md"
        >
          <div className="space-y-3">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">الحالة الحالية:</span>
              <span className={STATUS_LABELS[showTransition.status]?.badge}>
                {STATUS_LABELS[showTransition.status]?.label}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-500">المبلغ:</span>
              <span className="font-bold">{formatCurrency(showTransition.amount)}</span>
            </div>
            {transitionTargets.map(({ status, label }) => (
              <button
                key={status}
                onClick={() => transitionMutation.mutate({ id: showTransition.id, data: { status, reason: label } as never })}
                disabled={transitionMutation.isPending}
                className="btn-secondary w-full"
              >
                {label}
              </button>
            ))}
          </div>
        </Modal>
      )}

      {/* Bulk deposit modal */}
      <Modal isOpen={showBulk} onClose={() => setShowBulk(false)} title="إيداع مجمع للشيكات" size="md">
        <div className="space-y-4">
          <div>
            <label className="label">البنك المستهدف</label>
            <select value={bulkBankId} onChange={(e) => setBulkBankId(Number(e.target.value))} className="input">
              <option value={0}>— اختر البنك —</option>
              {banks.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </div>
          <div className="max-h-60 overflow-y-auto rounded-lg border border-gray-200 dark:border-zinc-700 divide-y divide-gray-100 dark:divide-zinc-800">
            {receivableCheques.map((c) => {
              const checked = bulkSelected.includes(c.id);
              return (
                <label key={c.id} className="flex items-center justify-between px-3 py-2 text-sm">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={(e) => {
                        if (e.target.checked) setBulkSelected((prev) => [...prev, c.id]);
                        else setBulkSelected((prev) => prev.filter((id) => id !== c.id));
                      }}
                    />
                    <span className="font-mono">{c.cheque_number}</span>
                  </div>
                  <span className="font-bold">{formatCurrency(c.amount)}</span>
                </label>
              );
            })}
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => setShowBulk(false)} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => bulkMutation.mutate({ cheque_ids: bulkSelected, bank_id: bulkBankId } as never)}
              disabled={bulkSelected.length === 0 || !bulkBankId || bulkMutation.isPending}
              className="btn-primary"
            >
              {bulkMutation.isPending ? 'جارٍ الإيداع...' : `إيداع (${bulkSelected.length})`}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

const TRANSITIONS: Record<string, Record<string, string>> = {
  on_hand: {
    deposited: 'إيداع في البنك',
    under_collection: 'قيد التحصيل',
    cleared: 'تحصيل مباشر',
    returned: 'إعادة الشيك',
    stopped: 'إيقاف الشيك',
    cancelled: 'إلغاء الشيك',
    replaced: 'استبدال الشيك',
  },
  deposited: {
    under_collection: 'قيد التحصيل',
    cleared: 'تحصيل',
    returned: 'إعادة الشيك',
    cancelled: 'إلغاء الشيك',
  },
  under_collection: {
    cleared: 'تحصيل',
    returned: 'إعادة الشيك',
    cancelled: 'إلغاء الشيك',
  },
};