import { useMemo, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { DataTable, type Column } from '@/components/ui/DataTable';
import { PageHeader } from '@/components/ui/PageHeader';
import { Modal } from '@/components/ui/Modal';
import { useToast } from '@/components/ui/Toast';
import { getStockMovements, createStockMovement, getProducts, getWarehouses } from '@/api/inventory';
import { formatDate, formatCurrency, formatDateTime } from '@/lib/utils';
import { PrintPreviewModal } from '@/components/print/PrintPreviewModal';
import { PrintDocument } from '@/components/print/PrintDocument';
import { useCompany } from '@/hooks/useCompany';

type MovementType = 'in' | 'out' | 'adjustment';

const TYPE_LABELS: Record<string, string> = { in: 'وارد', out: 'صادر', adjustment: 'تسوية' };
const TYPE_COLORS: Record<string, string> = { in: 'badge-success', out: 'badge-danger', adjustment: 'badge-warning' };

export default function StockMovementsPage() {
  const company = useCompany();
  const queryClient = useQueryClient();
  const toast = useToast();

  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [showPrint, setShowPrint] = useState(false);
  const [showForm, setShowForm] = useState(false);

  const [productId, setProductId] = useState('');
  const [productSearch, setProductSearch] = useState('');
  const [movementType, setMovementType] = useState<MovementType>('in');
  const [quantity, setQuantity] = useState('');
  const [unitCost, setUnitCost] = useState('');
  const [warehouseId, setWarehouseId] = useState('');
  const [notes, setNotes] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['stock-movements', page, search],
    queryFn: () => getStockMovements({ page, pageSize: 10, search }),
  });

  const { data: products } = useQuery({
    queryKey: ['products-for-movement', productSearch],
    queryFn: () => getProducts({ page: 1, pageSize: 50, search: productSearch }),
    enabled: showForm,
  });

  const { data: warehouses } = useQuery({
    queryKey: ['warehouses-for-movement'],
    queryFn: () => getWarehouses({ page: 1, pageSize: 100 }),
    enabled: showForm,
  });

  const productList = (products?.items || []) as unknown as Record<string, unknown>[];
  const selectedProduct = useMemo(
    () => productList.find((p) => String(p.id) === productId),
    [productList, productId],
  );

  const currentStock = Number(selectedProduct?.currentStock ?? 0);
  const stockUnit = String(selectedProduct?.unit ?? '');
  const enteredQty = Number(quantity) || 0;
  const adjustmentDiff = movementType === 'adjustment' ? enteredQty - currentStock : 0;

  const resetForm = () => {
    setProductId('');
    setProductSearch('');
    setMovementType('in');
    setQuantity('');
    setUnitCost('');
    setWarehouseId('');
    setNotes('');
  };

  const createMutation = useMutation({
    mutationFn: createStockMovement,
    onSuccess: (res) => {
      queryClient.invalidateQueries({ queryKey: ['stock-movements'] });
      queryClient.invalidateQueries({ queryKey: ['products'] });
      queryClient.invalidateQueries({ queryKey: ['products-for-movement'] });
      toast.success(`تم تسجيل الحركة. الرصيد الحالي: ${res?.currentStock ?? '-'}`);
      setShowForm(false);
      resetForm();
    },
    onError: (e: any) => toast.error('تعذّر الحفظ: ' + (e?.response?.data?.detail || e.message)),
  });

  const onSelectProduct = (id: string) => {
    setProductId(id);
    const p = productList.find((x) => String(x.id) === id);
    if (p && movementType === 'in' && unitCost === '') {
      setUnitCost(String(p.purchasePrice ?? ''));
    }
  };

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!productId) { toast.error('اختر منتجاً'); return; }
    const qtyInvalid = quantity === '' || Number.isNaN(Number(quantity))
      || (movementType === 'adjustment' ? Number(quantity) < 0 : Number(quantity) <= 0);
    if (qtyInvalid) {
      toast.error(movementType === 'adjustment' ? 'أدخل الكمية الفعلية (صفر أو أكثر)' : 'أدخل كمية صحيحة أكبر من صفر');
      return;
    }
    if (movementType === 'adjustment' && enteredQty === currentStock) {
      toast.error('الكمية الفعلية تساوي الرصيد الحالي');
      return;
    }
    createMutation.mutate({
      productId: Number(productId),
      movementType,
      quantity: enteredQty,
      unitCost: unitCost === '' ? undefined : Number(unitCost),
      warehouseId: warehouseId ? Number(warehouseId) : undefined,
      notes: notes || undefined,
    });
  };

  const columns: Column<Record<string, unknown>>[] = [
    { key: 'productName', header: 'المنتج', render: (item) => <span className="font-medium">{String(item.productName ?? `#${item.productId}`)}</span> },
    { key: 'movementType', header: 'النوع', render: (item) => {
      const t = String(item.movementType);
      return <span className={TYPE_COLORS[t] || 'badge-info'}>{TYPE_LABELS[t] || t}</span>;
    }},
    { key: 'warehouseName', header: 'المخزن', render: (item) => String(item.warehouseName ?? '-') },
    { key: 'quantity', header: 'الكمية', render: (item) => String(item.quantity) },
    { key: 'unitCost', header: 'التكلفة', render: (item) => formatCurrency(Number(item.unitCost ?? 0)) },
    { key: 'reference', header: 'المرجع', render: (item) => String(item.referenceType ?? item.notes ?? '-') },
    { key: 'createdAt', header: 'التاريخ', render: (item) => formatDate(String(item.createdAt)) },
  ];

  const movements = (data?.items || []) as unknown as Record<string, unknown>[];

  return (
    <div className="space-y-6">
      <PageHeader
        title="حركة المخزون"
        subtitle="تسجيل الوارد والصادر وتسويات الجرد"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" /></svg>}
        actions={<div className="flex items-center gap-2">
          <button onClick={() => setShowForm(true)} className="btn-primary">+ حركة جديدة</button>
          <button onClick={() => setShowPrint(true)} className="btn-secondary flex items-center gap-2" disabled={movements.length === 0}>
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4H7v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
            </svg>
            طباعة / PDF
          </button>
        </div>}
      />
      <DataTable columns={columns} data={movements} loading={isLoading} totalItems={data?.total || 0} page={page} pageSize={10} onPageChange={setPage} searchValue={search} onSearchChange={setSearch} searchPlaceholder="بحث بالمنتج..." />

      <Modal isOpen={showForm} onClose={() => { setShowForm(false); resetForm(); }} title="حركة مخزون جديدة" size="md">
        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="label">نوع الحركة</label>
            <select
              value={movementType}
              onChange={(e) => setMovementType(e.target.value as MovementType)}
              className="input"
            >
              <option value="in">وارد — إضافة كمية إلى المخزون</option>
              <option value="out">صادر — خصم كمية من المخزون</option>
              <option value="adjustment">تسوية — مطابقة الرصيد مع الكمية الفعلية</option>
            </select>
          </div>

          <div>
            <label className="label">المنتج</label>
            <input
              value={productSearch}
              onChange={(e) => setProductSearch(e.target.value)}
              className="input mb-2"
              placeholder="ابحث بالاسم أو الكود..."
            />
            <select value={productId} onChange={(e) => onSelectProduct(e.target.value)} className="input">
              <option value="">اختر المنتج</option>
              {productList.map((p) => (
                <option key={String(p.id)} value={String(p.id)}>
                  {String(p.name)}{p.code ? ` — ${String(p.code)}` : ''} (المخزون: {String(p.currentStock ?? 0)})
                </option>
              ))}
            </select>
            {selectedProduct && (
              <p className="mt-1 text-xs text-gray-600 dark:text-zinc-400">
                الرصيد الحالي: <span className="font-bold">{currentStock}</span> {stockUnit}
              </p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="label">
                {movementType === 'adjustment' ? 'الكمية الفعلية بعد الجرد' : 'الكمية'}
              </label>
              <input
                type="number"
                min={movementType === 'adjustment' ? 0 : 1}
                step={1}
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                className="input"
                placeholder="0"
              />
              {movementType === 'adjustment' && quantity !== '' && (
                <p className={`mt-1 text-xs ${adjustmentDiff > 0 ? 'text-green-600' : adjustmentDiff < 0 ? 'text-red-600' : 'text-gray-500'}`}>
                  الفرق: {adjustmentDiff > 0 ? '+' : ''}{adjustmentDiff} {stockUnit}
                </p>
              )}
            </div>

            {movementType === 'in' && (
              <div>
                <label className="label">تكلفة الوحدة</label>
                <input
                  type="number"
                  min={0}
                  step="0.0001"
                  value={unitCost}
                  onChange={(e) => setUnitCost(e.target.value)}
                  className="input"
                  placeholder="تُؤخذ من سعر الشراء إن تُركت فارغة"
                />
              </div>
            )}

            <div>
              <label className="label">المخزن (اختياري)</label>
              <select value={warehouseId} onChange={(e) => setWarehouseId(e.target.value)} className="input">
                <option value="">بدون تحديد</option>
                {((warehouses?.items || []) as unknown as Record<string, unknown>[]).map((w) => (
                  <option key={String(w.id)} value={String(w.id)}>{String(w.name)}</option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="label">ملاحظات</label>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} className="input" placeholder="اختياري" />
          </div>

          {movementType === 'in' && (
            <p className="text-xs text-gray-500 dark:text-zinc-400">
              سيُنشأ قيد محاسبي تلقائي: مدين مخزون / دائن استحقاق بقيمة الكمية × التكلفة.
            </p>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={() => { setShowForm(false); resetForm(); }} className="btn-secondary">إلغاء</button>
            <button type="submit" disabled={createMutation.isPending} className="btn-primary">
              {createMutation.isPending ? 'جاري الحفظ...' : 'حفظ الحركة'}
            </button>
          </div>
        </form>
      </Modal>

      <PrintPreviewModal isOpen={showPrint} onClose={() => setShowPrint(false)} title="حركة المخزون" filename="حركة-المخزون">
        <PrintDocument company={company} title="تقرير حركة المخزون" meta={[
          { label: 'تاريخ التقرير', value: formatDateTime(new Date().toISOString()) },
          { label: 'عدد السجلات', value: String(data?.total || movements.length) },
        ]}>
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 text-gray-700">
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">#</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المنتج</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">النوع</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المخزن</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">الكمية</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">التكلفة</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">المرجع</th>
                <th className="px-3 py-2 text-right font-semibold border border-gray-300">التاريخ</th>
              </tr>
            </thead>
            <tbody>
              {movements.map((item, idx) => (
                <tr key={String(item.id) || idx}>
                  <td className="px-3 py-2 border border-gray-300">{idx + 1}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(item.productName ?? `#${item.productId}`)}</td>
                  <td className="px-3 py-2 border border-gray-300">{TYPE_LABELS[String(item.movementType)] || String(item.movementType)}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(item.warehouseName ?? '-')}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(item.quantity)}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatCurrency(Number(item.unitCost ?? 0))}</td>
                  <td className="px-3 py-2 border border-gray-300">{String(item.referenceType ?? item.notes ?? '-')}</td>
                  <td className="px-3 py-2 border border-gray-300">{formatDate(String(item.createdAt))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </PrintDocument>
      </PrintPreviewModal>
    </div>
  );
}
