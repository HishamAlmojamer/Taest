import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getPayroll, processPayroll } from '@/api/hr';
import { formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function PayrollPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [period, setPeriod] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['payroll', page],
    queryFn: () => getPayroll({ page, pageSize: 10 }),
  });

  const processMutation = useMutation({
    mutationFn: processPayroll,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['payroll'] });
      setShowModal(false);
      setPeriod('');
      alert('تم معالجة الرواتب بنجاح');
    },
  });

  const handleProcess = () => {
    if (!period) {
      alert('يرجى إدخال الفترة');
      return;
    }
    processMutation.mutate({ period });
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{String(item.employeeName)}</span> },
    { key: 'period', header: 'الفترة', render: (item) => String(item.period) },
    { key: 'basicSalary', header: 'الراتب الأساسي', render: (item) => formatCurrency(Number(item.basicSalary)) },
    { key: 'allowances', header: 'البدلات', render: (item) => formatCurrency(Number(item.allowances)) },
    { key: 'deductions', header: 'الخصومات', render: (item) => formatCurrency(Number(item.deductions)) },
    { key: 'netSalary', header: 'الصافي', render: (item) => <span className="font-bold text-primary-600">{formatCurrency(Number(item.netSalary))}</span> },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">كشف الرواتب</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">معالجة الرواتب</button>
      </div>
      <DataTable columns={columns} data={(data?.items || []) as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} />

      {showModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h2 className="text-xl font-bold mb-4">معالجة الرواتب</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">الفترة</label>
                <input
                  type="month"
                  value={period}
                  onChange={(e) => setPeriod(e.target.value)}
                  className="w-full border rounded-lg px-3 py-2"
                />
              </div>
              <div className="flex justify-end gap-2">
                <button onClick={() => setShowModal(false)} className="px-4 py-2 border rounded-lg">إلغاء</button>
                <button
                  onClick={handleProcess}
                  disabled={processMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg"
                >
                  {processMutation.isPending ? 'جاري المعالجة...' : 'معالجة'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
