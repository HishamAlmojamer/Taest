import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { getProjects, createProject } from '@/api/projects';
import { getCustomers } from '@/api/crm';
import { formatCurrency } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';

export default function ProjectsListPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [formData, setFormData] = useState({ name: '', nameAr: '', description: '', customerId: '', startDate: '', endDate: '', budget: '' });

  const { data, isLoading } = useQuery({ queryKey: ['projects', page, search], queryFn: () => getProjects({ page, pageSize: 10, search }) });
  const { data: customersData } = useQuery({ queryKey: ['customers'], queryFn: () => getCustomers() });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['projects'] });
      setShowModal(false);
      setFormData({ name: '', nameAr: '', description: '', customerId: '', startDate: '', endDate: '', budget: '' });
      toast.success('تم إنشاء المشروع بنجاح');
    },
    onError: (error: any) => { toast.error('حدث خطأ: ' + (error?.response?.data?.detail || error.message)); },
  });

  const handleSubmit = () => {
    if (!formData.name || !formData.startDate || !formData.budget) { toast.warning('يرجى ملء جميع الحقول المطلوبة'); return; }
    createMutation.mutate({ ...formData, customerId: formData.customerId ? Number(formData.customerId) : undefined, budget: Number(formData.budget) });
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'اسم المشروع', sortable: true, render: (item) => <span className="font-medium text-primary-600">{String(item.name)}</span> },
    { key: 'customerName', header: 'العميل', render: (item) => String(item.customerName || '-') },
    { key: 'managerName', header: 'المدير', render: (item) => String(item.managerName || '-') },
    { key: 'budget', header: 'الميزانية', sortable: true, render: (item) => formatCurrency(Number(item.budget)) },
    { key: 'progress', header: 'التقدم', render: (item) => (
      <div className="flex items-center gap-2">
        <div className="flex-1 h-2 bg-gray-200 dark:bg-zinc-700 rounded-full overflow-hidden">
          <div className="h-full bg-primary-500 rounded-full" style={{ width: `${Number(item.progress)}%` }} />
        </div>
        <span className="text-xs text-gray-500 dark:text-zinc-400 w-10">{Number(item.progress)}%</span>
      </div>
    )},
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status)} /> },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="المشاريع"
        subtitle="إدارة المشاريع ومتابعة التقدم"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>}
        actions={<button onClick={() => setShowModal(true)} className="btn-primary">+ مشروع جديد</button>}
      />
      <DataTable columns={columns} data={(data?.items || []) as unknown as Record<string, unknown>[]} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث في المشاريع..." onRowClick={(item) => navigate(`/projects/${item.id}`)} />
      <Modal isOpen={showModal} onClose={() => setShowModal(false)} title="مشروع جديد" size="lg">
        <div className="space-y-4">
          <div><label className="label">اسم المشروع *</label><input type="text" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} className="input" /></div>
          <div><label className="label">الاسم بالعربية</label><input type="text" value={formData.nameAr} onChange={(e) => setFormData({ ...formData, nameAr: e.target.value })} className="input" /></div>
          <div><label className="label">الوصف</label><textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} className="input" rows={3} /></div>
          <div>
            <label className="label">العميل</label>
            <select value={formData.customerId} onChange={(e) => setFormData({ ...formData, customerId: e.target.value })} className="input">
              <option value="">اختر العميل</option>
              {customersData?.items?.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">تاريخ البداية *</label><input type="date" value={formData.startDate} onChange={(e) => setFormData({ ...formData, startDate: e.target.value })} className="input" /></div>
            <div><label className="label">تاريخ النهاية</label><input type="date" value={formData.endDate} onChange={(e) => setFormData({ ...formData, endDate: e.target.value })} className="input" /></div>
          </div>
          <div><label className="label">الميزانية *</label><input type="number" value={formData.budget} onChange={(e) => setFormData({ ...formData, budget: e.target.value })} className="input" placeholder="0.00" /></div>
          <div className="flex justify-end gap-2 pt-4">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">إلغاء</button>
            <button type="button" onClick={handleSubmit} className="btn-primary" disabled={createMutation.isPending}>{createMutation.isPending ? 'جاري الحفظ...' : 'حفظ'}</button>
          </div>
        </div>
      </Modal>
    </div>
  );
}
