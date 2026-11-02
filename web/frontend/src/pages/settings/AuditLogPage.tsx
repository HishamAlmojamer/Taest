import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAuditLogs } from '@/api/audit';
import { Modal } from '@/components/ui/Modal';
import { PageHeader } from '@/components/ui/PageHeader';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const actionLabels: Record<string, string> = {
  CREATE: 'إنشاء',
  UPDATE: 'تحديث',
  DELETE: 'حذف',
  APPROVE: 'اعتماد',
  REJECT: 'رفض',
  POST: 'ترحيل',
  REVERSE: 'عكس',
  LOGIN: 'تسجيل دخول',
  LOGOUT: 'تسجيل خروج',
};

const entityTypeLabels: Record<string, string> = {
  Sale: 'فاتورة مبيعات',
  Purchase: 'أمر شراء',
  JournalEntry: 'قيد يومي',
  Account: 'حساب',
  Product: 'منتج',
  Customer: 'عميل',
  Supplier: 'مورد',
  Employee: 'موظف',
  FixedAsset: 'أصل ثابت',
  Budget: 'ميزانية',
  BankReconciliation: 'تسوية بنكية',
  Cheque: 'شيك',
};

function actionBadgeClass(action: string) {
  switch (action) {
    case 'CREATE':
    case 'APPROVE':
    case 'POST':
      return 'badge-success';
    case 'DELETE':
    case 'REJECT':
    case 'REVERSE':
      return 'badge-danger';
    case 'UPDATE':
      return 'badge-info';
    case 'LOGIN':
    case 'LOGOUT':
      return 'badge-gray';
    default:
      return 'badge-gray';
  }
}

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const [filterAction, setFilterAction] = useState('');
  const [filterEntityType, setFilterEntityType] = useState('');
  const [filterUserId, setFilterUserId] = useState<number | ''>('');
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [selectedLog, setSelectedLog] = useState<any>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, filterAction, filterEntityType, filterUserId, startDate, endDate],
    queryFn: () => getAuditLogs({
      page,
      per_page: 20,
      action: filterAction || undefined,
      entity_type: filterEntityType || undefined,
      user_id: filterUserId || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
  });

  const logs = data?.logs || [];
  const totalPages = data?.total_pages || 1;
  const hasFilters = Boolean(filterAction || filterEntityType || filterUserId || startDate || endDate);

  const updateFilter = (setter: () => void) => {
    setter();
    setPage(1);
  };

  const clearFilters = () => {
    setFilterAction('');
    setFilterEntityType('');
    setFilterUserId('');
    setStartDate('');
    setEndDate('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="سجل التدقيق"
        subtitle="متابعة جميع العمليات التي تمت على النظام"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>}
      />

      <div className="card p-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
          <div>
            <label htmlFor="audit-action" className="label">الإجراء</label>
            <select
              id="audit-action"
              value={filterAction}
              onChange={(e) => updateFilter(() => setFilterAction(e.target.value))}
              className="select w-full"
            >
              <option value="">جميع الإجراءات</option>
              {Object.entries(actionLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="audit-entity" className="label">نوع الكيان</label>
            <select
              id="audit-entity"
              value={filterEntityType}
              onChange={(e) => updateFilter(() => setFilterEntityType(e.target.value))}
              className="select w-full"
            >
              <option value="">جميع الأنواع</option>
              {Object.entries(entityTypeLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label htmlFor="audit-user" className="label">المستخدم</label>
            <input
              id="audit-user"
              type="number"
              inputMode="numeric"
              value={filterUserId}
              onChange={(e) => updateFilter(() => setFilterUserId(e.target.value ? Number(e.target.value) : ''))}
              placeholder="معرف المستخدم"
              className="input w-full"
            />
          </div>
          <div>
            <label htmlFor="audit-start" className="label">من تاريخ</label>
            <input
              id="audit-start"
              type="date"
              value={startDate}
              onChange={(e) => updateFilter(() => setStartDate(e.target.value))}
              className="input w-full"
            />
          </div>
          <div>
            <label htmlFor="audit-end" className="label">إلى تاريخ</label>
            <input
              id="audit-end"
              type="date"
              value={endDate}
              onChange={(e) => updateFilter(() => setEndDate(e.target.value))}
              className="input w-full"
            />
          </div>
        </div>
        {hasFilters && (
          <div className="mt-3 flex justify-end">
            <button type="button" onClick={clearFilters} className="btn-ghost btn-sm">
              مسح الفلاتر
            </button>
          </div>
        )}
      </div>

      <div className="card overflow-hidden p-0">
        {isLoading && !data ? (
          <div className="flex items-center justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : logs.length === 0 ? (
          <EmptyState
            title="لا توجد سجلات"
            description="لم يتم العثور على أي عمليات مطابقة للفلاتر الحالية"
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[820px]" aria-label="سجل التدقيق">
                <thead className="table-header">
                  <tr>
                    <th scope="col" className="px-4 py-3 text-right">التاريخ والوقت</th>
                    <th scope="col" className="px-4 py-3 text-right">المستخدم</th>
                    <th scope="col" className="px-4 py-3 text-right">الإجراء</th>
                    <th scope="col" className="px-4 py-3 text-right">نوع الكيان</th>
                    <th scope="col" className="px-4 py-3 text-right">معرف الكيان</th>
                    <th scope="col" className="px-4 py-3 text-right">التفاصيل</th>
                  </tr>
                </thead>
                <tbody className={isLoading ? 'opacity-60' : undefined}>
                  {logs.map((log: any) => (
                    <tr key={log.id} className="table-row">
                      <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">
                        {new Date(log.created_at).toLocaleString('ar-SA')}
                      </td>
                      <td className="px-4 py-3 text-sm">{log.user_name || '—'}</td>
                      <td className="px-4 py-3">
                        <span className={actionBadgeClass(log.action)}>
                          {actionLabels[log.action] || log.action}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {entityTypeLabels[log.entity_type] || log.entity_type || '—'}
                      </td>
                      <td className="px-4 py-3 text-sm tabular-nums">{log.entity_id ?? '—'}</td>
                      <td className="px-4 py-3">
                        <button
                          type="button"
                          onClick={() => setSelectedLog(log)}
                          className="text-sm font-medium text-primary-600 hover:underline dark:text-primary-400"
                        >
                          التفاصيل
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="flex flex-col items-center justify-between gap-2 border-t border-gray-100 px-4 py-3 sm:flex-row dark:border-zinc-800">
              <span className="text-xs text-gray-500 dark:text-zinc-400">
                صفحة {page} من {totalPages}
                {typeof data?.total === 'number' ? ` — ${data.total} سجل` : ''}
              </span>
              {totalPages > 1 && (
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page <= 1}
                    className="btn-secondary btn-sm"
                  >
                    السابق
                  </button>
                  <button
                    type="button"
                    onClick={() => setPage(Math.min(totalPages, page + 1))}
                    disabled={page >= totalPages}
                    className="btn-secondary btn-sm"
                  >
                    التالي
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {selectedLog && (
        <Modal isOpen onClose={() => setSelectedLog(null)} title="تفاصيل سجل التدقيق">
          <div className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">التاريخ والوقت</p>
                <p className="text-sm font-medium">{new Date(selectedLog.created_at).toLocaleString('ar-SA')}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">المستخدم</p>
                <p className="text-sm font-medium">{selectedLog.user_name || '—'}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">الإجراء</p>
                <p className="text-sm font-medium">{actionLabels[selectedLog.action] || selectedLog.action}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">نوع الكيان</p>
                <p className="text-sm font-medium">
                  {entityTypeLabels[selectedLog.entity_type] || selectedLog.entity_type}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">معرف الكيان</p>
                <p className="text-sm font-medium tabular-nums">{selectedLog.entity_id}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 dark:text-zinc-400">عنوان IP</p>
                <p className="text-sm font-medium tabular-nums">{selectedLog.ip_address || '—'}</p>
              </div>
            </div>

            {selectedLog.old_value && (
              <div>
                <p className="mb-2 text-xs text-gray-500 dark:text-zinc-400">القيمة القديمة</p>
                <pre className="max-h-40 overflow-auto rounded-lg bg-gray-100 p-3 text-xs dark:bg-zinc-800">
                  {JSON.stringify(selectedLog.old_value, null, 2)}
                </pre>
              </div>
            )}

            {selectedLog.new_value && (
              <div>
                <p className="mb-2 text-xs text-gray-500 dark:text-zinc-400">القيمة الجديدة</p>
                <pre className="max-h-40 overflow-auto rounded-lg bg-gray-100 p-3 text-xs dark:bg-zinc-800">
                  {JSON.stringify(selectedLog.new_value, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end">
              <button type="button" onClick={() => setSelectedLog(null)} className="btn-secondary">
                إغلاق
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
