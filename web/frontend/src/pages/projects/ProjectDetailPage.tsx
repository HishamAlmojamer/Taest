import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getProject } from '@/api/projects';
import { PageLoader } from '@/components/ui/LoadingSpinner';
import { formatCurrency, formatDate, getStatusLabel } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageHeader } from '@/components/ui/PageHeader';

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const { data: project, isLoading } = useQuery({
    queryKey: ['project', id],
    queryFn: () => getProject(id!),
    enabled: !!id,
  });

  if (isLoading) return <PageLoader />;
  if (!project) return <div className="text-center py-12 text-gray-500 dark:text-zinc-400">المشروع غير موجود</div>;

  const spent = project.spent || 0;
  const budget = project.budget || 1;

  return (
    <div className="space-y-6">
      <PageHeader
        title={project.name}
        subtitle={project.customerName}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" /></svg>}
        actions={<button onClick={() => navigate('/projects')} className="btn-secondary">رجوع</button>}
      />

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatsCard title="التقدم" value={`${project.progress}%`} icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" /></svg>} color="blue" />
        <StatsCard title="الميزانية" value={project.budget} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" /></svg>} color="green" />
        <StatsCard title="المصروف" value={spent} currency icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" /></svg>} color={spent > budget * 0.9 ? 'red' : 'yellow'} />
        <StatsCard title="الحالة" value={getStatusLabel(project.status)} icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>} color="purple" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">تفاصيل المشروع</h3>
          <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-gray-500 dark:text-zinc-400">المدير:</span><span>{project.managerName}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-zinc-400">تاريخ البداية:</span><span>{formatDate(project.startDate)}</span></div>
            <div className="flex justify-between"><span className="text-gray-500 dark:text-zinc-400">تاريخ النهاية:</span><span>{formatDate(project.endDate)}</span></div>
            <div className="pt-3 border-t"><p className="text-gray-500 dark:text-zinc-400 mb-1">الوصف:</p><p>{project.description || 'لا يوجد وصف'}</p></div>
          </div>
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold mb-4">المهام ({project.tasks?.length || 0})</h3>
          {project.tasks && project.tasks.length > 0 ? (
            <div className="space-y-2">
              {project.tasks.slice(0, 5).map((task: any) => (
                <div key={task.id} className="flex items-center justify-between p-2 rounded-lg bg-gray-50 dark:bg-zinc-800 text-sm">
                  <span>{task.title}</span>
                  <StatusBadge status={task.status} />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500 dark:text-zinc-400 text-sm">لا توجد مهام بعد</p>
          )}
        </div>
      </div>
    </div>
  );
}
