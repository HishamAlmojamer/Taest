import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getAuditLogs, getAuditLogsByUser } from '@/api/audit';
import { Modal } from '@/components/ui/Modal';

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
    Purchase: ' أمر شراء',
    JournalEntry: 'قيد يومي',
    Account: 'حساب',
    Product: 'منتج',
    Customer: 'عميل',
    Supplier: 'مورد',
    Employee: 'موظف',
    FixedAsset: 'أصل ثابت',
    Budget: 'ميزانية',
    BankReconciliation: 'تسوية بنكية',
  };

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">سجل التدقيق</h1>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">الإجراء</label>
            <select
              value={filterAction}
              onChange={(e) => setFilterAction(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="">جميع الإجراءات</option>
              {Object.entries(actionLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">نوع الكيان</label>
            <select
              value={filterEntityType}
              onChange={(e) => setFilterEntityType(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            >
              <option value="">جميع الأنواع</option>
              {Object.entries(entityTypeLabels).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">المستخدم</label>
            <input
              type="number"
              value={filterUserId}
              onChange={(e) => setFilterUserId(e.target.value ? Number(e.target.value) : '')}
              placeholder="معرف المستخدم"
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">من تاريخ</label>
            <input
              type="date"
              value={startDate}
              onChange={(e) => setStartDate(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">إلى تاريخ</label>
            <input
              type="date"
              value={endDate}
              onChange={(e) => setEndDate(e.target.value)}
              className="w-full border rounded-lg px-3 py-2"
            />
          </div>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-right">التاريخ والوقت</th>
              <th className="px-4 py-3 text-right">المستخدم</th>
              <th className="px-4 py-3 text-right">الإجراء</th>
              <th className="px-4 py-3 text-right">نوع الكيان</th>
              <th className="px-4 py-3 text-right">معرف الكيان</th>
              <th className="px-4 py-3 text-right">الإجراءات</th>
            </tr>
          </thead>
          <tbody>
            {data?.logs?.map((log: any) => (
              <tr key={log.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3 text-sm">
                  {new Date(log.created_at).toLocaleString('ar-SA')}
                </td>
                <td className="px-4 py-3">{log.user_name}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    log.action === 'DELETE' ? 'bg-red-100 text-red-800' :
                    log.action === 'CREATE' ? 'bg-green-100 text-green-800' :
                    log.action === 'UPDATE' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {actionLabels[log.action] || log.action}
                  </span>
                </td>
                <td className="px-4 py-3">{entityTypeLabels[log.entity_type] || log.entity_type}</td>
                <td className="px-4 py-3">{log.entity_id}</td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => setSelectedLog(log)}
                    className="text-blue-600 hover:underline text-sm"
                  >
                    التفاصيل
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {data?.logs?.length === 0 && (
          <div className="p-4 text-center text-gray-500">لا توجد سجلات</div>
        )}
      </div>

      {/* Pagination */}
      {data?.total_pages > 1 && (
        <div className="flex justify-center gap-2">
          <button
            onClick={() => setPage(Math.max(1, page - 1))}
            disabled={page === 1}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            السابق
          </button>
          <span className="px-3 py-1">
            صفحة {page} من {data.total_pages}
          </span>
          <button
            onClick={() => setPage(Math.min(data.total_pages, page + 1))}
            disabled={page === data.total_pages}
            className="px-3 py-1 border rounded disabled:opacity-50"
          >
            التالي
          </button>
        </div>
      )}

      {/* Detail Modal */}
      {selectedLog && (
        <Modal onClose={() => setSelectedLog(null)} title="تفاصيل سجل التدقيق">
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm text-gray-500">التاريخ والوقت</label>
                <p className="font-medium">{new Date(selectedLog.created_at).toLocaleString('ar-SA')}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">المستخدم</label>
                <p className="font-medium">{selectedLog.user_name}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">الإجراء</label>
                <p className="font-medium">{actionLabels[selectedLog.action] || selectedLog.action}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">نوع الكيان</label>
                <p className="font-medium">{entityTypeLabels[selectedLog.entity_type] || selectedLog.entity_type}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">معرف الكيان</label>
                <p className="font-medium">{selectedLog.entity_id}</p>
              </div>
              <div>
                <label className="text-sm text-gray-500">عنوان IP</label>
                <p className="font-medium">{selectedLog.ip_address}</p>
              </div>
            </div>

            {/* Old Value */}
            {selectedLog.old_value && (
              <div>
                <label className="text-sm text-gray-500 mb-2 block">القيمة القديمة</label>
                <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto max-h-40">
                  {JSON.stringify(selectedLog.old_value, null, 2)}
                </pre>
              </div>
            )}

            {/* New Value */}
            {selectedLog.new_value && (
              <div>
                <label className="text-sm text-gray-500 mb-2 block">القيمة الجديدة</label>
                <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto max-h-40">
                  {JSON.stringify(selectedLog.new_value, null, 2)}
                </pre>
              </div>
            )}

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-2 border rounded-lg"
              >
                إغلاق
              </button>
            </div>
          </div>
        </Modal>
      )}

      {isLoading && <div className="text-center py-4">جاري التحميل...</div>}
    </div>
  );
}
