import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getARAging, getAPAging, getCustomerStatement, getSupplierStatement } from '@/api/agingReports';
import { getCustomers, getSuppliers } from '@/api/crm';
import { StatsCard } from '@/components/ui/StatsCard';
import { Modal } from '@/components/ui/Modal';
import { PageHeader } from '@/components/ui/PageHeader';
import ExcelExportButton from '@/components/excel/ExcelExportButton';

export default function AgingReportsPage() {
  const [activeTab, setActiveTab] = useState<'ar' | 'ap' | 'customer-statement' | 'supplier-statement'>('ar');
  const [asOfDate, setAsOfDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedCustomer, setSelectedCustomer] = useState<number | ''>('');
  const [selectedSupplier, setSelectedSupplier] = useState<number | ''>('');
  const [statementStart, setStatementStart] = useState(`${new Date().getFullYear()}-01-01`);
  const [statementEnd, setStatementEnd] = useState(new Date().toISOString().split('T')[0]);
  const [showStatementModal, setShowStatementModal] = useState(false);

  const { data: customers } = useQuery({
    queryKey: ['customers'],
    queryFn: getCustomers,
  });

  const { data: suppliers } = useQuery({
    queryKey: ['suppliers'],
    queryFn: getSuppliers,
  });

  const { data: arAging, isLoading: arLoading } = useQuery({
    queryKey: ['ar-aging', asOfDate],
    queryFn: () => getARAging(asOfDate),
    enabled: activeTab === 'ar',
  });

  const { data: apAging, isLoading: apLoading } = useQuery({
    queryKey: ['ap-aging', asOfDate],
    queryFn: () => getAPAging(asOfDate),
    enabled: activeTab === 'ap',
  });

  const { data: customerStatement, isLoading: csLoading } = useQuery({
    queryKey: ['customer-statement', selectedCustomer, statementStart, statementEnd],
    queryFn: () => getCustomerStatement(selectedCustomer as number, statementStart, statementEnd),
    enabled: activeTab === 'customer-statement' && !!selectedCustomer,
  });

  const { data: supplierStatement, isLoading: ssLoading } = useQuery({
    queryKey: ['supplier-statement', selectedSupplier, statementStart, statementEnd],
    queryFn: () => getSupplierStatement(selectedSupplier as number, statementStart, statementEnd),
    enabled: activeTab === 'supplier-statement' && !!selectedSupplier,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="تقارير أعمار الذمم"
        subtitle="عرض تقارير أعمار الذمم المدينة والدائنة"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>}
        actions={<div className="flex gap-2">
          <button
            onClick={() => setActiveTab('ar')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'ar' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-zinc-800'}`}
          >
            أعمار الذمم المدينة
          </button>
          <button
            onClick={() => setActiveTab('ap')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'ap' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-zinc-800'}`}
          >
            أعمار الذمم الدائنة
          </button>
          <button
            onClick={() => setActiveTab('customer-statement')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'customer-statement' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-zinc-800'}`}
          >
            كشف حساب عميل
          </button>
          <button
            onClick={() => setActiveTab('supplier-statement')}
            className={`px-4 py-2 rounded-lg ${activeTab === 'supplier-statement' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-zinc-800'}`}
          >
            كشف حساب مورد
          </button>
          {(activeTab === 'ar' || activeTab === 'ap') && (
            <ExcelExportButton
              url={activeTab === 'ar' ? '/excel/exports/ar-aging' : '/excel/exports/ap-aging'}
              params={{ as_of_date: asOfDate }}
              filename={`${activeTab === 'ar' ? 'ar' : 'ap'}-aging-${asOfDate}.xlsx`}
              label={`تصدير ${activeTab === 'ar' ? 'المدينين' : 'الدائنين'} Excel`}
            />
          )}
        </div>}
      />

      {/* Filters */}
      <div className="card p-4">
        {(activeTab === 'ar' || activeTab === 'ap') ? (
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
            <label className="text-sm font-medium">
              {activeTab === 'customer-statement' ? 'العميل:' : 'المورد:'}
            </label>
            <select
              value={activeTab === 'customer-statement' ? selectedCustomer : selectedSupplier}
              onChange={(e) => {
                if (activeTab === 'customer-statement') {
                  setSelectedCustomer(e.target.value ? Number(e.target.value) : '');
                } else {
                  setSelectedSupplier(e.target.value ? Number(e.target.value) : '');
                }
              }}
              className="border rounded-lg px-3 py-2"
            >
              <option value="">اختر...</option>
              {activeTab === 'customer-statement'
                ? customers?.items?.map((c: any) => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))
                : suppliers?.items?.map((s: any) => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))
              }
            </select>
            <label className="text-sm font-medium">من:</label>
            <input
              type="date"
              value={statementStart}
              onChange={(e) => setStatementStart(e.target.value)}
              className="border rounded-lg px-3 py-2"
            />
            <label className="text-sm font-medium">إلى:</label>
            <input
              type="date"
              value={statementEnd}
              onChange={(e) => setStatementEnd(e.target.value)}
              className="border rounded-lg px-3 py-2"
            />
          </div>
        )}
      </div>

      {/* AR Aging Report */}
      {activeTab === 'ar' && arAging && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <StatsCard title="الإجمالي" value={arAging.total?.toLocaleString() || '0'} />
            <StatsCard title="0-30 يوم" value={arAging.current?.toLocaleString() || '0'} />
            <StatsCard title="31-60 يوم" value={arAging.days_31_60?.toLocaleString() || '0'} />
            <StatsCard title="61-90 يوم" value={arAging.days_61_90?.toLocaleString() || '0'} />
            <StatsCard title="أكثر من 90 يوم" value={arAging.over_90?.toLocaleString() || '0'} />
          </div>

          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="table-header">
                <tr>
                  <th className="px-4 py-3 text-right">العميل</th>
                  <th className="px-4 py-3 text-right">الرصيد</th>
                  <th className="px-4 py-3 text-right">0-30 يوم</th>
                  <th className="px-4 py-3 text-right">31-60 يوم</th>
                  <th className="px-4 py-3 text-right">61-90 يوم</th>
                  <th className="px-4 py-3 text-right">أكثر من 90 يوم</th>
                </tr>
              </thead>
              <tbody>
                {arAging.customers?.map((customer: any) => (
                  <tr key={customer.customer_id} className="table-row">
                    <td className="px-4 py-3">{customer.customer_name}</td>
                    <td className="px-4 py-3 font-medium">{customer.total?.toLocaleString()}</td>
                    <td className="px-4 py-3">{customer.current?.toLocaleString()}</td>
                    <td className="px-4 py-3">{customer.days_31_60?.toLocaleString()}</td>
                    <td className="px-4 py-3">{customer.days_61_90?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-red-600">{customer.over_90?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-bold border-t-2 bg-gray-50 dark:bg-zinc-800">
                  <td className="px-4 py-3">الإجمالي</td>
                  <td className="px-4 py-3">{arAging.total?.toLocaleString()}</td>
                  <td className="px-4 py-3">{arAging.current?.toLocaleString()}</td>
                  <td className="px-4 py-3">{arAging.days_31_60?.toLocaleString()}</td>
                  <td className="px-4 py-3">{arAging.days_61_90?.toLocaleString()}</td>
                  <td className="px-4 py-3">{arAging.over_90?.toLocaleString()}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* AP Aging Report */}
      {activeTab === 'ap' && apAging && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            <StatsCard title="الإجمالي" value={apAging.total?.toLocaleString() || '0'} />
            <StatsCard title="0-30 يوم" value={apAging.current?.toLocaleString() || '0'} />
            <StatsCard title="31-60 يوم" value={apAging.days_31_60?.toLocaleString() || '0'} />
            <StatsCard title="61-90 يوم" value={apAging.days_61_90?.toLocaleString() || '0'} />
            <StatsCard title="أكثر من 90 يوم" value={apAging.over_90?.toLocaleString() || '0'} />
          </div>

          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="table-header">
                <tr>
                  <th className="px-4 py-3 text-right">المورد</th>
                  <th className="px-4 py-3 text-right">الرصيد</th>
                  <th className="px-4 py-3 text-right">0-30 يوم</th>
                  <th className="px-4 py-3 text-right">31-60 يوم</th>
                  <th className="px-4 py-3 text-right">61-90 يوم</th>
                  <th className="px-4 py-3 text-right">أكثر من 90 يوم</th>
                </tr>
              </thead>
              <tbody>
                {apAging.suppliers?.map((supplier: any) => (
                  <tr key={supplier.supplier_id} className="table-row">
                    <td className="px-4 py-3">{supplier.supplier_name}</td>
                    <td className="px-4 py-3 font-medium">{supplier.total?.toLocaleString()}</td>
                    <td className="px-4 py-3">{supplier.current?.toLocaleString()}</td>
                    <td className="px-4 py-3">{supplier.days_31_60?.toLocaleString()}</td>
                    <td className="px-4 py-3">{supplier.days_61_90?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-red-600">{supplier.over_90?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="font-bold border-t-2 bg-gray-50 dark:bg-zinc-800">
                  <td className="px-4 py-3">الإجمالي</td>
                  <td className="px-4 py-3">{apAging.total?.toLocaleString()}</td>
                  <td className="px-4 py-3">{apAging.current?.toLocaleString()}</td>
                  <td className="px-4 py-3">{apAging.days_31_60?.toLocaleString()}</td>
                  <td className="px-4 py-3">{apAging.days_61_90?.toLocaleString()}</td>
                  <td className="px-4 py-3">{apAging.over_90?.toLocaleString()}</td>
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}

      {/* Customer Statement */}
      {activeTab === 'customer-statement' && customerStatement && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard title="الرصيد الافتتاحي" value={customerStatement.opening_balance?.toLocaleString() || '0'} />
            <StatsCard title="الرصيد الختامي" value={customerStatement.closing_balance?.toLocaleString() || '0'} />
            <StatsCard
              title="الحركة"
              value={customerStatement.total_debit?.toLocaleString() || '0'}
            />
          </div>

          <div className="card overflow-hidden">
            <div className="p-4 border-b">
              <h3 className="font-bold">كشف حساب العميل - {customerStatement.customer_name}</h3>
            </div>
            <table className="w-full">
              <thead className="table-header">
                <tr>
                  <th className="px-4 py-3 text-right">التاريخ</th>
                  <th className="px-4 py-3 text-right">المرجع</th>
                  <th className="px-4 py-3 text-right">الوصف</th>
                  <th className="px-4 py-3 text-right">مدين</th>
                  <th className="px-4 py-3 text-right">دائن</th>
                  <th className="px-4 py-3 text-right">الرصيد</th>
                </tr>
              </thead>
              <tbody>
                {customerStatement.transactions?.map((txn: any, idx: number) => (
                  <tr key={idx} className="table-row">
                    <td className="px-4 py-3">{txn.date}</td>
                    <td className="px-4 py-3">{txn.reference}</td>
                    <td className="px-4 py-3">{txn.description}</td>
                    <td className="px-4 py-3">{txn.debit?.toLocaleString()}</td>
                    <td className="px-4 py-3">{txn.credit?.toLocaleString()}</td>
                    <td className="px-4 py-3 font-medium">{txn.balance?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Supplier Statement */}
      {activeTab === 'supplier-statement' && supplierStatement && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <StatsCard title="الرصيد الافتتاحي" value={supplierStatement.opening_balance?.toLocaleString() || '0'} />
            <StatsCard title="الرصيد الختامي" value={supplierStatement.closing_balance?.toLocaleString() || '0'} />
            <StatsCard
              title="الحركة"
              value={supplierStatement.total_credit?.toLocaleString() || '0'}
            />
          </div>

          <div className="card overflow-hidden">
            <div className="p-4 border-b">
              <h3 className="font-bold">كشف حساب المورد - {supplierStatement.supplier_name}</h3>
            </div>
            <table className="w-full">
              <thead className="table-header">
                <tr>
                  <th className="px-4 py-3 text-right">التاريخ</th>
                  <th className="px-4 py-3 text-right">المرجع</th>
                  <th className="px-4 py-3 text-right">الوصف</th>
                  <th className="px-4 py-3 text-right">مدين</th>
                  <th className="px-4 py-3 text-right">دائن</th>
                  <th className="px-4 py-3 text-right">الرصيد</th>
                </tr>
              </thead>
              <tbody>
                {supplierStatement.transactions?.map((txn: any, idx: number) => (
                  <tr key={idx} className="table-row">
                    <td className="px-4 py-3">{txn.date}</td>
                    <td className="px-4 py-3">{txn.reference}</td>
                    <td className="px-4 py-3">{txn.description}</td>
                    <td className="px-4 py-3">{txn.debit?.toLocaleString()}</td>
                    <td className="px-4 py-3">{txn.credit?.toLocaleString()}</td>
                    <td className="px-4 py-3 font-medium">{txn.balance?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {(arLoading || apLoading || csLoading || ssLoading) && (
        <div className="text-center py-8 text-gray-600 dark:text-zinc-400">جاري التحميل...</div>
      )}
    </div>
  );
}
