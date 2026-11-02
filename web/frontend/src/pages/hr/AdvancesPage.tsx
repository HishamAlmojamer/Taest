import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getAdvances, createAdvance, approveAdvance, payAdvance, voidAdvance, deleteAdvance, getEmployees, updateAdvanceStatus } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'pending', label: 'قيد الانتظار' },
  { key: 'approved', label: 'معتمدة' },
  { key: 'paid', label: 'مدفوعة' },
  { key: 'voided', label: 'ملغاة' },
];

const paymentMethods = [
  { value: 'CASH', label: 'نقدي' },
  { value: 'BANK', label: 'تحويل بنكي' },
  { value: 'CHECK', label: 'شيك' },
];

const advanceTypes = [
  { value: 'advance', label: 'سلفة عامة' },
  { value: 'salary', label: 'دفعة من الراتب' },
  { value: 'urgent', label: 'سلفة عاجلة' },
  { value: 'other', label: 'أخرى' },
];

export default function AdvancesPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const company = useCompany();
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: string } | null>(null);
  const [printAdvance, setPrintAdvance] = useState<any>(null);
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '',
    advanceType: 'advance',
    amount: '',
    installments: '1',
    requestDate: '',
    reason: '',
    paymentMethod: 'BANK',
    notes: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-advances', page, statusFilter],
    queryFn: () => getAdvances({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createAdvance({
      employee_id: Number(form.employeeId),
      advance_type: form.advanceType,
      amount: Number(form.amount),
      installments: Number(form.installments) || 1,
      request_date: form.requestDate || undefined,
      reason: form.reason || undefined,
      payment_method: form.paymentMethod,
      notes: form.notes || undefined,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hr-advances'] });
      setShowModal(false);
      resetForm();
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: approveAdvance,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-advances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const payMutation = useMutation({
    mutationFn: (p: { id: number; data: { status: string; payment_method?: string; payment_date?: string } }) => updateAdvanceStatus(p.id, p.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-advances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const voidMutation = useMutation({
    mutationFn: (p: { id: number; reason?: string }) => updateAdvanceStatus(p.id, { status: 'voided', reason: p.reason }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-advances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAdvance,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-advances'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', advanceType: 'advance', amount: '', installments: '1', requestDate: '', reason: '', paymentMethod: 'BANK', notes: '' });
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId);
    return emp ? emp.full_name : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'amount', header: 'المبلغ', render: (item) => <span className="font-bold text-primary-600">{formatCurrency(Number(item.amount))}</span> },
    { key: 'installments', header: 'الأقساط', render: (item) => String(item.installments || '-') },
    { key: 'monthlyDeduction', header: 'الخصم الشهري', render: (item) => formatCurrency(Number(item.monthlyDeduction || 0)) },
    { key: 'requestDate', header: 'تاريخ الطلب', render: (item) => String(item.requestDate || '-') },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'journalEntryId', header: 'القيد', render: (item) => item.journalEntryId ? (
      <button onClick={() => navigate(`/accounting/journal?entryId=${item.journalEntryId}`)} className="text-primary-600 hover:text-primary-700 text-xs font-mono underline">
        #{String(item.journalEntryId)}
      </button>
    ) : <span className="text-gray-400 text-xs">-</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => {
      const id = Number(item.id);
      if (item.status === 'pending') return (
        <div className="flex gap-1">
          <button onClick={() => setConfirmAction({ id, action: 'approve' })} className="text-green-600 hover:text-green-700 text-xs font-medium bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded">اعتماد</button>
          <button onClick={() => setConfirmAction({ id, action: 'delete' })} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
        </div>
      );
      if (item.status === 'approved') return (
        <div className="flex gap-1">
          <button onClick={() => setConfirmAction({ id, action: 'pay' })} className="text-blue-600 hover:text-blue-700 text-xs font-medium bg-blue-50 dark:bg-blue-500/10 px-2 py-1 rounded">دفع</button>
          <button onClick={() => setConfirmAction({ id, action: 'void' })} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">إلغاء</button>
        </div>
      );
      return (
        <button onClick={() => setPrintAdvance(item)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">طباعة</button>
      );
    }},
  ];

  const handleConfirm = () => {
    if (!confirmAction) return;
    const { id, action } = confirmAction;
    if (action === 'approve') approveMutation.mutate(id);
    else if (action === 'pay') payMutation.mutate({ id, data: { status: 'paid', payment_method: 'BANK' } });
    else if (action === 'void') voidMutation.mutate({ id });
    else if (action === 'delete') deleteMutation.mutate(id);
    setConfirmAction(null);
  };

  const confirmMessages: Record<string, { title: string; message: string }> = {
    approve: { title: 'اعتماد السلفة', message: 'هل أنت متأكد من اعتماد هذه السلفة؟' },
    pay: { title: 'صرف السلفة', message: 'هل أنت متأكد من صرف هذه السلفة؟ سيتم إنشاء قيد محاسبي.' },
    void: { title: 'إلغاء السلفة', message: 'هل أنت متأكد من إلغاء هذه السلفة؟ سيتم عكس القيد المحاسبي.' },
    delete: { title: 'حذف السلفة', message: 'هل أنت متأكد من حذف هذه السلفة؟ لا يمكن التراجع عن هذا الإجراء.' },
  };

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="سلف الموظفين"
          subtitle={`${data?.total || 0} سجل`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={() => setShowModal(true)} className="btn-primary">سلفة جديدة</button>}
        />
      </div>

      {/* Status Tabs */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        {statusTabs.map((tab) => (
          <button key={tab.key} onClick={() => { setStatusFilter(tab.key); setPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              statusFilter === tab.key
                ? 'border-primary-500 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'
            }`}>
            {tab.label}
          </button>
        ))}
      </div>

      <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} keepPreviousData />

      {/* Create Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); resetForm(); }} title="سلفة جديدة" size="md">
        <div className="space-y-4">
          <div>
            <label className="label">الموظف</label>
            <select value={form.employeeId} onChange={(e) => setForm({ ...form, employeeId: e.target.value })} className={inputClass}>
              <option value="">اختر الموظف...</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{e.full_name} {e.code ? `(${e.code})` : ''}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">نوع السلفة</label>
              <select value={form.advanceType} onChange={(e) => setForm({ ...form, advanceType: e.target.value })} className={inputClass}>
                {advanceTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="label">المبلغ</label>
              <input type="number" min="0" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} className={inputClass} placeholder="0.00" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">عدد الأقساط</label>
              <input type="number" min="1" value={form.installments} onChange={(e) => setForm({ ...form, installments: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">تاريخ الطلب</label>
              <input type="date" value={form.requestDate} onChange={(e) => setForm({ ...form, requestDate: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">طريقة الصرف</label>
            <select value={form.paymentMethod} onChange={(e) => setForm({ ...form, paymentMethod: e.target.value })} className={inputClass}>
              {paymentMethods.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">السبب</label>
            <input type="text" value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })} className={inputClass} />
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => createMutation.mutate()}
              disabled={!form.employeeId || !form.amount || Number(form.amount) <= 0 || createMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Confirm Action Dialog */}
      <ConfirmDialog
        isOpen={confirmAction !== null}
        onClose={() => setConfirmAction(null)}
        onConfirm={handleConfirm}
        title={confirmAction ? confirmMessages[confirmAction.action]?.title : ''}
        message={confirmAction ? confirmMessages[confirmAction.action]?.message : ''}
        variant={confirmAction?.action === 'void' || confirmAction?.action === 'delete' ? 'danger' : 'warning'}
      />

      {/* Print Advance */}
      <PrintPreviewModal
        isOpen={printAdvance !== null}
        onClose={() => setPrintAdvance(null)}
        title={`سلفة ${printAdvance?.employeeName || ''}`}
        filename={`سلفة-${printAdvance?.employeeName || printAdvance?.id || 'advance'}`}
      >
        <PrintDocument
          company={company}
          title="سند سلفة موظف"
          meta={[
            { label: 'رقم السند', value: `#${printAdvance?.id || '-'}` },
            { label: 'الموظف', value: printAdvance?.employeeName || '-' },
            { label: 'تاريخ الطلب', value: printAdvance?.requestDate ? formatDate(String(printAdvance.requestDate)) : '-' },
            { label: 'الحالة', value: String(printAdvance?.status || '') },
            { label: 'المبلغ', value: formatCurrency(Number(printAdvance?.amount || 0)) },
            { label: 'عدد الأقساط', value: String(printAdvance?.installments || '-') },
            { label: 'الخصم الشهري', value: formatCurrency(Number(printAdvance?.monthlyDeduction || 0)) },
            { label: 'طريقة الصرف', value: String(printAdvance?.paymentMethod || '-') },
          ]}
        >
          {printAdvance?.reason && (
            <div className="text-sm">
              <p className="font-semibold text-gray-700 mb-1">السبب:</p>
              <p className="text-gray-600">{printAdvance.reason}</p>
            </div>
          )}
          <div className="mt-10 grid grid-cols-2 gap-8 text-center text-sm text-gray-700">
            <div>
              <p className="border-t border-gray-400 pt-2 font-medium">توقيع الموظف</p>
            </div>
            <div>
              <p className="border-t border-gray-400 pt-2 font-medium">اعتماد الإدارة / الصراف</p>
            </div>
          </div>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
