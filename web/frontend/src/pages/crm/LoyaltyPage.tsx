import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { EmptyState } from '@/components/ui/EmptyState';
import { useForm } from 'react-hook-form';
import { getLoyaltyList, adjustCustomerLoyalty, type LoyaltyCustomerRow } from '@/api/crm';
import { IconStar, IconPlus } from '@/components/ui/Icons';
import { cn } from '@/lib/utils';

const TIER_STYLE: Record<string, string> = {
  platinum: 'bg-zinc-800 text-white',
  gold: 'bg-amber-100 text-amber-800',
  silver: 'bg-gray-100 text-gray-700',
  regular: 'bg-sky-100 text-sky-800',
};

const TIER_AR: Record<string, string> = {
  platinum: 'بلاتيني',
  gold: 'ذهبي',
  silver: 'فضي',
  regular: 'عادي',
};

function computeTier(points: number): string {
  if (points >= 1500) return 'platinum';
  if (points >= 800) return 'gold';
  if (points >= 300) return 'silver';
  return 'regular';
}

interface AdjustForm {
  points: number;
}

export default function LoyaltyPage() {
  const queryClient = useQueryClient();
  const { register, handleSubmit, reset } = useForm<AdjustForm>();
  const [search, setSearch] = useState('');
  const [adjusting, setAdjusting] = useState<LoyaltyCustomerRow | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['crm-loyalty', search],
    queryFn: () => getLoyaltyList({ search: search || undefined, page: 1, pageSize: 100 }),
  });
  const rows: LoyaltyCustomerRow[] = data?.items || [];

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['crm-loyalty'] });

  const adjustMutation = useMutation({
    mutationFn: (points: number) => adjustCustomerLoyalty(adjusting!.customerId, points),
    onSuccess: () => { invalidate(); setAdjusting(null); reset(); },
  });

  const openAdjust = (row: LoyaltyCustomerRow) => {
    setAdjusting(row);
    reset({ points: 0 });
  };

  const columns: Column<Record<string, unknown>>[] = [
    {
      key: 'name',
      header: 'العميل',
      render: (item) => (
        <div>
          <p className="font-medium">{String(item.customerName)}</p>
          {!!item.customerPhone && <p className="text-xs text-gray-400">{String(item.customerPhone)}</p>}
        </div>
      ),
    },
    {
      key: 'pointsBalance',
      header: 'رصيد النقاط',
      render: (item) => <span className="font-semibold text-primary-600">{Number(item.pointsBalance).toLocaleString()}</span>,
    },
    {
      key: 'totalPointsEarned',
      header: 'إجمالي النقاط المكتسبة',
      render: (item) => <span>{Number(item.totalPointsEarned).toLocaleString()}</span>,
    },
    {
      key: 'tier',
      header: 'المستوى',
      render: (item) => {
        const tier = computeTier(Number(item.pointsBalance));
        return (
          <span className={cn('badge', TIER_STYLE[tier])}>{TIER_AR[tier]}</span>
        );
      },
    },
    {
      key: 'actions',
      header: 'إجراءات',
      render: (item) => (
        <button className="btn-ghost p-1.5 text-primary-600" onClick={(e) => { e.stopPropagation(); openAdjust(item as unknown as LoyaltyCustomerRow); }}>
          <IconPlus className="h-4 w-4" /> تعديل
        </button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="برنامج الولاء"
        subtitle="نقاط العملاء والمستويات"
        icon={<IconStar className="h-6 w-6" />}
        actions={
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="بحث عن عميل..."
            className="input w-64"
          />
        }
      />

      {rows.length === 0 && !isLoading ? (
        <EmptyState title="لا توجد بيانات ولاء" description="ابدأ بمنح أول عميل نقاط ولاء" />
      ) : (
        <DataTable
          columns={columns}
          data={(rows as unknown) as Record<string, unknown>[]}
          loading={isLoading}
          emptyTitle="لا توجد نتائج"
        />
      )}

      <Modal isOpen={!!adjusting} onClose={() => setAdjusting(null)} title={`تعديل نقاط: ${adjusting?.customerName || ''}`}>
        <form onSubmit={handleSubmit((d) => adjustMutation.mutate(Number(d.points)))} className="space-y-4">
          <div>
            <label className="label">عدد النقاط (قيمة موجبة للإضافة، سالبة للخصم)</label>
            <input type="number" step="1" className="input" {...register('points', { required: true, valueAsNumber: true })} autoFocus />
          </div>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn-ghost" onClick={() => setAdjusting(null)}>إلغاء</button>
            <button type="submit" className="btn-primary" disabled={adjustMutation.isPending}>
              {adjustMutation.isPending ? 'جارٍ الحفظ...' : 'حفظ'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}