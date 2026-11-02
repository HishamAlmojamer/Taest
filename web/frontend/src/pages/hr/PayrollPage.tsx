import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getPayroll, calculateBulkPayroll, approvePayroll, voidPayroll, payPayroll, getEmployees, getDepartments } from '@/api/hr';
import { formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const statusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'draft', label: 'مسودة' },
  { key: 'approved', label: 'معتمدة' },
  { key: 'paid', label: 'مدفوعة' },
  { key: 'voided', label: 'ملغاة' },
];

export default function PayrollPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [period, setPeriod] = useState('');
  const [selectedDept, setSelectedDept] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [confirmAction, setConfirmAction] = useState<{ id: number; action: string } | null>(null);
  const [payTarget, setPayTarget] = useState<number | null>(null);
  const [payMethod, setPayMethod] = useState('BANK');
  const [payDate, setPayDate] = useState(() => new Date().toISOString().slice(0, 10));
  const toast = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ['payroll', page, statusFilter],
    queryFn: () => getPayroll({ page, pageSize: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const { data: deptData } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const employees = empData?.items || [];
  const departments = deptData?.items || [];

  const items = data?.items || [];

  const processMutation = useMutation({
    mutationFn: (p: { period: string; departmentId?: number }) => calculateBulkPayroll({
      period_from: p.period + '-01',
      period_to: p.period + '-28',
      department_id: p.departmentId,
    } as any),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll'] });
      setShowModal(false);
      setPeriod('');
      setSelectedDept('');
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const approveMutation = useMutation({
    mutationFn: approvePayroll,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['payroll'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const payMutation = useMutation({
    mutationFn: (p: { id: number; data: { payment_method?: string; payment_date?: string } }) => payPayroll(p.id, p.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll'] });
      setPayTarget(null);
      toast.success('تم بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const voidMutation = useMutation({
    mutationFn: voidPayroll,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['payroll'] }); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId);
    return emp ? emp.full_name : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'periodFrom', header: 'من', render: (item) => String(item.periodFrom || item.period || '-') },
    { key: 'periodTo', header: 'إلى', render: (item) => String(item.periodTo || '-') },
    { key: 'basicSalary', header: 'الأساسي', render: (item) => formatCurrency(Number(item.basicSalary)) },
    { key: 'allowances', header: 'البدلات', render: (item) => formatCurrency(Number(item.allowances || item.totalAllowances || 0)) },
    { key: 'overtime', header: 'الإضافي', render: (item) => formatCurrency(Number(item.overtime)) },
    { key: 'deductions', header: 'الخصومات', render: (item) => formatCurrency(Number(item.deductions)) },
    { key: 'advanceDeduction', header: 'خصم السلف', render: (item) => {
      const v = Number(item.advanceDeduction || 0);
      return v ? <span className="text-red-600 dark:text-red-400">{formatCurrency(v)}</span> : <span className="text-gray-400">-</span>;
    } },
    { key: 'netSalary', header: 'الصافي', render: (item) => <span className="font-bold text-primary-600">{formatCurrency(Number(item.netSalary))}</span> },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'journalEntryId', header: 'القيد', render: (item) => item.journalEntryId ? (
      <button onClick={() => navigate(`/accounting/journal?entryId=${item.journalEntryId}`)} className="text-primary-600 hover:text-primary-700 text-xs font-mono underline">
        #{String(item.journalEntryId)}
      </button>
    ) : <span className="text-gray-400 text-xs">-</span> },
    { key: 'actions', header: 'إجراءات', render: (item) => {
      const id = Number(item.id);
      if (item.status === 'draft') return (
        <button onClick={() => setConfirmAction({ id, action: 'approve' })} className="text-green-600 hover:text-green-700 text-xs font-medium bg-green-50 dark:bg-green-500/10 px-2 py-1 rounded">اعتماد</button>
      );
      if (item.status === 'approved') return (
        <div className="flex gap-1">
          <button onClick={() => { setPayTarget(id); setPayMethod(String(item.paymentMethod || 'BANK')); }} className="text-blue-600 hover:text-blue-700 text-xs font-medium bg-blue-50 dark:bg-blue-500/10 px-2 py-1 rounded">دفع</button>
          <button onClick={() => setConfirmAction({ id, action: 'void' })} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">إلغاء</button>
        </div>
      );
      return null;
    }},
  ];

  const handleConfirm = () => {
    if (!confirmAction) return;
    const { id, action } = confirmAction;
    if (action === 'approve') approveMutation.mutate(id);
    else if (action === 'void') voidMutation.mutate(id);
    setConfirmAction(null);
  };

  const handlePay = () => {
    if (payTarget === null) return;
    payMutation.mutate({ id: payTarget, data: { payment_method: payMethod, payment_date: payDate } });
  };

  const confirmMessages: Record<string, { title: string; message: string }> = {
    approve: { title: 'اعتماد الراتب', message: 'هل أنت متأكد من اعتماد هذا الراتب؟ سيتم إنشاء قيد محاسبي.' },
    void: { title: 'إلغاء الراتب', message: 'هل أنت متأكد من إلغاء هذا الراتب؟ سيتم عكس القيد المحاسبي.' },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="كشف الرواتب"
          subtitle={`${data?.total || 0} سجل`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={() => setShowModal(true)} className="btn-primary">معالجة الرواتب</button>}
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

      {/* Bulk Calculation Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setPeriod(''); setSelectedDept(''); }} title="معالجة الرواتب" size="sm">
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-zinc-400">حساب الرواتب لجميع الموظفين النشطين</p>
          <div>
            <label className="label">الفترة</label>
            <input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} className="input" />
          </div>
          <div>
            <label className="label">القسم (اختياري)</label>
            <select value={selectedDept} onChange={(e) => setSelectedDept(e.target.value)} className="input">
              <option value="">جميع الأقسام</option>
              {departments.map((d: any) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setPeriod(''); setSelectedDept(''); }} className="btn-secondary">إلغاء</button>
            <button onClick={() => { if (period) processMutation.mutate({ period, departmentId: selectedDept ? Number(selectedDept) : undefined }); }} disabled={!period || processMutation.isPending} className="btn-primary">
              {processMutation.isPending ? 'جاري المعالجة...' : 'معالجة'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Pay Modal */}
      <Modal isOpen={payTarget !== null} onClose={() => setPayTarget(null)} title="تسجيل دفع الراتب" size="sm">
        <div className="space-y-4">
          <div>
            <label className="label">طريقة الدفع</label>
            <select value={payMethod} onChange={(e) => setPayMethod(e.target.value)} className="input">
              <option value="BANK">تحويل بنكي</option>
              <option value="CASH">نقدي</option>
              <option value="CHECK">شيك</option>
            </select>
          </div>
          <div>
            <label className="label">تاريخ الدفع</label>
            <input type="date" value={payDate} onChange={(e) => setPayDate(e.target.value)} className="input" />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => setPayTarget(null)} className="btn-secondary">إلغاء</button>
            <button onClick={handlePay} disabled={payMutation.isPending} className="btn-primary">
              {payMutation.isPending ? 'جاري التسجيل...' : 'تسجيل الدفع'}
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
        variant={confirmAction?.action === 'approve' ? 'info' : confirmAction?.action === 'void' ? 'danger' : 'warning'}
      />
    </div>
  );
}
