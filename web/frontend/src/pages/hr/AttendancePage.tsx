import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getAttendance } from '@/api/hr';
import { StatusBadge } from '@/components/ui/StatusBadge';

export default function AttendancePage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const { data, isLoading } = useQuery({
    queryKey: ['attendance', page, search],
    queryFn: () => getAttendance({ page, pageSize: 10, search }),
  });

  const attendanceData = Array.isArray(data) ? data : [];

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeId', header: 'رقم الموظف', render: (item) => <span className="font-medium">#{String(item.employeeId)}</span> },
    { key: 'date', header: 'التاريخ', render: (item) => String(item.date || '-') },
    { key: 'checkIn', header: 'وقت الحضور', render: (item) => String(item.checkIn || '-') },
    { key: 'checkOut', header: 'وقت الانصراف', render: (item) => String(item.checkOut || '-') },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
    { key: 'notes', header: 'ملاحظات', render: (item) => String(item.notes || '-') },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الحضور والغياب</h1>
      <DataTable columns={columns} data={attendanceData as any} loading={isLoading} totalItems={attendanceData.length || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالاسم..." />
    </div>
  );
}
