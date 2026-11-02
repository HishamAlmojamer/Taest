import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/lib/utils';
import {
  getFiscalPeriods,
  createFiscalPeriod,
  validatePeriodForClosing,
  closeFiscalPeriod,
  lockFiscalPeriod,
  unlockFiscalPeriod,
  reopenFiscalPeriod,
  softCloseFiscalPeriod,
  reopenSoftClosedPeriod,
  getFiscalYears,
  createFiscalYear,
  generateFiscalPeriods,
  closeFiscalYear,
  openNextFiscalYear,
  type FiscalPeriod,
  type FiscalYear,
  type ValidatePeriodResult,
} from '@/api/periodClosing';

function formatDate(dateStr: string): string {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  if (isNaN(d.getTime())) return dateStr;
  return d.toLocaleDateString('ar-SA-u-nu-latn', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function FiscalPeriodsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showNewModal, setShowNewModal] = useState(false);
  const [showNewFYModal, setShowNewFYModal] = useState(false);
  const [generateFor, setGenerateFor] = useState<FiscalYear | null>(null);
  const [generateCount, setGenerateCount] = useState(12);
  const [closeFYTarget, setCloseFYTarget] = useState<FiscalYear | null>(null);
  const [closingPeriod, setClosingPeriod] = useState<FiscalPeriod | null>(null);
  const [validation, setValidation] = useState<ValidatePeriodResult | null>(null);
  const [validating, setValidating] = useState(false);

  const { data: periods = [], isLoading: periodsLoading } = useQuery({
    queryKey: ['fiscal-periods'],
    queryFn: () => getFiscalPeriods(),
  });

  const { data: fiscalYears = [] } = useQuery({
    queryKey: ['fiscal-years'],
    queryFn: () => getFiscalYears(),
  });

  const periodCounts = {
    open: periods.filter((p) => !p.isClosed && !p.isLocked && !p.isSoftClosed).length,
    softClosed: periods.filter((p) => p.isSoftClosed && !p.isClosed).length,
    locked: periods.filter((p) => p.isLocked && !p.isClosed).length,
    closed: periods.filter((p) => p.isClosed).length,
  };

  // --- Fiscal Year mutations ---
  const newFYMutation = useMutation({
    mutationFn: (data: { name: string; startDate: string; endDate: string }) =>
      createFiscalYear({ name: data.name, startDate: data.startDate, endDate: data.endDate }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-years'] });
      setShowNewFYModal(false);
      toast.success('تم إنشاء السنة المالية بنجاح');
    },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const genPeriodsMutation = useMutation({
    mutationFn: (data: { id: number; count: number }) =>
      generateFiscalPeriods(data.id, data.count),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
      setGenerateFor(null);
      toast.success(`تم توليد ${res.created} فترة بنجاح`);
    },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const closeFYMutation = useMutation({
    mutationFn: (fyId: number) => closeFiscalYear(fyId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-years'] });
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
      setCloseFYTarget(null);
      toast.success('تم إقفال السنة المالية بنجاح' + (res.retainedEarnings ? ` (أرباح مبقاة: ${res.retainedEarnings.toFixed(2)})` : ''));
    },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const openNextMutation = useMutation({
    mutationFn: (fyId: number) => openNextFiscalYear(fyId),
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['fiscal-years'] });
      queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] });
      toast.success(`تم ترحيل أرصدة الافتتاح (${res.lines || 0} سطر) بنجاح`);
    },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  // --- Period mutations ---
  const newPeriodMutation = useMutation({
    mutationFn: (data: { name: string; startDate: string; endDate: string }) => createFiscalPeriod(data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); setShowNewModal(false); toast.success('تم إنشاء الفترة المالية بنجاح'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const closeMutation = useMutation({
    mutationFn: (periodId: number) => closeFiscalPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); setClosingPeriod(null); setValidation(null); toast.success('تم إقفال الفترة المالية بنجاح'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const lockMutation = useMutation({
    mutationFn: (periodId: number) => lockFiscalPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); toast.success('تم قفل الفترة المالية'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const unlockMutation = useMutation({
    mutationFn: (periodId: number) => unlockFiscalPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); toast.success('تم فتح قفل الفترة المالية'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const reopenMutation = useMutation({
    mutationFn: (periodId: number) => reopenFiscalPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); toast.success('تمت إعادة فتح الفترة المالية'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const softCloseMutation = useMutation({
    mutationFn: (periodId: number) => softCloseFiscalPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); toast.success('تم الإقفال المؤقت للفترة المالية'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const reopenSoftMutation = useMutation({
    mutationFn: (periodId: number) => reopenSoftClosedPeriod(periodId),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['fiscal-periods'] }); toast.success('تم فتح الإقفال المؤقت للفترة المالية'); },
    onError: (e: any) => toast.error('حدث خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  async function handleValidate(period: FiscalPeriod) {
    setClosingPeriod(period);
    setValidating(true);
    setValidation(null);
    try {
      const res = await validatePeriodForClosing(period.id);
      setValidation(res);
    } finally {
      setValidating(false);
    }
  }

  const sortedPeriods = [...periods].sort((a, b) => new Date(b.startDate).getTime() - new Date(a.startDate).getTime());

  if (periodsLoading) return <PageLoader />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="السنوات والفترات المالية"
        subtitle="أنشئ السنة المالية، ولّد الفترات، واقفلها بعد ترحيل القيود"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>}
        actions={
          <div className="flex gap-2">
            <button onClick={() => setShowNewFYModal(true)} className="btn-secondary">+ سنة مالية</button>
            <button onClick={() => setShowNewModal(true)} className="btn-primary">+ فترة جديدة</button>
          </div>
        }
      />

      {/* ======== Fiscal Years ======== */}
      <div className="card overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-zinc-300">السنوات المالية</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="px-4 py-3 text-right text-xs font-semibold">السنة</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">من</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">إلى</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">الفترات</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">الحالة</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {fiscalYears.map((fy) => (
                <tr key={fy.id} className="table-row">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-zinc-100">{fy.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{formatDate(fy.startDate)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{formatDate(fy.endDate)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">
                    {fy.periodCount ?? 0} {fy.closedPeriodCount ? `(${fy.closedPeriodCount} مغلقة)` : ''}
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={fy.isClosed ? 'closed' : 'open'} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      {!fy.isClosed && (
                        <>
                          <button
                            onClick={() => { setGenerateFor(fy); setGenerateCount(12); }}
                            className="btn-ghost btn-sm"
                            title="توليد فترات شهرية"
                          >
                            توليد فترات
                          </button>
                          <button
                            onClick={() => setCloseFYTarget(fy)}
                            disabled={closeFYMutation.isPending}
                            className="btn-secondary btn-sm text-danger-600 dark:text-danger-400"
                          >
                            إقفال السنة
                          </button>
                        </>
                      )}
                      {fy.isClosed && !fy.openingBalancesPosted && (
                        <button
                          onClick={() => openNextMutation.mutate(fy.id)}
                          disabled={openNextMutation.isPending}
                          className="btn-primary btn-sm"
                        >
                          ترحيل الأرصدة الافتتاحية
                        </button>
                      )}
                      {fy.isClosed && fy.openingBalancesPosted && (
                        <span className="text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-1">
                          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                          تم ترحيل الأرصدة
                        </span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {fiscalYears.length === 0 && (
                <tr><td colSpan={6} className="px-4 py-10 text-center text-gray-400 dark:text-zinc-500">لا توجد سنوات مالية. أنشئ سنة مالية جديدة ثم ولّد الفترات.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ======== Period Stats ======== */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <div className="card p-5 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400">مفتوحة</p>
            <p className="text-2xl font-bold text-primary-600">{periodCounts.open}</p>
          </div>
          <div className="p-3 rounded-xl bg-primary-50 dark:bg-primary-500/10 text-primary-600 dark:text-primary-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
          </div>
        </div>
        <div className="card p-5 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400">إقفال مؤقت</p>
            <p className="text-2xl font-bold text-orange-600">{periodCounts.softClosed}</p>
          </div>
          <div className="p-3 rounded-xl bg-orange-50 dark:bg-orange-500/10 text-orange-600 dark:text-orange-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
          </div>
        </div>
        <div className="card p-5 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400">مقفلة</p>
            <p className="text-2xl font-bold text-amber-600">{periodCounts.locked}</p>
          </div>
          <div className="p-3 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
          </div>
        </div>
        <div className="card p-5 flex items-center justify-between">
          <div>
            <p className="text-sm text-gray-500 dark:text-zinc-400">مغلقة نهائياً</p>
            <p className="text-2xl font-bold text-emerald-600">{periodCounts.closed}</p>
          </div>
          <div className="p-3 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
          </div>
        </div>
      </div>

      {/* ======== Periods Table ======== */}
      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="px-4 py-3 text-right text-xs font-semibold">الفترة</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">من</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">إلى</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">الحالة</th>
                <th className="px-4 py-3 text-right text-xs font-semibold">إجراءات</th>
              </tr>
            </thead>
            <tbody>
              {sortedPeriods.map((period) => (
                <tr key={period.id} className="table-row">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 dark:text-zinc-100">{period.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{formatDate(period.startDate)}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-zinc-400">{formatDate(period.endDate)}</td>
                  <td className="px-4 py-3">
                    {period.isSoftClosed && !period.isClosed && (
                      <span className="inline-flex items-center rounded-full font-medium px-2 py-0.5 text-xs bg-orange-500/10 text-orange-600 dark:bg-orange-400/10 dark:text-orange-400">
                        إقفال مؤقت
                      </span>
                    )}
                    {!period.isSoftClosed && <StatusBadge status={period.isClosed ? 'closed' : period.isLocked ? 'locked' : 'open'} />}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Close / Validate */}
                      {!period.isClosed && !period.isSoftClosed && (
                        <button onClick={() => handleValidate(period)} disabled={period.isLocked} className={cn('btn-ghost btn-sm', period.isLocked && 'opacity-50 cursor-not-allowed')}>إقفال</button>
                      )}

                      {/* Soft-close */}
                      {!period.isClosed && !period.isSoftClosed && !period.isLocked && (
                        <button
                          onClick={() => softCloseMutation.mutate(period.id)}
                          disabled={softCloseMutation.isPending}
                          className="btn-ghost btn-sm text-orange-600 dark:text-orange-400"
                        >
                          إقفال مؤقت
                        </button>
                      )}

                      {/* Reopen soft */}
                      {period.isSoftClosed && !period.isClosed && (
                        <button
                          onClick={() => reopenSoftMutation.mutate(period.id)}
                          disabled={reopenSoftMutation.isPending}
                          className="btn-ghost btn-sm text-primary-600 dark:text-primary-400"
                        >
                          رفع الإقفال المؤقت
                        </button>
                      )}

                      {/* Lock */}
                      {!period.isClosed && !period.isLocked && (
                        <button onClick={() => lockMutation.mutate(period.id)} disabled={period.isLocked} className="btn-secondary btn-sm">
                          قفل
                        </button>
                      )}

                      {/* Unlock */}
                      {period.isLocked && !period.isClosed && (
                        <button onClick={() => unlockMutation.mutate(period.id)} disabled={unlockMutation.isPending} className="btn-secondary btn-sm text-amber-600 dark:text-amber-400">
                          فتح القفل
                        </button>
                      )}

                      {/* Closed state + reopen */}
                      {period.isClosed && (
                        <>
                          <span className="text-emerald-600 dark:text-emerald-400 flex items-center gap-1 text-sm">
                            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                            مغلقة نهائياً
                          </span>
                          <button onClick={() => reopenMutation.mutate(period.id)} disabled={reopenMutation.isPending} className="btn-secondary btn-sm text-orange-600 dark:text-orange-400">
                            إعادة فتح
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {sortedPeriods.length === 0 && (
                <tr><td colSpan={5} className="px-4 py-10 text-center text-gray-400 dark:text-zinc-500">لا توجد فترات محاسبية. أنشئ فترة جديدة للبدء.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* ======== Modals ======== */}
      <Modal isOpen={showNewModal} onClose={() => setShowNewModal(false)} title="فترة محاسبية جديدة" size="md">
        <NewPeriodForm onSubmit={(data) => newPeriodMutation.mutate(data)} loading={newPeriodMutation.isPending} onCancel={() => setShowNewModal(false)} />
      </Modal>

      <Modal isOpen={showNewFYModal} onClose={() => setShowNewFYModal(false)} title="سنة مالية جديدة" size="md">
        <NewFiscalYearForm onSubmit={(data) => newFYMutation.mutate(data)} loading={newFYMutation.isPending} onCancel={() => setShowNewFYModal(false)} />
      </Modal>

      <Modal isOpen={!!generateFor} onClose={() => setGenerateFor(null)} title={`توليد فترات - ${generateFor?.name || ''}`} size="sm">
        <div className="space-y-4">
          <div>
            <label className="label">عدد الفترات</label>
            <select className="input" value={generateCount} onChange={(e) => setGenerateCount(Number(e.target.value))}>
              <option value={12}>12 (شهري)</option>
              <option value={4}>4 (ربع سنوي)</option>
              <option value={1}>1 (السنة كاملة)</option>
              <option value={6}>6 (نصف سنوي)</option>
              <option value={24}>24 (شهري لسنتين)</option>
            </select>
          </div>
          <div className="flex justify-end gap-2 pt-3 border-t border-gray-200 dark:border-zinc-700">
            <button className="btn-secondary" onClick={() => setGenerateFor(null)}>إلغاء</button>
            <button
              className="btn-primary"
              disabled={genPeriodsMutation.isPending}
              onClick={() => generateFor && genPeriodsMutation.mutate({ id: generateFor.id, count: generateCount })}
            >
              {genPeriodsMutation.isPending ? 'جاري التوليد...' : 'توليد الفترات'}
            </button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!closeFYTarget} onClose={() => setCloseFYTarget(null)} title={`إقفال السنة المالية - ${closeFYTarget?.name || ''}`} size="md">
        <div className="space-y-4">
          <div className="flex items-start gap-3 p-4 rounded-xl bg-amber-50 dark:bg-amber-500/10 text-amber-700 dark:text-amber-300">
            <svg className="h-5 w-5 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" /></svg>
            <div>
              <p className="font-semibold">تنبيه: إقفال السنة المالية</p>
              <ul className="text-sm mt-1 space-y-1 list-disc list-inside">
                <li>سيتم إنشاء قيد إغلاق (إيرادات → أرباح مبقاة)</li>
                <li>ستتحول جميع القيم إلى "مغلقة نهائياً"</li>
                <li>يمكن بعدها ترحيل الأرصدة الافتتاحية للسنة التالية</li>
              </ul>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-3 border-t border-gray-200 dark:border-zinc-700">
            <button className="btn-secondary" onClick={() => setCloseFYTarget(null)}>إلغاء</button>
            <button
              className="btn-primary"
              disabled={closeFYMutation.isPending}
              onClick={() => closeFYTarget && closeFYMutation.mutate(closeFYTarget.id)}
            >
              {closeFYMutation.isPending ? 'جاري الإقفال...' : 'تأكيد إقفال السنة المالية'}
            </button>
          </div>
        </div>
      </Modal>

      <Modal isOpen={!!closingPeriod} onClose={() => { setClosingPeriod(null); setValidation(null); }} title={`إقفال ${closingPeriod?.name || ''}`} size="md">
        {validating ? (
          <div className="py-8 text-center text-gray-500 dark:text-zinc-400">جاري التحقق من إمكانية الإقفال...</div>
        ) : validation ? (
          <div className="space-y-4">
            {validation.canClose ? (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-emerald-50 dark:bg-emerald-500/10 text-emerald-700 dark:text-emerald-300">
                <svg className="h-5 w-5 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <div><p className="font-semibold">الفترة جاهزة للإقفال</p><p className="text-sm">جميع القيود مُرحّلة والدفاتر متوازنة.</p></div>
              </div>
            ) : (
              <div className="flex items-start gap-3 p-4 rounded-xl bg-danger-50 dark:bg-danger-500/10 text-danger-700 dark:text-danger-300">
                <svg className="h-5 w-5 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                <div><p className="font-semibold">لا يمكن إغلاق الفترة حالياً</p><ul className="text-sm list-disc list-inside mt-1 space-y-1">{validation.issues.map((issue, i) => <li key={i}>{issue}</li>)}</ul></div>
              </div>
            )}
            <div className="flex justify-end gap-2 pt-3 border-t border-gray-200 dark:border-zinc-700">
              <button onClick={() => { setClosingPeriod(null); setValidation(null); }} className="btn-secondary">إلغاء</button>
              {validation.canClose && closingPeriod && (
                <button onClick={() => closeMutation.mutate(closingPeriod.id)} disabled={closeMutation.isPending} className="btn-primary">{closeMutation.isPending ? 'جاري الإقفال...' : 'تأكيد الإقفال'}</button>
              )}
            </div>
          </div>
        ) : null}
      </Modal>
    </div>
  );
}

function NewPeriodForm({ onSubmit, loading, onCancel }: { onSubmit: (data: { name: string; startDate: string; endDate: string }) => void; loading: boolean; onCancel: () => void }): JSX.Element {
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const thisYear = new Date().getFullYear();
  const valid = name.trim() && start && end && new Date(start) < new Date(end);

  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); if (valid) onSubmit({ name, startDate: start, endDate: end }); }}>
      <div><label className="label">اسم الفترة *</label><input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder={`مثال: ${thisYear} - 01`} /></div>
      <div className="grid grid-cols-2 gap-4">
        <div><label className="label">تاريخ البداية *</label><input type="date" className="input" value={start} onChange={(e) => setStart(e.target.value)} /></div>
        <div><label className="label">تاريخ النهاية *</label><input type="date" className="input" value={end} onChange={(e) => setEnd(e.target.value)} /></div>
      </div>
      {name && start && end && new Date(start) >= new Date(end) && <p className="text-danger-600 dark:text-danger-400 text-sm">تاريخ النهاية يجب أن يكون بعد تاريخ البداية.</p>}
      <div className="flex justify-end gap-2 pt-3 border-t border-gray-200 dark:border-zinc-700">
        <button type="button" className="btn-secondary" onClick={onCancel}>إلغاء</button>
        <button type="submit" className="btn-primary" disabled={!valid || loading}>{loading ? 'جاري الإنشاء...' : 'إنشاء الفترة'}</button>
      </div>
    </form>
  );
}

function NewFiscalYearForm({ onSubmit, loading, onCancel }: { onSubmit: (data: { name: string; startDate: string; endDate: string }) => void; loading: boolean; onCancel: () => void }): JSX.Element {
  const [name, setName] = useState('');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const thisYear = new Date().getFullYear();
  const valid = name.trim() && start && end && new Date(start) < new Date(end);

  return (
    <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); if (valid) onSubmit({ name, startDate: start, endDate: end }); }}>
      <div><label className="label">اسم السنة المالية *</label><input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder={`مثال: ${thisYear}`} /></div>
      <div className="grid grid-cols-2 gap-4">
        <div><label className="label">تاريخ البداية *</label><input type="date" className="input" value={start} onChange={(e) => setStart(e.target.value)} /></div>
        <div><label className="label">تاريخ النهاية *</label><input type="date" className="input" value={end} onChange={(e) => setEnd(e.target.value)} /></div>
      </div>
      {name && start && end && new Date(start) >= new Date(end) && <p className="text-danger-600 dark:text-danger-400 text-sm">تاريخ النهاية يجب أن يكون بعد تاريخ البداية.</p>}
      <div className="flex justify-end gap-2 pt-3 border-t border-gray-200 dark:border-zinc-700">
        <button type="button" className="btn-secondary" onClick={onCancel}>إلغاء</button>
        <button type="submit" className="btn-primary" disabled={!valid || loading}>{loading ? 'جاري الإنشاء...' : 'إنشاء السنة المالية'}</button>
      </div>
    </form>
  );
}
