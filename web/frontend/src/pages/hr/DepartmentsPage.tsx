import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDepartmentTree, createDepartment, updateDepartment, deleteDepartment, getDepartments, getEmployees, getPositions } from '@/api/hr';
import { TreeView } from '@/components/ui/TreeView';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import type { HRDepartment, HRPosition } from '@/types';

interface DeptForm { code: string; name: string; name_en: string; description: string; parent_id: number | null; manager_id: number | null; }

function flattenDepts(depts: HRDepartment[]): HRDepartment[] {
  const result: HRDepartment[] = [];
  const walk = (items: HRDepartment[]) => {
    for (const d of items) {
      result.push(d);
      if (d.children) walk(d.children);
    }
  };
  walk(depts);
  return result;
}

export default function DepartmentsPage() {
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [selectedDept, setSelectedDept] = useState<HRDepartment | null>(null);
  const [showModal, setShowModal] = useState(false);
  const [editingDept, setEditingDept] = useState<HRDepartment | null>(null);
  const [showDelete, setShowDelete] = useState(false);
  const [parentId, setParentId] = useState<number | null>(null);
  const toast = useToast();

  const { data: tree, isLoading } = useQuery({ queryKey: ['departmentTree'], queryFn: getDepartmentTree });
  const { data: flatDepts } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const { data: empData } = useQuery({ queryKey: ['employees', { pageSize: 200 }], queryFn: () => getEmployees({ pageSize: 200 }) });
  const { data: positionsData } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions({}) });
  const { register, handleSubmit, reset, setValue } = useForm<DeptForm>();

  const createMutation = useMutation({
    mutationFn: createDepartment,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departmentTree'] }); queryClient.invalidateQueries({ queryKey: ['departments'] }); setShowModal(false); reset(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const updateMutation = useMutation({
    mutationFn: (d: { id: number; data: Partial<HRDepartment> }) => updateDepartment(d.id, d.data),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departmentTree'] }); queryClient.invalidateQueries({ queryKey: ['departments'] }); setShowModal(false); setEditingDept(null); reset(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });
  const deleteMutation = useMutation({
    mutationFn: deleteDepartment,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departmentTree'] }); queryClient.invalidateQueries({ queryKey: ['departments'] }); setShowDelete(false); setSelectedDept(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deptToTreeNode = (d: HRDepartment): any => ({
    id: d.id,
    label: d.name,
    code: d.code,
    meta: <span className="text-xs text-gray-500 dark:text-zinc-400">{d.employeeCount} موظف</span>,
    children: d.children ? d.children.map(deptToTreeNode) : undefined,
  });

  const treeNodes = (tree?.items || []).map(deptToTreeNode);

  const allFlat = flatDepts ? flattenDepts(flatDepts.items || []) : [];
  const employees = empData?.items || [];
  const subDepts = selectedDept?.children || [];
  const deptPositions = (positionsData?.items || []).filter((p: HRPosition) => p.departmentId === selectedDept?.id);

  const openAdd = (pid: number | null = null) => {
    setEditingDept(null);
    setParentId(pid);
    reset({ code: '', name: '', name_en: '', description: '', parent_id: pid, manager_id: null });
    setShowModal(true);
  };
  const openEdit = (dept: HRDepartment) => {
    setEditingDept(dept);
    setParentId(null);
    reset({ code: dept.code, name: dept.name, name_en: dept.name_en || '', description: dept.description || '', parent_id: dept.parent_id, manager_id: dept.manager_id || null });
    setShowModal(true);
  };
  const onSubmit = (d: DeptForm) => {
    if (editingDept) updateMutation.mutate({ id: editingDept.id, data: d as Partial<HRDepartment> });
    else createMutation.mutate(d as Partial<HRDepartment>);
  };

  const countAll = (items: HRDepartment[]): number => items.reduce((sum, d) => sum + (d.employeeCount || 0) + (d.children ? countAll(d.children) : 0), 0);
  const totalEmployees = tree?.items ? countAll(tree.items) : 0;

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Left: Tree */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex items-center justify-between mb-3">
          <PageHeader
            title="شجرة الأقسام"
            subtitle={`${allFlat.length} قسم — ${totalEmployees} موظف`}
            icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
            actions={<button onClick={() => openAdd()} className="btn-primary">+ قسم جديد</button>}
          />
        </div>
        <TreeView
          nodes={treeNodes}
          searchable
          searchPlaceholder="بحث في الأقسام..."
          onSelect={(node) => {
            const dept = allFlat.find((d) => d.id === node.id) || null;
            setSelectedDept(dept);
          }}
        />
      </div>

      {/* Right: Detail Panel */}
      <div className="w-80 flex-shrink-0">
        {selectedDept ? (
          <div className="card p-5 space-y-4">
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs bg-gray-100 dark:bg-zinc-800 px-2 py-0.5 rounded">{selectedDept.code}</span>
              <h2 className="font-bold text-lg text-gray-900 dark:text-zinc-100">{selectedDept.name}</h2>
            </div>
            {selectedDept.name_en && <p className="text-sm text-gray-500 dark:text-zinc-400">{selectedDept.name_en}</p>}
            {selectedDept.description && <p className="text-sm text-gray-600 dark:text-zinc-400">{selectedDept.description}</p>}

            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-zinc-400">المدير</span>
                <span className="text-gray-900 dark:text-zinc-100">{selectedDept.managerName || 'غير محدد'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500 dark:text-zinc-400">عدد الموظفين</span>
                <span className="font-bold text-primary-600">{selectedDept.employeeCount}</span>
              </div>
              {subDepts.length > 0 && (
                <div className="pt-2 border-t border-gray-100 dark:border-zinc-700">
                  <p className="text-gray-500 dark:text-zinc-400 mb-1">الأقسام الفرعية ({subDepts.length})</p>
                  {subDepts.map((sub) => (
                    <button key={sub.id} onClick={() => setSelectedDept(sub)} className="block w-full text-right text-sm py-1 hover:text-primary-600">
                      {sub.name} <span className="text-gray-400">({sub.employeeCount})</span>
                    </button>
                  ))}
                </div>
              )}
              {deptPositions.length > 0 && (
                <div className="pt-2 border-t border-gray-100 dark:border-zinc-700">
                  <p className="text-gray-500 dark:text-zinc-400 mb-1">المناصب ({deptPositions.length})</p>
                  {deptPositions.map((pos) => (
                    <div key={pos.id} className="flex justify-between text-sm py-0.5">
                      <span className="text-gray-700 dark:text-zinc-300">{pos.name}</span>
                      <span className="text-gray-400 text-xs font-mono">{pos.code}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-gray-100 dark:border-zinc-700 space-y-2">
              <button onClick={() => openAdd(selectedDept.id)} className="btn-primary w-full text-sm">+ إضافة قسم فرعي</button>
              <div className="flex gap-2">
                <button onClick={() => navigate(`/hr/employees?departmentId=${selectedDept.id}`)} className="btn-secondary flex-1 text-sm">عرض الموظفين</button>
                <button onClick={() => openEdit(selectedDept)} className="btn-secondary flex-1 text-sm">تعديل</button>
                <button onClick={() => setShowDelete(true)} className="btn-danger flex-1 text-sm">حذف</button>
              </div>
            </div>
          </div>
        ) : (
          <div className="card p-8 text-center text-gray-400 dark:text-zinc-500">
            <p>اختر قاماً من الشجرة لعرض التفاصيل</p>
          </div>
        )}
      </div>

      {/* Add/Edit Modal */}
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditingDept(null); reset(); }} title={editingDept ? 'تعديل القسم' : 'قسم جديد'} size="sm">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div><label className="label">الكود</label><input {...register('code', { required: true })} className="input" /></div>
          <div><label className="label">الاسم (عربي)</label><input {...register('name', { required: true })} className="input" /></div>
          <div><label className="label">الاسم (إنجليزي)</label><input {...register('name_en')} className="input" /></div>
          <div><label className="label">الوصف</label><textarea {...register('description')} className="input" rows={2} /></div>
          {!editingDept && parentId === null && (
            <div><label className="label">القسم الأب</label>
              <select {...register('parent_id', { valueAsNumber: true })} className="input">
                <option value="">— بدون —</option>
                {allFlat.map((d) => <option key={d.id} value={d.id}>{d.code} - {d.name}</option>)}
              </select>
            </div>
          )}
          <div><label className="label">المدير</label>
            <select {...register('manager_id', { valueAsNumber: true })} className="input">
              <option value="">— غير محدد —</option>
              {employees.map((e: any) => <option key={e.id} value={e.id}>{e.full_name}</option>)}
            </select>
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); setEditingDept(null); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary" disabled={createMutation.isPending || updateMutation.isPending}>{editingDept ? 'تحديث' : 'حفظ'}</button>
          </div>
        </form>
      </Modal>

      {/* Delete Confirmation */}
      <ConfirmDialog isOpen={showDelete} onClose={() => setShowDelete(false)} onConfirm={() => selectedDept && deleteMutation.mutate(selectedDept.id)} title="حذف القسم" message={`هل أنت متأكد من حذف "${selectedDept?.name}"؟`} />
    </div>
  );
}
