import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBudgets, createBudget, getBudgetVsActual, getBudgetAlerts, rejectBudget } from '@/api/budgets';
import { getAccounts } from '@/api/accounting';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';
import { cn, formatCurrency } from '@/lib/utils';

export default function BudgetsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(1);
  const [showAlerts, setShowAlerts] = useState(false);
  const [rejectTarget, setRejectTarget] = useState<any>(null);
  const [rejectReason, setRejectReason] = useState('');

  const { data: budgets, isLoading } = useQuery({
    queryKey: ['budgets', selectedPeriod],
    queryFn: () => getBudgets(selectedPeriod),
  });

  const { data: accounts } = useQuery({
    queryKey: ['accounts'],
    queryFn: getAccounts,
  });

  const { data: budgetVsActual } = useQuery({
    queryKey: ['budget-vs-actual', selectedPeriod],
    queryFn: () => getBudgetVsActual(selectedPeriod),
  });

  const { data: alerts } = useQuery({
    queryKey: ['budget-alerts'],
    queryFn: () => getBudgetAlerts(80),
  });

  const createMutation = useMutation({
    mutationFn: createBudget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      toast.success('تم إضافة الميزانية بنجاح');
      setShowCreateModal(false);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const rejectMutation = useMutation({
    mutationFn: ({ id, reason }: { id: number; reason: string }) => rejectBudget(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['budgets'] });
      toast.success('تم رفض الميزانية');
      setRejectTarget(null);
      setRejectReason('');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const closeReject = () => {
    setRejectTarget(null);
    setRejectReason('');
  };

  const alertCount = alerts?.alerts?.length || 0;
  const budgetRows = budgets || [];
  const varianceRows = budgetVsActual?.budgets || [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="إدارة الميزانيات"
        subtitle="متابعة الميزانيات التقديرية ومقارنتها بالإنفاق الفعلي"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>}
        actions={
          <>
            <button
              type="button"
              onClick={() => setShowAlerts(!showAlerts)}
              className={cn('btn-secondary', showAlerts && 'ring-2 ring-amber-400/60')}
              aria-expanded={showAlerts}
            >
              <svg className="h-4 w-4 text-amber-600 dark:text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
              </svg>
              التنبيهات
              {alertCount > 0 && (
                <span className="rounded-full bg-amber-100 px-1.5 py-0.5 text-[11px] font-bold text-amber-700 dark:bg-amber-500/15 dark:text-amber-400">
                  {alertCount}
                </span>
              )}
            </button>
            <button type="button" onClick={() => setShowCreateModal(true)} className="btn-primary">
              + إضافة ميزانية
            </button>
          </>
        }
      />

      {showAlerts && (
        <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 dark:border-amber-500/20 dark:bg-amber-500/5">
          <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-amber-800 dark:text-amber-300">
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            تنبيهات تجاوز الميزانية
          </h3>
          {alertCount === 0 ? (
            <p className="text-sm text-amber-700 dark:text-amber-400">لا توجد تنبيهات حالياً.</p>
          ) : (
            <div className="space-y-2">
              {alerts.alerts.map((alert: any, idx: number) => (
                <div
                  key={idx}
                  className={cn(
                    'flex flex-wrap items-center gap-x-4 gap-y-1 rounded-lg px-3 py-2 text-sm',
                    alert.severity === 'CRITICAL'
                      ? 'bg-red-100/80 text-red-800 dark:bg-red-500/10 dark:text-red-300'
                      : 'bg-amber-100/80 text-amber-800 dark:bg-amber-500/10 dark:text-amber-300'
                  )}
                >
                  <span className="font-medium">{alert.account_code} - {alert.account_name}</span>
                  <span>الاستهلاك: <strong className="tabular-nums">{alert.usage_percent}%</strong></span>
                  <span>المتبقي: <strong className="tabular-nums">{alert.remaining?.toLocaleString()}</strong></span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {budgetVsActual && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <StatsCard
            title="إجمالي الميزانية"
            value={Number(budgetVsActual.total_budget || 0)}
            currency
            color="blue"
            icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" /></svg>}
          />
          <StatsCard
            title="إجمالي الفعلي"
            value={Number(budgetVsActual.total_actual || 0)}
            currency
            color="green"
            icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" /></svg>}
          />
          <StatsCard
            title="الانحراف"
            value={Number(budgetVsActual.total_budget || 0) - Number(budgetVsActual.total_actual || 0)}
            currency
            color={Number(budgetVsActual.total_budget || 0) >= Number(budgetVsActual.total_actual || 0) ? 'green' : 'red'}
            icon={<svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 6l3 1m0 0l-3 9a5.002 5.002 0 006.001 0M6 7l3 9M6 7l6-2m6 2l3-1m-3 1l-3 9a5.002 5.002 0 006.001 0M18 7l3 9m-3-9l-6-2m0-2v2m0 16V5m0 16H9m3 0h3" /></svg>}
          />
        </div>
      )}

      <div className="card overflow-hidden p-0">
        <div className="border-b border-gray-100 p-4 dark:border-zinc-800">
          <h3 className="font-semibold text-gray-900 dark:text-zinc-100">قائمة الميزانيات</h3>
        </div>
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : budgetRows.length === 0 ? (
          <EmptyState
            title="لا توجد ميزانيات"
            description="ابدأ بإضافة ميزانية لحساب من دليل الحسابات لتتمكن من متابعة الإنفاق."
            action={
              <button type="button" onClick={() => setShowCreateModal(true)} className="btn-primary btn-sm">
                إضافة ميزانية
              </button>
            }
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[720px]" aria-label="قائمة الميزانيات">
              <thead className="table-header">
                <tr>
                  <th scope="col" className="px-4 py-3 text-right">الرمز</th>
                  <th scope="col" className="px-4 py-3 text-right">الحساب</th>
                  <th scope="col" className="px-4 py-3 text-right">المبلغ</th>
                  <th scope="col" className="px-4 py-3 text-right">الحالة</th>
                  <th scope="col" className="px-4 py-3 text-right">إجراءات</th>
                </tr>
              </thead>
              <tbody>
                {budgetRows.map((item: any) => (
                  <tr key={item.id} className="table-row">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-600 dark:text-zinc-400">
                      {item.account_code}
                    </td>
                    <td className="px-4 py-3 text-sm">{item.account_name}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium tabular-nums">
                      {formatCurrency(Number(item.budget_amount || 0))}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <StatusBadge status={String(item.status || 'DRAFT')} />
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {item.status === 'DRAFT' && (
                        <button
                          type="button"
                          onClick={() => { setRejectTarget(item); setRejectReason(''); }}
                          className="text-xs font-medium text-red-600 hover:underline dark:text-red-400"
                        >
                          رفض
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card overflow-hidden p-0">
        <div className="border-b border-gray-100 p-4 dark:border-zinc-800">
          <h3 className="font-semibold text-gray-900 dark:text-zinc-100">الميزانية مقابل الفعلي</h3>
        </div>
        {varianceRows.length === 0 ? (
          <EmptyState title="لا توجد بيانات مقارنة" description="ستظهر المقارنة بعد اعتماد ميزانيات وربطها بالقيد الفعلي." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[820px]" aria-label="الميزانية مقابل الفعلي">
              <thead className="table-header">
                <tr>
                  <th scope="col" className="px-4 py-3 text-right">الرمز</th>
                  <th scope="col" className="px-4 py-3 text-right">الحساب</th>
                  <th scope="col" className="px-4 py-3 text-right">الميزانية</th>
                  <th scope="col" className="px-4 py-3 text-right">الفعلي</th>
                  <th scope="col" className="px-4 py-3 text-right">الانحراف</th>
                  <th scope="col" className="px-4 py-3 text-right">النسبة</th>
                  <th scope="col" className="px-4 py-3 text-right">الحالة</th>
                </tr>
              </thead>
              <tbody>
                {varianceRows.map((item: any) => (
                  <tr key={item.budget_id} className="table-row">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-600 dark:text-zinc-400">
                      {item.account_code}
                    </td>
                    <td className="px-4 py-3 text-sm">{item.account_name}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">
                      {formatCurrency(Number(item.budget_amount || 0))}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">
                      {formatCurrency(Number(item.actual_amount || 0))}
                    </td>
                    <td
                      className={cn(
                        'whitespace-nowrap px-4 py-3 text-sm font-medium tabular-nums',
                        Number(item.variance) < 0
                          ? 'text-red-600 dark:text-red-400'
                          : 'text-emerald-600 dark:text-emerald-400'
                      )}
                    >
                      {formatCurrency(Number(item.variance || 0))}
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">
                      {item.variance_percent}%
                    </td>
                    <td className="px-4 py-3">
                      {item.is_over_budget ? (
                        <span className="badge-danger">تجاوز</span>
                      ) : (
                        <span className="badge-success">ضمن الميزانية</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="إضافة ميزانية جديدة"
        size="md"
        footer={
          <>
            <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">
              إلغاء
            </button>
            <button
              type="submit"
              form="create-budget-form"
              className="btn-primary"
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ الميزانية'}
            </button>
          </>
        }
      >
        <form
          id="create-budget-form"
          onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            createMutation.mutate({
              account_id: Number(formData.get('account_id')),
              fiscal_period_id: selectedPeriod,
              budget_amount: Number(formData.get('budget_amount')),
              notes: formData.get('notes'),
            });
          }}
          className="space-y-4"
        >
          <div>
            <label htmlFor="budget-account" className="label">الحساب</label>
            <select id="budget-account" name="account_id" required className="select">
              <option value="">اختر الحساب</option>
              {(accounts as any)?.items?.map((acc: any) => (
                <option key={acc.id} value={acc.id}>{acc.account_code} - {acc.account_name}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="budget-amount" className="label">المبلغ</label>
            <input
              id="budget-amount"
              name="budget_amount"
              type="number"
              min={0}
              step="0.01"
              required
              className="input tabular-nums"
              placeholder="0.00"
            />
          </div>
          <div>
            <label htmlFor="budget-notes" className="label">ملاحظات</label>
            <input id="budget-notes" name="notes" className="input" placeholder="اختياري" />
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={!!rejectTarget}
        onClose={closeReject}
        title="رفض الميزانية"
        size="sm"
        footer={
          <>
            <button type="button" onClick={closeReject} className="btn-secondary">إلغاء</button>
            <button
              type="button"
              onClick={() => { if (rejectReason.trim() && rejectTarget) rejectMutation.mutate({ id: rejectTarget.id, reason: rejectReason }); }}
              disabled={!rejectReason.trim() || rejectMutation.isPending}
              className="btn-danger"
            >
              {rejectMutation.isPending ? 'جاري الرفض...' : 'رفض الميزانية'}
            </button>
          </>
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-600 dark:text-zinc-400">
            هل أنت متأكد من رفض ميزانية الحساب{' '}
            <strong className="text-gray-900 dark:text-zinc-100">
              {rejectTarget?.account_code} - {rejectTarget?.account_name}
            </strong>؟
          </p>
          <div>
            <label htmlFor="reject-reason" className="label">سبب الرفض</label>
            <textarea
              id="reject-reason"
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              className="input"
              rows={3}
              placeholder="أدخل سبب الرفض..."
            />
          </div>
        </div>
      </Modal>
    </div>
  );
}
