import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBudgets, createBudget, getBudgetVsActual, getBudgetAlerts } from '@/api/budgets';
import { getAccounts } from '@/api/accounting';
import { StatsCard } from '@/components/ui/StatsCard';

export default function BudgetsPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPeriod, setSelectedPeriod] = useState<number>(1);
  const [showAlerts, setShowAlerts] = useState(false);

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
      setShowCreateModal(false);
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">إدارة الميزانيات</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setShowAlerts(!showAlerts)}
            className="bg-yellow-500 text-white px-4 py-2 rounded-lg"
          >
            التنبيهات ({alerts?.alerts?.length || 0})
          </button>
          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg"
          >
            إضافة ميزانية
          </button>
        </div>
      </div>

      {/* Budget Alerts */}
      {showAlerts && alerts?.alerts?.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="font-bold text-yellow-800 mb-2">تنبيهات الميزانية</h3>
          <div className="space-y-2">
            {alerts.alerts.map((alert: any, idx: number) => (
              <div key={idx} className={`p-2 rounded ${alert.severity === 'CRITICAL' ? 'bg-red-100' : 'bg-yellow-100'}`}>
                <span className="font-medium">{alert.account_code} - {alert.account_name}</span>
                <span className="mr-4">الاستهلاك: {alert.usage_percent}%</span>
                <span className="mr-4">المتبقي: {alert.remaining?.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary */}
      {budgetVsActual && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatsCard title="إجمالي الميزانية" value={budgetVsActual.total_budget?.toLocaleString()} />
          <StatsCard title="إجمالي الفعلي" value={budgetVsActual.total_actual?.toLocaleString()} />
          <StatsCard
            title="الانحراف"
            value={(budgetVsActual.total_budget - budgetVsActual.total_actual)?.toLocaleString()}
          />
        </div>
      )}

      {/* Budget vs Actual Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h3 className="font-bold">الميزانية مقابل الفعلي</h3>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-right">الرمز</th>
              <th className="px-4 py-3 text-right">الحساب</th>
              <th className="px-4 py-3 text-right">الميزانية</th>
              <th className="px-4 py-3 text-right">الفعلي</th>
              <th className="px-4 py-3 text-right">الانحراف</th>
              <th className="px-4 py-3 text-right">النسبة</th>
              <th className="px-4 py-3 text-right">الحالة</th>
            </tr>
          </thead>
          <tbody>
            {budgetVsActual?.budgets?.map((item: any) => (
              <tr key={item.budget_id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3">{item.account_code}</td>
                <td className="px-4 py-3">{item.account_name}</td>
                <td className="px-4 py-3">{item.budget_amount?.toLocaleString()}</td>
                <td className="px-4 py-3">{item.actual_amount?.toLocaleString()}</td>
                <td className={`px-4 py-3 ${item.variance < 0 ? 'text-red-600' : 'text-green-600'}`}>
                  {item.variance?.toLocaleString()}
                </td>
                <td className="px-4 py-3">{item.variance_percent}%</td>
                <td className="px-4 py-3">
                  {item.is_over_budget ? (
                    <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs">تجاوز</span>
                  ) : (
                    <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">ضمن الميزانية</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Create Budget Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">إضافة ميزانية جديدة</h2>
            <form onSubmit={(e) => {
              e.preventDefault();
              const formData = new FormData(e.target as HTMLFormElement);
              createMutation.mutate({
                account_id: Number(formData.get('account_id')),
                fiscal_period_id: selectedPeriod,
                budget_amount: Number(formData.get('budget_amount')),
                notes: formData.get('notes'),
              });
            }} className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">الحساب</label>
                <select name="account_id" required className="w-full border rounded-lg px-3 py-2">
                  <option value="">اختر الحساب</option>
                  {(accounts as any)?.items?.map((acc: any) => (
                    <option key={acc.id} value={acc.id}>{acc.account_code} - {acc.account_name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">المبلغ</label>
                <input name="budget_amount" type="number" step="0.01" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">ملاحظات</label>
                <input name="notes" className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div className="flex justify-end gap-2">
                <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 border rounded-lg">إلغاء</button>
                <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">حفظ</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {isLoading && <div className="text-center py-4">جاري التحميل...</div>}
    </div>
  );
}
