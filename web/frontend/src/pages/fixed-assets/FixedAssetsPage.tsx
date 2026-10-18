import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getFixedAssets, createFixedAsset, calculateDepreciation, getFixedAssetsSummary, getAssetCategories } from '@/api/fixedAssets';
import { Modal } from '@/components/ui/Modal';
import { StatsCard } from '@/components/ui/StatsCard';

export default function FixedAssetsPage() {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedAsset, setSelectedAsset] = useState<any>(null);
  const [showDepreciationModal, setShowDepreciationModal] = useState(false);
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

  const createMutation = useMutation({
    mutationFn: createFixedAsset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets'] });
      setShowCreateModal(false);
    },
  });

  const depreciateMutation = useMutation({
    mutationFn: ({ assetId, month, year }: any) => calculateDepreciation(assetId, month, year),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['fixed-assets'] });
      setShowDepreciationModal(false);
    },
  });

  const statusColors: Record<string, string> = {
    ACTIVE: 'bg-green-100 text-green-800',
    FULLY_DEPRECIATED: 'bg-yellow-100 text-yellow-800',
    DISPOSED: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">الأصول الثابتة</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg"
        >
          إضافة أصل جديد
        </button>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatsCard title="عدد الأصول" value={summary.total_assets} />
          <StatsCard title="التكلفة الإجمالية" value={summary.total_cost?.toLocaleString()} />
          <StatsCard title="الإهلاك المتراكم" value={summary.total_accumulated_depreciation?.toLocaleString()} />
          <StatsCard title="القيمة الدفترية" value={summary.total_book_value?.toLocaleString()} />
        </div>
      )}

      {/* Filters */}
      <div className="bg-white p-4 rounded-lg shadow flex gap-4">
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value ? Number(e.target.value) : '')}
          className="border rounded-lg px-3 py-2"
        >
          <option value="">جميع الفئات</option>
          {categories?.map((cat: any) => (
            <option key={cat.id} value={cat.id}>{cat.name}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="border rounded-lg px-3 py-2"
        >
          <option value="">جميع الحالات</option>
          <option value="ACTIVE">نشط</option>
          <option value="FULLY_DEPRECIATED">محول بالكامل</option>
          <option value="DISPOSED">تم التصفية</option>
        </select>
      </div>

      {/* Assets Table */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-right">الرمز</th>
              <th className="px-4 py-3 text-right">الاسم</th>
              <th className="px-4 py-3 text-right">تاريخ الشراء</th>
              <th className="px-4 py-3 text-right">التكلفة</th>
              <th className="px-4 py-3 text-right">الإهلاك</th>
              <th className="px-4 py-3 text-right">القيمة الدفترية</th>
              <th className="px-4 py-3 text-right">الحالة</th>
              <th className="px-4 py-3 text-right">الإجراءات</th>
            </tr>
          </thead>
          <tbody>
            {assets?.map((asset: any) => (
              <tr key={asset.id} className="border-t hover:bg-gray-50">
                <td className="px-4 py-3">{asset.code}</td>
                <td className="px-4 py-3">{asset.name}</td>
                <td className="px-4 py-3">{asset.purchase_date}</td>
                <td className="px-4 py-3">{asset.purchase_cost?.toLocaleString()}</td>
                <td className="px-4 py-3">{asset.accumulated_depreciation?.toLocaleString()}</td>
                <td className="px-4 py-3">{asset.current_value?.toLocaleString()}</td>
                <td className="px-4 py-3">
                  <span className={`px-2 py-1 rounded-full text-xs ${statusColors[asset.status] || ''}`}>
                    {asset.status === 'ACTIVE' ? 'نشط' : asset.status === 'FULLY_DEPRECIATED' ? 'محول بالكامل' : 'تم التصفية'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  {asset.status === 'ACTIVE' && (
                    <button
                      onClick={() => {
                        setSelectedAsset(asset);
                        setShowDepreciationModal(true);
                      }}
                      className="text-blue-600 hover:underline ml-2"
                    >
                      إهلاك شهري
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {isLoading && <div className="text-center py-4">جاري التحميل...</div>}
        {assets?.length === 0 && <div className="text-center py-4 text-gray-500">لا توجد أصول</div>}
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
                <label className="block text-sm font-medium mb-1">الرمز</label>
                <input name="code" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">الاسم</label>
                <input name="name" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">الفئة</label>
                <select name="category_id" required className="w-full border rounded-lg px-3 py-2">
                  <option value="">اختر الفئة</option>
                  {categories?.map((cat: any) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">تاريخ الشراء</label>
                <input name="purchase_date" type="date" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">التكلفة</label>
                <input name="purchase_cost" type="number" step="0.01" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">العمر الإنتاجي (شهور)</label>
                <input name="useful_life_months" type="number" required className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">القيمة التخليصية</label>
                <input name="salvage_value" type="number" step="0.01" className="w-full border rounded-lg px-3 py-2" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">الموقع</label>
                <input name="location" className="w-full border rounded-lg px-3 py-2" />
              </div>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowCreateModal(false)} className="px-4 py-2 border rounded-lg">إلغاء</button>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">حفظ</button>
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
                <label className="block text-sm font-medium mb-1">الشهر</label>
                <select name="month" className="w-full border rounded-lg px-3 py-2">
                  {[1,2,3,4,5,6,7,8,9,10,11,12].map(m => (
                    <option key={m} value={m}>{m}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">السنة</label>
                <input name="year" type="number" defaultValue={new Date().getFullYear()} className="w-full border rounded-lg px-3 py-2" />
              </div>
            </div>
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm"><strong>الأصل:</strong> {selectedAsset.name}</p>
              <p className="text-sm"><strong>التكلفة:</strong> {selectedAsset.purchase_cost?.toLocaleString()}</p>
              <p className="text-sm"><strong>الإهلاك الحالي:</strong> {selectedAsset.accumulated_depreciation?.toLocaleString()}</p>
              <p className="text-sm"><strong>القيمة الدفترية:</strong> {selectedAsset.current_value?.toLocaleString()}</p>
            </div>
            <div className="flex justify-end gap-2">
              <button type="button" onClick={() => setShowDepreciationModal(false)} className="px-4 py-2 border rounded-lg">إلغاء</button>
              <button type="submit" className="px-4 py-2 bg-blue-600 text-white rounded-lg">حساب الإهلاك</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
