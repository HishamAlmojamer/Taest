import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getDepartments, createDepartment } from '@/api/hr';
import { Modal } from '@/components/ui/Modal';
import { useForm } from 'react-hook-form';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function DepartmentsPage() {
  const queryClient = useQueryClient();
  const [showModal, setShowModal] = useState(false);
  const { data: departments, isLoading } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const createMutation = useMutation({
    mutationFn: createDepartment,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['departments'] }); setShowModal(false); },
  });
  const { register, handleSubmit, reset } = useForm();

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">الأقسام</h1>
        <button onClick={() => setShowModal(true)} className="btn-primary">+ قسم جديد</button>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {departments?.items?.map((dept: any) => (
          <div key={dept.id} className="card hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="font-semibold text-gray-900 dark:text-zinc-100">{dept.name}</h3>
                {dept.nameEn && <p className="text-sm text-gray-500 dark:text-zinc-400 mt-0.5">{dept.nameEn}</p>}
              </div>
              <span className="badge-info">{dept.employeeCount} موظف</span>
            </div>
            <div className="mt-3 pt-3 border-t border-gray-100 dark:border-zinc-700 text-sm text-gray-600 dark:text-zinc-400">
              <p>المدير: {dept.managerName || 'غير محدد'}</p>
            </div>
          </div>
        ))}
      </div>
      <Modal isOpen={showModal} onClose={() => { setShowModal(false); reset(); }} title="قسم جديد" size="sm">
        <form onSubmit={handleSubmit((d) => createMutation.mutate({
          code: `DEPT-${Date.now()}`,
          name: d.name,
          nameEn: d.nameEn || d.name,
          description: d.description,
        } as never))} className="space-y-4">
          <div><label className="label">اسم القسم</label><input {...register('name', { required: true })} className="input" /></div>
          <div><label className="label">الاسم بالإنجليزية</label><input {...register('nameEn')} className="input" /></div>
          <div><label className="label">الوصف</label><textarea {...register('description')} className="input" rows={2} /></div>
          <div className="flex justify-end gap-2">
            <button type="button" onClick={() => { setShowModal(false); reset(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" className="btn-primary">حفظ</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
