import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { ConfirmDialog } from '@/components/ui/ConfirmDialog';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '@/stores/authStore';
import { getPromotions, createPromotion, updatePromotion, togglePromotion, deletePromotion } from '@/api/promotions';
import type { Promotion } from '@/types';
import { IconTarget, IconPlus, IconPencil, IconTrash } from '@/components/ui/Icons';
import { formatCurrency } from '@/lib/utils';

const STATUS_BADGE: Record<string, string> = {
  active: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  scheduled: 'bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-400',
  paused: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  expired: 'bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-zinc-400',
  draft: 'bg-gray-100 text-gray-600 dark:bg-zinc-800 dark:text-zinc-400',
};

const STATUS_AR: Record<string, string> = {
  active: 'نشط',
  scheduled: 'مجدول',
  paused: 'متوقف',
  expired: 'منتهي',
  draft: 'مسودة',
};

interface PromotionFormValues {
  name: string;
  code?: string;
  description?: string;
  promoType: 'percentage' | 'fixed';
  discountValue: number;
  appliesTo: 'all' | 'category' | 'product';
  targetName?: string;
  minPurchase: number;
  maxDiscount?: number;
  startDate?: string;
  endDate?: string;
  usageLimit?: number;
  priority: number;
  isActive: boolean;
}

export default function PromotionsPage() {
  const queryClient = useQueryClient();
  const { branchId, user } = useAuthStore();
  const { register, handleSubmit, reset, watch } = useForm<PromotionFormValues>();
  const promoType = watch('promoType');
  const [showModal, setShowModal] = useState(false);
  const [editing, setEditing] = useState<Promotion | null>(null);
  const [deleting, setDeleting] = useState<Promotion | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['promotions'],
    queryFn: () => getPromotions(),
  });
  const promotions: Promotion[] = data?.items || [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['promotions'] });

  const saveMutation = useMutation({
    mutationFn: (payload: Partial<Promotion>) =>
      editing ? updatePromotion(editing.id, payload) : createPromotion(payload),
    onSuccess: () => { invalidate(); setShowModal(false); setEditing(null); reset(); },
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => togglePromotion(id),
    onSuccess: invalidate,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deletePromotion(id),
    onSuccess: () => { invalidate(); setDeleting(null); },
  });

  const openCreate = () => {
    setEditing(null);
    reset({
      promoType: 'percentage',
      appliesTo: 'all',
      discountValue: 0,
      minPurchase: 0,
      priority: 0,
      isActive: true,
    });
    setShowModal(true);
  };

  const openEdit = (p: Promotion) => {
    setEditing(p);
    reset({
      name: p.name,
      code: p.code,
      description: p.description,
      promoType: p.promoType,
      discountValue: p.discountValue,
      appliesTo: p.appliesTo,
      targetName: p.targetName,
      minPurchase: p.minPurchase,
      maxDiscount: p.maxDiscount ?? undefined,
      startDate: p.startDate?.slice(0, 10),
      endDate: p.endDate?.slice(0, 10),
      usageLimit: p.usageLimit ?? undefined,
      priority: p.priority,
      isActive: p.isActive,
    });
    setShowModal(true);
  };

  const onSubmit = (values: PromotionFormValues) => {
    saveMutation.mutate({
      ...values,
      companyId: Number(user?.companyId || 1),
      branchId: branchId ?? 1,
    });
  };

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'العرض',
      render: (item) => (
        <div>
          <p className="font-medium">{String(item.name)}</p>
          {!!item.code && <p className="text-xs text-gray-400">{String(item.code)}</p>}
        </div>
      ),
    },
    {
      key: 'discount',
      header: 'الخصم',
      render: (item) => (
        <span className="font-semibold text-primary-600">
          {item.promoType === 'fixed'
            ? formatCurrency(Number(item.discountValue))
            : `${Number(item.discountValue)}%`}
        </span>
      ),
    },
    {
      key: 'appliesTo',
      header: 'التطبيق',
      render: (item) => (
        <div>
          <span className="badge-primary">
            {item.appliesTo === 'all' ? 'كل المنتجات' : item.appliesTo === 'category' ? 'تصنيف' : 'منتج'}
          </span>
          {!!item.targetName && <p className="text-xs text-gray-400 mt-0.5">{String(item.targetName)}</p>}
        </div>
      ),
    },
    {
      key: 'dates',
      header: 'المدة',
      render: (item) => (
        <div className="text-xs text-gray-500">
          <p>{item.startDate ? `من ${String(item.startDate).slice(0, 10)}` : 'بدون تاريخ بدء'}</p>
          <p>{item.endDate ? `إلى ${String(item.endDate).slice(0, 10)}` : 'بدون تاريخ نهاية'}</p>
        </div>
      ),
    },
    {
      key: 'usage',
      header: 'الاستخدام',
      render: (item) => (
        <span className="text-xs">
          {String(item.usedCount)}
          {item.usageLimit ? ` / ${item.usageLimit}` : ''}
        </span>
      ),
    },
    {
      key: 'status',
      header: 'الحالة',
      render: (item) => {
        const s = String(item.status || '');
        return <span className={`badge ${STATUS_BADGE[s] || STATUS_BADGE.draft}`}>{STATUS_AR[s] || s}</span>;
      },
    },
    {
      key: 'actions',
      header: 'إجراءات',
      render: (item) => (
        <div className="flex gap-1">
          <button className="btn-ghost p-1" onClick={(e) => { e.stopPropagation(); openEdit(item as unknown as Promotion); }}>
            <IconPencil className="h-4 w-4" />
          </button>
          <button
            className="btn-ghost p-1"
            title={item.isActive ? 'إيقاف' : 'تفعيل'}
            onClick={(e) => { e.stopPropagation(); toggleMutation.mutate(Number(item.id)); }}
          >
            <span className={`h-2.5 w-2.5 rounded-full ${item.isActive ? 'bg-emerald-500' : 'bg-gray-400'}`} />
          </button>
          <button className="btn-ghost p-1 text-red-600" onClick={(e) => { e.stopPropagation(); setDeleting(item as unknown as Promotion); }}>
            <IconTrash className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="العروض الترويجية"
        subtitle="إدارة خصومات وعروض المبيعات"
        icon={<IconTarget className="h-6 w-6" />}
        actions={
          <button className="btn-primary" onClick={openCreate}>
            <IconPlus className="h-4 w-4 ml-1 inline" /> عرض جديد
          </button>
        }
      />

      {promotions.length === 0 && !isLoading ? (
        <EmptyState title="لا توجد عروض ترويجية" description="أنشئ أول عرض لتفعيل الخصومات التلقائية" />
      ) : (
        <DataTable
          columns={columns}
          data={(promotions as unknown) as Record<string, unknown>[]}
          loading={isLoading}
          emptyTitle="لا توجد عروض"
          onRowClick={(item) => openEdit(item as unknown as Promotion)}
        />
      )}

      <Modal isOpen={showModal} onClose={() => { setShowModal(false); setEditing(null); }} title={editing ? 'تعديل العرض' : 'عرض ترويجي جديد'}>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">اسم العرض *</label><input className="input" {...register('name', { required: true })} /></div>
            <div><label className="label">الكود</label><input className="input" placeholder="PROMO-001" {...register('code')} /></div>
          </div>
          <div><label className="label">الوصف</label><textarea className="input" rows={2} {...register('description')} /></div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">نوع الخصم</label>
              <select className="input" {...register('promoType')}>
                <option value="percentage">نسبة مئوية (%)</option>
                <option value="fixed">مبلغ ثابت</option>
              </select>
            </div>
            <div>
              <label className="label">{promoType === 'percentage' ? 'قيمة الخصم (%)' : 'قيمة الخصم (مبلغ)'}</label>
              <input type="number" step="0.01" className="input" {...register('discountValue', { valueAsNumber: true })} />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="label">نطاق التطبيق</label>
              <select className="input" {...register('appliesTo')}>
                <option value="all">كل المنتجات</option>
                <option value="category">تصنيف محدد</option>
                <option value="product">منتج محدد</option>
              </select>
            </div>
            <div><label className="label">التصنيف / المنتج المستهدف</label><input className="input" {...register('targetName')} /></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div><label className="label">حد أدنى للشراء</label><input type="number" step="0.01" className="input" {...register('minPurchase', { valueAsNumber: true })} /></div>
            <div><label className="label">حد أقصى للخصم</label><input type="number" step="0.01" className="input" {...register('maxDiscount', { valueAsNumber: true })} /></div>
            <div><label className="label">حد الاستخدام</label><input type="number" className="input" {...register('usageLimit', { valueAsNumber: true })} /></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div><label className="label">تاريخ البدء</label><input type="date" className="input" {...register('startDate')} /></div>
            <div><label className="label">تاريخ الانتهاء</label><input type="date" className="input" {...register('endDate')} /></div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 items-center">
            <div><label className="label">الأولوية</label><input type="number" className="input" {...register('priority', { valueAsNumber: true })} /></div>
            <label className="flex items-center gap-2 text-sm mt-4"><input type="checkbox" className="h-4 w-4" {...register('isActive')} /> عرض نشط</label>
          </div>

          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => { setShowModal(false); setEditing(null); }}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
              {saveMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>

      <ConfirmDialog
        isOpen={!!deleting}
        onClose={() => setDeleting(null)}
        onConfirm={() => deleting && deleteMutation.mutate(deleting.id)}
        title="حذف العرض"
        message={`هل أنت متأكد من حذف العرض "${deleting?.name}"؟`}
        confirmText="حذف"
      />
    </div>
  );
}