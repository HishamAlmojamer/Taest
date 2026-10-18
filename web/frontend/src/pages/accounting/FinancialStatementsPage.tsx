import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getBalanceSheet, getIncomeStatement, getCashFlowStatement } from '@/api/financialStatements';
import { StatsCard } from '@/components/ui/StatsCard';

export default function FinancialStatementsPage() {
  const [activeTab, setActiveTab] = useState<'balance-sheet' | 'income-statement' | 'cash-flow'>('balance-sheet');
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [periodStart, setPeriodStart] = useState(`${new Date().getFullYear()}-01-01`);
  const [periodEnd, setPeriodEnd] = useState(new Date().toISOString().split('T')[0]);

  const { data: balanceSheet, isLoading: bsLoading } = useQuery({
    queryKey: ['balance-sheet', asOfDate],
    queryFn: () => getBalanceSheet(asOfDate),
    enabled: activeTab === 'balance-sheet',
  });

  const { data: incomeStatement, isLoading: isLoading } = useQuery({
    queryKey: ['income-statement', periodStart, periodEnd],
    queryFn: () => getIncomeStatement(periodStart, periodEnd),
    enabled: activeTab === 'income-statement',
  });

  const { data: cashFlow, isLoading: cfLoading } = useQuery({
    queryKey: ['cash-flow', periodStart, periodEnd],
    queryFn: () => getCashFlowStatement(periodStart, periodEnd),
    enabled: activeTab === 'cash-flow',
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">القوائم المالية</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setActiveTab('balance-sheet')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'balance-sheet' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          >
            الميزان العمومي
          </button>
          <button
            onClick={() => setActiveTab('income-statement')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'income-statement' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          >
            قائمة الدخل
          </button>
          <button
            onClick={() => setActiveTab('cash-flow')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'cash-flow' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`}
          >
            التدفق النقدي
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow">
        {activeTab === 'balance-sheet' ? (
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">حتى تاريخ:</label>
            <input
              type="date"
              value={asOfDate}
              onChange={(e) => setAsOfDate(e.target.value)}
              className="border rounded-lg px-3 py-2"
            />
          </div>
        ) : (
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">من:</label>
            <input
              type="date"
              value={periodStart}
              onChange={(e) => setPeriodStart(e.target.value)}
              className="border rounded-lg px-3 py-2"
            />
            <label className="text-sm font-medium">إلى:</label>
            <input
              type="date"
              value={periodEnd}
              onChange={(e) => setPeriodEnd(e.target.value)}
              className="border rounded-lg px-3 py-2"
            />
          </div>
        )}
      </div>

      {/* Balance Sheet */}
      {activeTab === 'balance-sheet' && balanceSheet && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard title="إجمالي الأصول" value={balanceSheet.assets?.total?.toLocaleString() || '0'} />
            <StatsCard title="إجمالي الخصوم" value={balanceSheet.liabilities?.total?.toLocaleString() || '0'} />
            <StatsCard title="إجمالي حقوق الملكية" value={balanceSheet.equity?.total?.toLocaleString() || '0'} />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Assets */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 text-green-600">الأصول</h3>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-right py-2">الرمز</th>
                    <th className="text-right py-2">الاسم</th>
                    <th className="text-left py-2">الرصيد</th>
                  </tr>
                </thead>
                <tbody>
                  {balanceSheet.assets?.accounts?.map((acc: any) => (
                    <tr key={acc.id} className="border-b">
                      <td className="py-2">{acc.code}</td>
                      <td className="py-2">{acc.name}</td>
                      <td className="py-2 text-left">{acc.balance?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-bold border-t-2">
                    <td colSpan={2} className="py-2">الإجمالي</td>
                    <td className="py-2 text-left">{balanceSheet.assets?.total?.toLocaleString()}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Liabilities & Equity */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 text-red-600">الخصوم وحقوق الملكية</h3>
              <div className="mb-4">
                <h4 className="font-medium mb-2">الخصوم</h4>
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-right py-2">الرمز</th>
                      <th className="text-right py-2">الاسم</th>
                      <th className="text-left py-2">الرصيد</th>
                    </tr>
                  </thead>
                  <tbody>
                    {balanceSheet.liabilities?.accounts?.map((acc: any) => (
                      <tr key={acc.id} className="border-b">
                        <td className="py-2">{acc.code}</td>
                        <td className="py-2">{acc.name}</td>
                        <td className="py-2 text-left">{acc.balance?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div>
                <h4 className="font-medium mb-2">حقوق الملكية</h4>
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-right py-2">الرمز</th>
                      <th className="text-right py-2">الاسم</th>
                      <th className="text-left py-2">الرصيد</th>
                    </tr>
                  </thead>
                  <tbody>
                    {balanceSheet.equity?.accounts?.map((acc: any) => (
                      <tr key={acc.id} className="border-b">
                        <td className="py-2">{acc.code}</td>
                        <td className="py-2">{acc.name}</td>
                        <td className="py-2 text-left">{acc.balance?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-4 pt-4 border-t-2 font-bold">
                <div className="flex justify-between">
                  <span>الإجمالي</span>
                  <span>{balanceSheet.total_liabilities_and_equity?.toLocaleString()}</span>
                </div>
                <div className={`text-sm mt-2 ${balanceSheet.is_balanced ? 'text-green-600' : 'text-red-600'}`}>
                  {balanceSheet.is_balanced ? '✓ الميزان متوازن' : '✗ الميزان غير متوازن'}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Income Statement */}
      {activeTab === 'income-statement' && incomeStatement && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard title="إجمالي الإيرادات" value={incomeStatement.revenue?.total?.toLocaleString() || '0'} />
            <StatsCard title="إجمالي المصروفات" value={incomeStatement.expenses?.total?.toLocaleString() || '0'} />
            <StatsCard
              title="صافي الربح/الخسارة"
              value={incomeStatement.net_income?.toLocaleString() || '0'}
              trend={{ value: Math.abs(incomeStatement.net_income || 0), isPositive: incomeStatement.is_profit }}
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Revenue */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 text-green-600">الإيرادات</h3>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-right py-2">الرمز</th>
                    <th className="text-right py-2">الاسم</th>
                    <th className="text-left py-2">المبلغ</th>
                  </tr>
                </thead>
                <tbody>
                  {incomeStatement.revenue?.accounts?.map((acc: any) => (
                    <tr key={acc.id} className="border-b">
                      <td className="py-2">{acc.code}</td>
                      <td className="py-2">{acc.name}</td>
                      <td className="py-2 text-left">{acc.balance?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-bold border-t-2">
                    <td colSpan={2} className="py-2">الإجمالي</td>
                    <td className="py-2 text-left">{incomeStatement.revenue?.total?.toLocaleString()}</td>
                  </tr>
                </tfoot>
              </table>
            </div>

            {/* Expenses */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-bold mb-4 text-red-600">المصروفات</h3>
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-right py-2">الرمز</th>
                    <th className="text-right py-2">الاسم</th>
                    <th className="text-left py-2">المبلغ</th>
                  </tr>
                </thead>
                <tbody>
                  {incomeStatement.expenses?.accounts?.map((acc: any) => (
                    <tr key={acc.id} className="border-b">
                      <td className="py-2">{acc.code}</td>
                      <td className="py-2">{acc.name}</td>
                      <td className="py-2 text-left">{acc.balance?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="font-bold border-t-2">
                    <td colSpan={2} className="py-2">الإجمالي</td>
                    <td className="py-2 text-left">{incomeStatement.expenses?.total?.toLocaleString()}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center">
              <span className="text-lg font-bold">صافي الربح/الخسارة</span>
              <span className={`text-2xl font-bold ${incomeStatement.is_profit ? 'text-green-600' : 'text-red-600'}`}>
                {incomeStatement.net_income?.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Cash Flow Statement */}
      {activeTab === 'cash-flow' && cashFlow && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h3 className="text-lg font-bold mb-4">بيان التدفق النقدي</h3>

            <div className="space-y-6">
              {/* Operating Activities */}
              <div className="border-b pb-4">
                <h4 className="font-bold mb-3">الأنشطة التشغيلية</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">التدفقات الواردة:</span>
                    <p className="text-green-600 font-medium">{cashFlow.operating_activities?.inflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">التدفقات الصادرة:</span>
                    <p className="text-red-600 font-medium">{cashFlow.operating_activities?.outflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">صافي التدفق:</span>
                    <p className={`font-bold ${cashFlow.operating_activities?.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {cashFlow.operating_activities?.net?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Investing Activities */}
              <div className="border-b pb-4">
                <h4 className="font-bold mb-3">الأنشطة الاستثمارية</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">التدفقات الواردة:</span>
                    <p className="text-green-600 font-medium">{cashFlow.investing_activities?.inflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">التدفقات الصادرة:</span>
                    <p className="text-red-600 font-medium">{cashFlow.investing_activities?.outflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">صافي التدفق:</span>
                    <p className={`font-bold ${cashFlow.investing_activities?.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {cashFlow.investing_activities?.net?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Financing Activities */}
              <div className="border-b pb-4">
                <h4 className="font-bold mb-3">الأنشطة التمويلية</h4>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">التدفقات الواردة:</span>
                    <p className="text-green-600 font-medium">{cashFlow.financing_activities?.inflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">التدفقات الصادرة:</span>
                    <p className="text-red-600 font-medium">{cashFlow.financing_activities?.outflows?.toLocaleString()}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">صافي التدفق:</span>
                    <p className={`font-bold ${cashFlow.financing_activities?.net >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {cashFlow.financing_activities?.net?.toLocaleString()}
                    </p>
                  </div>
                </div>
              </div>

              {/* Net Cash Flow */}
              <div className="flex justify-between items-center pt-4">
                <span className="text-lg font-bold">صافي التدفق النقدي الكلي</span>
                <span className={`text-2xl font-bold ${cashFlow.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {cashFlow.net_cash_flow?.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>
      )}

      {(bsLoading || isLoading || cfLoading) && (
        <div className="text-center py-8">جاري التحميل...</div>
      )}
    </div>
  );
}
