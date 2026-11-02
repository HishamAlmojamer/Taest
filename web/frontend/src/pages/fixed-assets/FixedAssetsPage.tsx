import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getFixedAssets, createFixedAsset, calculateDepreciation, getFixedAssetsSummary, getAssetCategories, getDepreciationSchedule, disposeFixedAsset, createAssetCategory } from '@/api/fixedAssets';
import { Modal } from '@/components/ui/Modal';
import { StatsCard } from '@/components/ui/StatsCard';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

const statusColors: Record<string, string> = {
  ACTIVE: 'badge-success',
  FULLY_DEPRECIATED: 'badge-warning',
  DISPOSED: 'badge-danger',
};

const statusLabels: Record<string, string> = {
  ACTIVE: 'نشط',
  FULLY_DEPRECIATED: 'محوّل بالكامل',
  DISPOSED: 'تم التصفية',
};

function AssetDetails({ asset }: { asset: any }) {
  return (
    <div className="bg-gray-50 dark:bg-zinc-800/50 p-4 rounded-lg space-y-1">
      <p className="text-sm"><strong>الأصل:</strong> {asset.code} — {asset.name}</p>
      <p className="text-sm"><strong>التكلفة:</strong> {asset.purchase_cost?.toLocaleString()}</p>
      <p className="text-sm"><strong>الإهلاك المتراكم:</strong> {asset.accumulated_depreciation?.toLocaleString()}</p>
      <p className="text-sm"><strong>القيمة الدفترية:</strong> {asset.current_value?.toLocaleString()}</p>
      <p className="text-sm"><strong>تاريخ الشراء:</strong> {asset.purchase_date}</p>
    </div>
  );
}

export default function FixedAssetsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [showDepreciationModal, setShowDepreciationModal] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [showDisposeModal, setShowDisposeModal] = useState(false);
  const [showCategoriesModal, setShowCategoriesModal] = useState(false);
  const [filterCategory, setFilterCategory] = useState<number | ''>('');
  const [filterStatus, setFilterStatus] = useState('');

  const { data: assets, isLoading } = useQuery({
    queryKey: ['fixed-assets', filterCategory, filterStatus],
    queryFn: () => getFixedAssets(filterCategory as number || undefined, filterStatus || undefined),
  });

  const { data: summary } = useQuery({
    queryKey: ['fixed-assets-summary'],
    queryFn: getFixedAssetsSummary,
  });

  const { data: categories } = useQuery({
    queryKey: ['asset-categories'],
    queryFn: getAssetCategories,
  });

  const { data: schedule } = useQuery({
    queryKey: ['depreciation-schedule', selectedAsset?.id],
    queryFn: () => getDepreciationSchedule(selectedAsset.id),
    enabled: showScheduleModal && !!selectedAsset,
  });

  const createMutation = useMutation({
    mutationFn: createFixedAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets'] });
      queryClient.invalidateQueries({ queryKey: ['fixed-assets-summary'] });
      toast.success('تم إضافة الأصل بنجاح');
      setShowCreateModal(false);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const depreciateMutation = useMutation({
    mutationFn: ({ assetId, month, year }: any) => calculateDepreciation(assetId, month, year),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets'] });
      queryClient.invalidateQueries({ queryKey: ['fixed-assets-summary'] });
      toast.success('تم حساب الإهلاك بنجاح');
      setShowDepreciationModal(false);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const disposeMutation = useMutation({
    mutationFn: ({ assetId, data }: any) => disposeFixedAsset(assetId, data),
    onSuccess: (res: any) => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets'] });
      queryClient.invalidateQueries({ queryKey: ['fixed-assets-summary'] });
      toast.success('تمت تصفية الأصل، قيد اليومية رقم ' + (res?.journal_entry_id || ''));
      setShowDisposeModal(false);
      setSelectedAsset(null);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const categoryMutation = useMutation({
    mutationFn: createAssetCategory,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['asset-categories'] });
      toast.success('تمت إضافة الفئة بنجاح');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="الأصول الثابتة"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" /></svg>}
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={() => setShowCategoriesModal(true)}
              className="btn-secondary"
            >
              إدارة الفئات
            </button>
            <button
              onClick={() => setShowCreateModal(true)}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg"
            >
              إضافة أصل جديد
            </button>
          </div>
        }
      />

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatsCard title="عدد الأصول" value={summary.total_assets} />
          <StatsCard title="التكلفة الإجمالية" value={Number(summary.total_cost || 0)} currency color="blue" />
          <StatsCard title="الإهلاك المتراكم" value={Number(summary.total_accumulated_depreciation || 0)} currency color="yellow" />
          <StatsCard title="القيمة الدفترية" value={Number(summary.total_book_value || 0)} currency color="green" />
        </div>
      )}

      {/* Filters */}
      <div className="card p-4 flex gap-4">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value ? Number(e.target.value) : '')}
          className="select"
        >
          <option value="">جميع الفئات</option>
          {categories?.map((cat: any) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="select"
        >
          <option value="">جميع الحالات</option>
          <option value="ACTIVE">نشط</option>
          <option value="FULLY_DEPRECIATED">محول بالكامل</option>
          <option value="DISPOSED">تم التصفية</option>
        </select>
      </div>

      {/* Assets Table */}
      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <LoadingSpinner />
          </div>
        ) : assets?.length === 0 ? (
          <EmptyState title="لا توجد أصول ثابتة" description="أضف أصلاً جديداً أو عدّل الفلاتر لعرض النتائج." />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[900px]" aria-label="قائمة الأصول الثابتة">
              <thead className="table-header">
                <tr>
                  <th scope="col" className="px-4 py-3 text-right">الرمز</th>
                  <th scope="col" className="px-4 py-3 text-right">الاسم</th>
                  <th scope="col" className="px-4 py-3 text-right">تاريخ الشراء</th>
                  <th scope="col" className="px-4 py-3 text-right">التكلفة</th>
                  <th scope="col" className="px-4 py-3 text-right">الإهلاك</th>
                  <th scope="col" className="px-4 py-3 text-right">القيمة الدفترية</th>
                  <th scope="col" className="px-4 py-3 text-right">الحالة</th>
                  <th scope="col" className="px-4 py-3 text-right">الإجراءات</th>
                </tr>
              </thead>
              <tbody>
                {assets?.map((asset: any) => (
                  <tr key={asset.id} className="table-row">
                    <td className="whitespace-nowrap px-4 py-3 font-mono text-xs text-gray-600 dark:text-zinc-400">{asset.code}</td>
                    <td className="px-4 py-3 text-sm">{asset.name}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">{asset.purchase_date}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">{asset.purchase_cost?.toLocaleString()}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm tabular-nums">{asset.accumulated_depreciation?.toLocaleString()}</td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm font-medium tabular-nums">{asset.current_value?.toLocaleString()}</td>
                    <td className="px-4 py-3 text-sm">
                      <span className={statusColors[asset.status] || 'badge-gray'}>
                        {statusLabels[asset.status] || asset.status}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-4 py-3 text-sm">
                      <div className="flex items-center gap-3">
                        <button
                          type="button"
                          onClick={() => {
                            setSelectedAsset(asset);
                            setShowScheduleModal(true);
                          }}
                          className="font-medium text-gray-600 hover:underline dark:text-zinc-300"
                        >
                          جدول الإهلاك
                        </button>
                        {asset.status === 'ACTIVE' && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedAsset(asset);
                              setShowDepreciationModal(true);
                            }}
                            className="font-medium text-blue-600 hover:underline dark:text-blue-400"
                          >
                            إهلاك شهري
                          </button>
                        )}
                        {asset.status !== 'DISPOSED' && (
                          <button
                            type="button"
                            onClick={() => {
                              setSelectedAsset(asset);
                              setShowDisposeModal(true);
                            }}
                            className="font-medium text-red-600 hover:underline dark:text-red-400"
                          >
                            تصفية
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Asset Modal */}
      {showCreateModal && (
        <Modal onClose={() => setShowCreateModal(false)} title="إضافة أصل جديد">
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            createMutation.mutate({
              code: formData.get('code'),
              name: formData.get('name'),
              category_id: Number(formData.get('category_id')),
              purchase_date: formData.get('purchase_date'),
              purchase_cost: Number(formData.get('purchase_cost')),
              useful_life_months: Number(formData.get('useful_life_months')),
              salvage_value: Number(formData.get('salvage_value') || 0),
              location: formData.get('location'),
            });
          }} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">الرمز</label>
                <input name="code" required className="input" />
              </div>
              <div>
                <label className="label">الاسم</label>
                <input name="name" required className="input" />
              </div>
              <div>
                <label className="label">الفئة</label>
                <select name="category_id" required className="select">
                  <option value="">اختر الفئة</option>
                  {categories?.map((cat: any) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">تاريخ الشراء</label>
                <input name="purchase_date" type="date" required className="input" />
              </div>
              <div>
                <label className="label">التكلفة</label>
                <input name="purchase_cost" type="number" step="0.01" required className="input" />
              </div>
              <div>
                <label className="label">العمر الإنتاجي (شهور)</label>
                <input name="useful_life_months" type="number" required className="input" />
              </div>
              <div>
                <label className="label">القيمة التخليصية</label>
                <input name="salvage_value" type="number" step="0.01" className="input" />
              </div>
              <div>
                <label className="label">الموقع</label>
                <input name="location" className="input" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreateModal(false)} className="btn-secondary">إلغاء</button>
              <button type="submit" className="btn-primary">حفظ</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Depreciation Modal */}
      {showDepreciationModal && selectedAsset && (
        <Modal onClose={() => setShowDepreciationModal(false)} title="حساب الإهلاك الشهري">
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            depreciateMutation.mutate({
              assetId: selectedAsset.id,
              month: Number(formData.get('month')),
              year: Number(formData.get('year')),
            });
          }} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">الشهر</label>
                <select name="month" className="select">
                  {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="label">السنة</label>
                <input name="year" type="number" defaultValue={new Date().getFullYear()} className="input" />
              </div>
            </div>
            <AssetDetails asset={selectedAsset} />
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowDepreciationModal(false)} className="btn-secondary">إلغاء</button>
              <button type="submit" className="btn-primary">حساب الإهلاك</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Depreciation Schedule Modal */}
      {showScheduleModal && selectedAsset && (
        <Modal onClose={() => { setShowScheduleModal(false); setSelectedAsset(null); }} title={`جدول إهلاك: ${selectedAsset.name}`}>
          <div className="space-y-4">
            <AssetDetails asset={selectedAsset} />
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="table-header">
                  <tr>
                    <th className="px-4 py-2 text-right">الفترة</th>
                    <th className="px-4 py-2 text-right">قيمة الإهلاك</th>
                    <th className="px-4 py-2 text-right">المتراكم</th>
                    <th className="px-4 py-2 text-right">القيمة الدفترية</th>
                  </tr>
                </thead>
                <tbody>
                  {schedule?.map((row: any) => (
                    <tr key={row.id} className="table-row">
                      <td className="px-4 py-2 text-sm">{row.period_month}/{row.period_year}</td>
                      <td className="px-4 py-2 text-sm">{row.depreciation_amount?.toLocaleString()}</td>
                      <td className="px-4 py-2 text-sm">{row.accumulated_depreciation?.toLocaleString()}</td>
                      <td className="px-4 py-2 text-sm">{row.book_value?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {schedule?.length === 0 && (
                <p className="text-center py-4 text-gray-500 dark:text-zinc-400">لا توجد قيود إهلاك بعد</p>
              )}
            </div>
            <div className="flex justify-end">
              <button onClick={() => { setShowScheduleModal(false); setSelectedAsset(null); }} className="btn-secondary">إغلاق</button>
            </div>
          </div>
        </Modal>
      )}

      {/* Dispose Modal */}
      {showDisposeModal && selectedAsset && (
        <Modal onClose={() => { setShowDisposeModal(false); setSelectedAsset(null); }} title="تصفية أصل ثابت">
          <form onSubmit={(e) => {
            e.preventDefault();
            const formData = new FormData(e.target as HTMLFormElement);
            disposeMutation.mutate({
              assetId: selectedAsset.id,
              data: {
                disposal_date: formData.get('disposal_date'),
                disposal_amount: Number(formData.get('disposal_amount') || 0),
                reason: formData.get('reason'),
              },
            });
          }} className="space-y-4">
            <AssetDetails asset={selectedAsset} />
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">تاريخ التصفية</label>
                <input name="disposal_date" type="date" required defaultValue={new Date().toISOString().split('T')[0]} className="input" />
              </div>
              <div>
                <label className="label">قيمة البيع / المتحصلات</label>
                <input name="disposal_amount" type="number" step="0.01" placeholder="0.00" className="input" />
              </div>
            </div>
            <div>
              <label className="label">سبب التصفية</label>
              <input name="reason" className="input" />
            </div>
            <div className="rounded-lg bg-amber-50 dark:bg-amber-500/10 border border-amber-200 dark:border-amber-500/30 p-3 text-sm text-amber-700 dark:text-amber-400">
              سيتم إنشاء قيد يومية يثبت استبعاد الأصل من الدفاتر مع إثبات أي ربح أو خسارة.
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => { setShowDisposeModal(false); setSelectedAsset(null); }} className="btn-secondary">إلغاء</button>
              <button type="submit" className="btn-danger">تأكيد التصفية</button>
            </div>
          </form>
        </Modal>
      )}

      {/* Categories Modal */}
      {showCategoriesModal && (
        <Modal onClose={() => setShowCategoriesModal(false)} title="فئات الأصول الثابتة">
          <div className="space-y-4">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target as HTMLFormElement);
                categoryMutation.mutate({
                  code: formData.get('code'),
                  name: formData.get('name'),
                  name_ar: formData.get('name_ar'),
                  depreciation_rate: Number(formData.get('depreciation_rate') || 0),
                  useful_life_months: Number(formData.get('useful_life_months') || 0),
                  depreciation_method: formData.get('depreciation_method'),
                });
                (e.target as HTMLFormElement).reset();
              }}
              className="bg-gray-50 dark:bg-zinc-800/50 p-4 rounded-lg grid grid-cols-2 gap-3"
            >
              <input name="code" required placeholder="الرمز (مثال: EQUIP)" className="input" />
              <input name="name" required placeholder="الاسم" className="input" />
              <input name="name_ar" placeholder="الاسم بالعربية" className="input" />
              <select name="depreciation_method" className="select">
                <option value="STRAIGHT_LINE">القسط الثابت</option>
                <option value="DECLINING_BALANCE">الرصيد المتناقص</option>
              </select>
              <input name="depreciation_rate" type="number" step="0.01" placeholder="نسبة الإهلاك السنوية" className="input" />
              <input name="useful_life_months" type="number" placeholder="العمر الإنتاجي (شهور)" className="input" />
              <button type="submit" className="btn-primary col-span-2">إضافة الفئة</button>
            </form>

            <div className="max-h-80 overflow-y-auto">
              <table className="w-full">
                <thead className="table-header">
                  <tr>
                    <th className="px-4 py-2 text-right">الرمز</th>
                    <th className="px-4 py-2 text-right">الاسم</th>
                    <th className="px-4 py-2 text-right">الطريقة</th>
                    <th className="px-4 py-2 text-right">العمر (شهر)</th>
                  </tr>
                </thead>
                <tbody>
                  {categories?.map((cat: any) => (
                    <tr key={cat.id} className="table-row">
                      <td className="px-4 py-2 text-sm">{cat.code}</td>
                      <td className="px-4 py-2 text-sm">{cat.name}</td>
                      <td className="px-4 py-2 text-sm">{cat.depreciation_method === 'STRAIGHT_LINE' ? 'قسط ثابت' : 'متناقص'}</td>
                      <td className="px-4 py-2 text-sm">{cat.useful_life_months}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {categories?.length === 0 && (
                <p className="text-center py-4 text-gray-500 dark:text-zinc-400">لا توجد فئات بعد</p>
              )}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}