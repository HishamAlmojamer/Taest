import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { getJobPostings, createJobPosting, updateJobPosting, deleteJobPosting, getCandidates, createCandidate, updateCandidate, deleteCandidate, getDepartments, getPositions } from '@/api/hr';
import { formatCurrency, formatDate } from '@/lib/utils';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { HRJobPosting, HRCandidate } from '@/types';

const postingStatusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'open', label: 'مفتوحة' },
  { key: 'closed', label: 'مغلقة' },
];

const candidateStatusTabs = [
  { key: 'all', label: 'الكل' },
  { key: 'new', label: 'جديد' },
  { key: 'screening', label: 'فحص' },
  { key: 'interview', label: 'مقابلة' },
  { key: 'hired', label: 'تم التعيين' },
  { key: 'rejected', label: 'مرفوض' },
];

const employmentTypes = [
  { value: 'full_time', label: 'دوام كامل' },
  { value: 'part_time', label: 'دوام جزئي' },
  { value: 'contract', label: 'عقد' },
  { value: 'internship', label: 'تدريب' },
];

export default function RecruitmentPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'postings' | 'candidates'>('postings');
  const [page, setPage] = useState(1);
  const [statusFilter, setStatusFilter] = useState('all');

  const [showPostingModal, setShowPostingModal] = useState(false);
  const [editingPosting, setEditingPosting] = useState<HRJobPosting | null>(null);
  const [showDeletePosting, setShowDeletePosting] = useState<HRJobPosting | null>(null);

  const [showCandidateModal, setShowCandidateModal] = useState(false);
  const [editingCandidate, setEditingCandidate] = useState<HRCandidate | null>(null);
  const [showDeleteCandidate, setShowDeleteCandidate] = useState<HRCandidate | null>(null);
  const toast = useToast();

  const [postingForm, setPostingForm] = useState({
    title: '', departmentId: '', positionId: '', vacancies: '1', salaryMin: '', salaryMax: '',
    location: '', employmentType: 'full_time', status: 'open', postedDate: '', deadline: '', description: '', requirements: '',
  });

  const [candidateForm, setCandidateForm] = useState({
    jobPostingId: '', name: '', email: '', phone: '', status: 'new', rating: '0', source: '', notes: '', resumeText: '',
  });

  const postingsQuery = useQuery({
    queryKey: ['hr-job-postings', page, statusFilter],
    queryFn: () => getJobPostings({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const candidatesQuery = useQuery({
    queryKey: ['hr-candidates', page, statusFilter],
    queryFn: () => getCandidates({ page, per_page: 10, status: statusFilter !== 'all' ? statusFilter : undefined }),
  });

  const { data: deptData } = useQuery({ queryKey: ['departments'], queryFn: getDepartments });
  const { data: positionsData } = useQuery({ queryKey: ['positions'], queryFn: () => getPositions({}) });

  const departments = deptData?.items || [];
  const positions = positionsData?.items || [];
  const postings = postingsQuery.data?.items || [];
  const candidates = candidatesQuery.data?.items || [];

  const activeQuery = tab === 'postings' ? postingsQuery : candidatesQuery;
  const activeItems = tab === 'postings' ? postings : candidates;
  const activeTabs = tab === 'postings' ? postingStatusTabs : candidateStatusTabs;

  // ── Job Posting mutations ──
  const createPostingMutation = useMutation({
    mutationFn: () => createJobPosting({
      title: postingForm.title,
      departmentId: postingForm.departmentId ? Number(postingForm.departmentId) : undefined,
      positionId: postingForm.positionId ? Number(postingForm.positionId) : undefined,
      vacancies: Number(postingForm.vacancies) || 1,
      salaryMin: postingForm.salaryMin ? Number(postingForm.salaryMin) : undefined,
      salaryMax: postingForm.salaryMax ? Number(postingForm.salaryMax) : undefined,
      location: postingForm.location || undefined,
      employmentType: postingForm.employmentType,
      status: postingForm.status,
      postedDate: postingForm.postedDate || undefined,
      deadline: postingForm.deadline || undefined,
      description: postingForm.description || undefined,
      requirements: postingForm.requirements || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-job-postings'] }); setShowPostingModal(false); resetPostingForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updatePostingMutation = useMutation({
    mutationFn: () => updateJobPosting(editingPosting!.id, {
      title: postingForm.title,
      departmentId: postingForm.departmentId ? Number(postingForm.departmentId) : undefined,
      positionId: postingForm.positionId ? Number(postingForm.positionId) : undefined,
      vacancies: Number(postingForm.vacancies) || 1,
      salaryMin: postingForm.salaryMin ? Number(postingForm.salaryMin) : undefined,
      salaryMax: postingForm.salaryMax ? Number(postingForm.salaryMax) : undefined,
      location: postingForm.location || undefined,
      employmentType: postingForm.employmentType,
      status: postingForm.status,
      postedDate: postingForm.postedDate || undefined,
      deadline: postingForm.deadline || undefined,
      description: postingForm.description || undefined,
      requirements: postingForm.requirements || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-job-postings'] }); setShowPostingModal(false); setEditingPosting(null); resetPostingForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deletePostingMutation = useMutation({
    mutationFn: deleteJobPosting,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-job-postings'] }); setShowDeletePosting(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  // ── Candidate mutations ──
  const createCandidateMutation = useMutation({
    mutationFn: () => createCandidate({
      jobPostingId: candidateForm.jobPostingId ? Number(candidateForm.jobPostingId) : undefined,
      name: candidateForm.name,
      email: candidateForm.email || undefined,
      phone: candidateForm.phone || undefined,
      status: candidateForm.status,
      rating: candidateForm.rating ? Number(candidateForm.rating) : undefined,
      source: candidateForm.source || undefined,
      notes: candidateForm.notes || undefined,
      resumeText: candidateForm.resumeText || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-candidates'] }); queryClient.invalidateQueries({ queryKey: ['hr-job-postings'] }); setShowCandidateModal(false); resetCandidateForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const updateCandidateMutation = useMutation({
    mutationFn: () => updateCandidate(editingCandidate!.id, {
      jobPostingId: candidateForm.jobPostingId ? Number(candidateForm.jobPostingId) : undefined,
      name: candidateForm.name,
      email: candidateForm.email || undefined,
      phone: candidateForm.phone || undefined,
      status: candidateForm.status,
      rating: candidateForm.rating ? Number(candidateForm.rating) : undefined,
      source: candidateForm.source || undefined,
      notes: candidateForm.notes || undefined,
      resumeText: candidateForm.resumeText || undefined,
    }),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-candidates'] }); setShowCandidateModal(false); setEditingCandidate(null); resetCandidateForm(); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const deleteCandidateMutation = useMutation({
    mutationFn: deleteCandidate,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['hr-candidates'] }); setShowDeleteCandidate(null); toast.success('تم بنجاح'); },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const resetPostingForm = () => {
    setPostingForm({ title: '', departmentId: '', positionId: '', vacancies: '1', salaryMin: '', salaryMax: '', location: '', employmentType: 'full_time', status: 'open', postedDate: '', deadline: '', description: '', requirements: '' });
  };

  const resetCandidateForm = () => {
    setCandidateForm({ jobPostingId: '', name: '', email: '', phone: '', status: 'new', rating: '0', source: '', notes: '', resumeText: '' });
  };

  const openAddPosting = () => { setEditingPosting(null); resetPostingForm(); setShowPostingModal(true); };

  const openEditPosting = (p: HRJobPosting) => {
    setEditingPosting(p);
    setPostingForm({
      title: p.title,
      departmentId: p.departmentId ? String(p.departmentId) : '',
      positionId: p.positionId ? String(p.positionId) : '',
      vacancies: String(p.vacancies ?? 1),
      salaryMin: p.salaryMin ? String(p.salaryMin) : '',
      salaryMax: p.salaryMax ? String(p.salaryMax) : '',
      location: p.location || '',
      employmentType: p.employmentType || 'full_time',
      status: p.status || 'open',
      postedDate: p.postedDate || '',
      deadline: p.deadline || '',
      description: p.description || '',
      requirements: p.requirements || '',
    });
    setShowPostingModal(true);
  };

  const openAddCandidate = () => { setEditingCandidate(null); resetCandidateForm(); setShowCandidateModal(true); };

  const openEditCandidate = (c: HRCandidate) => {
    setEditingCandidate(c);
    setCandidateForm({
      jobPostingId: c.jobPostingId ? String(c.jobPostingId) : '',
      name: c.name,
      email: c.email || '',
      phone: c.phone || '',
      status: c.status || 'new',
      rating: c.rating ? String(c.rating) : '0',
      source: c.source || '',
      notes: c.notes || '',
      resumeText: c.resumeText || '',
    });
    setShowCandidateModal(true);
  };

  const postingColumns: Column<Record<string, unknown>>[] = [
    { key: 'title', header: 'المسمى الوظيفي', render: (item) => <span className="font-medium">{String(item.title)}</span> },
    { key: 'departmentName', header: 'القسم', render: (item) => String(item.departmentName || '-') },
    { key: 'vacancies', header: 'الوظائف الشاغرة', render: (item) => <span className="font-bold text-primary-600">{String(item.vacancies)}</span> },
    { key: 'salaryMin', header: 'الراتب', render: (item) => item.salaryMin ? `${formatCurrency(Number(item.salaryMin))} - ${formatCurrency(Number(item.salaryMax || item.salaryMin))}` : '-' },
    { key: 'location', header: 'الموقع', render: (item) => String(item.location || '-') },
    { key: 'employmentType', header: 'نوع العمل', render: (item) => employmentTypes.find((t) => t.value === String(item.employmentType))?.label || String(item.employmentType || '-') },
    { key: 'postedDate', header: 'تاريخ النشر', render: (item) => formatDate(String(item.postedDate || '')) },
    { key: 'deadline', header: 'آخر موعد', render: (item) => formatDate(String(item.deadline || '')) },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEditPosting(item as unknown as HRJobPosting)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDeletePosting(item as unknown as HRJobPosting)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const candidateColumns: Column<Record<string, unknown>>[] = [
    { key: 'name', header: 'الاسم', render: (item) => <span className="font-medium">{String(item.name)}</span> },
    { key: 'jobTitle', header: 'الوظيفة المتقدم لها', render: (item) => String(item.jobTitle || '-') },
    { key: 'email', header: 'البريد', render: (item) => String(item.email || '-') },
    { key: 'phone', header: 'الهاتف', render: (item) => String(item.phone || '-') },
    { key: 'appliedDate', header: 'تاريخ التقديم', render: (item) => formatDate(String(item.appliedDate || '')) },
    { key: 'rating', header: 'التقييم', render: (item) => Number(item.rating) > 0 ? <span className="text-amber-500">{"★".repeat(Math.round(Number(item.rating)))}</span> : '-' },
    { key: 'status', header: 'الحالة', render: (item) => <StatusBadge status={String(item.status).toUpperCase()} /> },
    { key: 'actions', header: 'إجراءات', render: (item) => (
      <div className="flex gap-1">
        <button onClick={() => openEditCandidate(item as unknown as HRCandidate)} className="text-primary-600 hover:text-primary-700 text-xs font-medium bg-primary-50 dark:bg-primary-500/10 px-2 py-1 rounded">تعديل</button>
        <button onClick={() => setShowDeleteCandidate(item as unknown as HRCandidate)} className="text-red-600 hover:text-red-700 text-xs font-medium bg-red-50 dark:bg-red-500/10 px-2 py-1 rounded">حذف</button>
      </div>
    )},
  ];

  const inputClass = 'w-full rounded-lg border border-gray-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 px-3 py-2 text-sm text-gray-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent';

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="التوظيف"
          subtitle={tab === 'postings' ? `${postingsQuery.data?.total || 0} إعلان وظيفة` : `${candidatesQuery.data?.total || 0} متقدم`}
          icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" /></svg>}
          actions={tab === 'postings'
            ? <button onClick={openAddPosting} className="btn-primary">إعلان وظيفة جديد</button>
            : <button onClick={openAddCandidate} className="btn-primary">متقدم جديد</button>}
        />
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        <button onClick={() => { setTab('postings'); setPage(1); setStatusFilter('all'); }} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'postings' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
          إعلانات الوظائف
        </button>
        <button onClick={() => { setTab('candidates'); setPage(1); setStatusFilter('all'); }} className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${tab === 'candidates' ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
          المتقدمون
        </button>
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-zinc-700">
        {activeTabs.map((t) => (
          <button key={t.key} onClick={() => { setStatusFilter(t.key); setPage(1); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${statusFilter === t.key ? 'border-primary-500 text-primary-600' : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200'}`}>
            {t.label}
          </button>
        ))}
      </div>

      <DataTable
        columns={tab === 'postings' ? postingColumns : candidateColumns}
        data={activeItems as any}
        loading={activeQuery.isLoading}
        totalItems={activeQuery.data?.total || 0}
        page={page}
        pageSize={10}
        onPageChange={setPage}
        keepPreviousData
      />

      {/* Job Posting Modal */}
      <Modal isOpen={showPostingModal} onClose={() => { setShowPostingModal(false); setEditingPosting(null); resetPostingForm(); }} title={editingPosting ? 'تعديل إعلان الوظيفة' : 'إعلان وظيفة جديد'} size="lg">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">المسمى الوظيفي</label>
              <input value={postingForm.title} onChange={(e) => setPostingForm({ ...postingForm, title: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">عدد الوظائف الشاغرة</label>
              <input type="number" min="1" value={postingForm.vacancies} onChange={(e) => setPostingForm({ ...postingForm, vacancies: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">القسم</label>
              <select value={postingForm.departmentId} onChange={(e) => setPostingForm({ ...postingForm, departmentId: e.target.value })} className={inputClass}>
                <option value="">— بدون —</option>
                {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">المنصب</label>
              <select value={postingForm.positionId} onChange={(e) => setPostingForm({ ...postingForm, positionId: e.target.value })} className={inputClass}>
                <option value="">— بدون —</option>
                {positions.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الحد الأدنى للراتب</label>
              <input type="number" min="0" value={postingForm.salaryMin} onChange={(e) => setPostingForm({ ...postingForm, salaryMin: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الحد الأقصى للراتب</label>
              <input type="number" min="0" value={postingForm.salaryMax} onChange={(e) => setPostingForm({ ...postingForm, salaryMax: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الموقع</label>
              <input type="text" value={postingForm.location} onChange={(e) => setPostingForm({ ...postingForm, location: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">نوع العمل</label>
              <select value={postingForm.employmentType} onChange={(e) => setPostingForm({ ...postingForm, employmentType: e.target.value })} className={inputClass}>
                {employmentTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="label">تاريخ النشر</label>
              <input type="date" value={postingForm.postedDate} onChange={(e) => setPostingForm({ ...postingForm, postedDate: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">آخر موعد للتقديم</label>
              <input type="date" value={postingForm.deadline} onChange={(e) => setPostingForm({ ...postingForm, deadline: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الحالة</label>
              <select value={postingForm.status} onChange={(e) => setPostingForm({ ...postingForm, status: e.target.value })} className={inputClass}>
                <option value="open">مفتوحة</option>
                <option value="closed">مغلقة</option>
              </select>
            </div>
          </div>
          <div>
            <label className="label">الوصف</label>
            <textarea value={postingForm.description} onChange={(e) => setPostingForm({ ...postingForm, description: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div>
            <label className="label">المتطلبات</label>
            <textarea value={postingForm.requirements} onChange={(e) => setPostingForm({ ...postingForm, requirements: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowPostingModal(false); setEditingPosting(null); resetPostingForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editingPosting ? updatePostingMutation : createPostingMutation).mutate()}
              disabled={!postingForm.title || createPostingMutation.isPending || updatePostingMutation.isPending}
              className="btn-primary"
            >
              {createPostingMutation.isPending || updatePostingMutation.isPending ? 'جاري الحفظ...' : editingPosting ? 'تحديث' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      {/* Candidate Modal */}
      <Modal isOpen={showCandidateModal} onClose={() => { setShowCandidateModal(false); setEditingCandidate(null); resetCandidateForm(); }} title={editingCandidate ? 'تعديل المتقدم' : 'متقدم جديد'} size="md">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">الاسم</label>
              <input value={candidateForm.name} onChange={(e) => setCandidateForm({ ...candidateForm, name: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الوظيفة</label>
              <select value={candidateForm.jobPostingId} onChange={(e) => setCandidateForm({ ...candidateForm, jobPostingId: e.target.value })} className={inputClass}>
                <option value="">— بدون —</option>
                {postings.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
              </select>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">البريد الإلكتروني</label>
              <input type="email" value={candidateForm.email} onChange={(e) => setCandidateForm({ ...candidateForm, email: e.target.value })} className={inputClass} />
            </div>
            <div>
              <label className="label">الهاتف</label>
              <input type="tel" value={candidateForm.phone} onChange={(e) => setCandidateForm({ ...candidateForm, phone: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">المصدر</label>
              <input type="text" value={candidateForm.source} onChange={(e) => setCandidateForm({ ...candidateForm, source: e.target.value })} className={inputClass} placeholder="مثال: لينكد إن" />
            </div>
            <div>
              <label className="label">التقييم (1-5)</label>
              <input type="number" min="0" max="5" step="1" value={candidateForm.rating} onChange={(e) => setCandidateForm({ ...candidateForm, rating: e.target.value })} className={inputClass} />
            </div>
          </div>
          <div>
            <label className="label">الحالة</label>
            <select value={candidateForm.status} onChange={(e) => setCandidateForm({ ...candidateForm, status: e.target.value })} className={inputClass}>
              {candidateStatusTabs.filter((t) => t.key !== 'all').map((t) => <option key={t.key} value={t.key}>{t.label}</option>)}
            </select>
          </div>
          <div>
            <label className="label">ملخص السيرة الذاتية</label>
            <textarea value={candidateForm.resumeText} onChange={(e) => setCandidateForm({ ...candidateForm, resumeText: e.target.value })} className={inputClass} rows={3} />
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <textarea value={candidateForm.notes} onChange={(e) => setCandidateForm({ ...candidateForm, notes: e.target.value })} className={inputClass} rows={2} />
          </div>
          <div className="flex justify-end gap-2">
            <button onClick={() => { setShowCandidateModal(false); setEditingCandidate(null); resetCandidateForm(); }} className="btn-secondary">إلغاء</button>
            <button
              onClick={() => (editingCandidate ? updateCandidateMutation : createCandidateMutation).mutate()}
              disabled={!candidateForm.name || createCandidateMutation.isPending || updateCandidateMutation.isPending}
              className="btn-primary"
            >
              {createCandidateMutation.isPending || updateCandidateMutation.isPending ? 'جاري الحفظ...' : editingCandidate ? 'تحديث' : 'حفظ'}
            </button>
          </div>
        </div>
      </Modal>

      <ConfirmDialog
        isOpen={showDeletePosting !== null}
        onClose={() => setShowDeletePosting(null)}
        onConfirm={() => showDeletePosting && deletePostingMutation.mutate(showDeletePosting.id)}
        title="حذف إعلان الوظيفة"
        message={`هل أنت متأكد من حذف "${showDeletePosting?.title}"؟`}
        variant="danger"
      />

      <ConfirmDialog
        isOpen={showDeleteCandidate !== null}
        onClose={() => setShowDeleteCandidate(null)}
        onConfirm={() => showDeleteCandidate && deleteCandidateMutation.mutate(showDeleteCandidate.id)}
        title="حذف المتقدم"
        message={`هل أنت متأكد من حذف "${showDeleteCandidate?.name}"؟`}
        variant="danger"
      />
    </div>
  );
}
