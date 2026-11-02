import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getDocuments, createDocument, updateDocument, deleteDocument, getEmployees } from '@/api/hr';
import { formatDate } from '@/lib/utils';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRDocument } from '@/types';

const documentTypes = ['عقد عمل', 'هوية', 'جواز سفر', 'إقامة', 'شهادة صحية', 'شهادة علمية', 'شهادة خبرة', 'تأمين طبي', 'أخرى'];

export default function DocumentsPage() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<HRDocument | null>(null);
  const [showDelete, setShowDelete] = useState<HRDocument | null>(null);
  const [search, setSearch] = useState('');
  const toast = useToast();

  const [form, setForm] = useState({
    employeeId: '', documentType: 'عقد عمل', title: '', issueDate: '', expiryDate: '', notes: '',
  });

  const { data, isLoading } = useQuery({
    queryKey: ['hr-documents', page, search],
    queryFn: () => getDocuments({ page, per_page: 10, search: search || undefined }),
  });

  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const employees = empData?.items || [];

  const items = data?.items || [];

  const createMutation = useMutation({
    mutationFn: () => createDocument({
      employeeId: Number(form.employeeId),
      documentType: form.documentType,
      title: form.title,
      issueDate: form.issueDate || undefined,
      expiryDate: form.expiryDate || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-documents'] }); setShowModal(false); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateMutation = useMutation({
    mutationFn: () => updateDocument(editing!.id, {
      documentType: form.documentType,
      title: form.title,
      issueDate: form.issueDate || undefined,
      expiryDate: form.expiryDate || undefined,
      notes: form.notes || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-documents'] }); setShowModal(false); setEditing(null); resetForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-documents'] }); setShowDelete(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetForm = () => {
    setForm({ employeeId: '', documentType: 'عقد عمل', title: '', issueDate: '', expiryDate: '', notes: '' });
  };

  const openAdd = () => { setEditing(null); resetForm(); setShowModal(true); };

  const openEdit = (d: HRDocument) => {
    setEditing(d);
    setForm({
      employeeId: String(d.employeeId),
      documentType: d.documentType || 'عقد عمل',
      title: d.title,
      issueDate: d.issueDate || '',
      expiryDate: d.expiryDate || '',
      notes: d.notes || '',
    });
    setShowModal(true);
  };

  const getEmployeeName = (empId: number) => {
    const emp = employees.find((e: any) => e.id === empId) as any;
    return emp ? (emp.fullName || emp.full_name || `#${empId}`) : `#${empId}`;
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'employeeName', header: 'الموظف', render: (item) => <span className="font-medium">{getEmployeeName(Number(item.employeeId))}</span> },
    { key: 'documentType', header: 'نوع المستند', render: (item) => <span className="badge bg-primary-50 dark:bg-primary-500/10 text-primary-700 dark:text-primary-300">{String(item.documentType || '-')}</span> },
    { key: 'title', header: 'العنوان', render: (item) => <span className="font-bold">{String(item.title)}</span> },
    { key: 'issueDate', header: 'تاريخ الإصدار', render: (item) => formatDate(String(item.issueDate || '')) },
    { key: 'expiryDate', header: 'تاريخ الانتهاء', render: (item) => {
      const exp = String(item.expiryDate || '');
      if (!exp) return <span className="text-gray-400">-</span>;
      const expired = new Date(exp) < new Date();
      return <span className={expired ? 'text-red-600 font-medium' : ''}>{formatDate(exp)} {expired && '— منتهي'}</span>;
    }},
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEdit(item as unknown as HRDocument)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDelete(item as unknown as HRDocument)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="مستندات الموظفين"
          subtitle={`${data?.total || 0} مستند`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={<button onClick={openAdd} className="btn-primary">مستند جديد</button>}
        />
      </div>

      <input value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} placeholder="بحث بالعنوان أو نوع المستند..." className={`${inputClass} max-w-sm`} />

      <DataTable columns={columns} data={items as any} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} keepPreviousData />

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); resetForm(); }} title={editing ? 'تعديل المستند' : 'مستند جديد'}>
        <div className="space-y-4">
          <div>
            <label className="label">الموظف</label>
            <select value={form.employeeId} onChange={(e) => setForm({ ...form, employeeId: e.target.value })} className={inputClass} disabled={!!editing}>
              <option value="">اختر الموظف...</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{(e.fullName || e.full_name)} {e.code ? `(${e.code})` : ''}</option>)}
            </select>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">نوع المستند</label>
              <select value={form.documentType} onChange={(e) => setForm({ ...form, documentType: e.target.value })} className={inputClass}>
                {documentTypes.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div>
              <label className="label">العنوان</label>
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">تاريخ الإصدار</label>
              <input type="date" value={form.issueDate} onChange={(e) => setForm({ ...form, issueDate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">تاريخ الانتهاء</label>
              <input type="date" value={form.expiryDate} onChange={(e) => setForm({ ...form, expiryDate: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowModal(false); setEditing(null); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editing ? updateMutation : createMutation).mutate()}
              disabled={!form.employeeId || !form.title || createMutation.isPending || updateMutation.isPending}
              className="btn-primary"
            >
              {createMutation.isPending || updateMutation.isPending ? 'جاري الحفظ...' : editing ? 'تحديث' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={showDelete !== null}
        onClose={() => setShowDelete(null)}
        onConfirm={() => showDelete && deleteMutation.mutate(showDelete.id)}
        title="حذف المستند"
        message={`هل أنت متأكد من حذف "${showDelete?.title}"؟`}
        variant="danger"
      />
    </div>
  );
}
