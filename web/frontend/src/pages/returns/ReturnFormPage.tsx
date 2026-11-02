import { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getSales, getSale } from '@/api/sales';
import { getPurchases, getPurchase } from '@/api/purchases';
import { createSalesReturn, createPurchaseReturn } from '@/api/returns';
import { getProducts } from '@/api/inventory';
import { getTaxRates } from '@/api/taxes';
import { useAuthStore } from '@/stores/authStore';
import { FormActions } from '@/components/ui/FormActions';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import type { Sale, Purchase, PaginatedResponse } from '@/types';

interface Props {
  type: 'sales' | 'purchase';
}

export default function ReturnFormPage({ type }: Props) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { branchId, user } = useAuthStore();
  const isSales = type === 'sales';
  const basePath = isSales ? '/returns/sales' : '/returns/purchases';
  const toast = useToast();

  const [sourceId, setSourceId] = useState('');
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [refundMethod, setRefundMethod] = useState('credit');
  const [isRestocked, setIsRestocked] = useState(true);
  const [reason, setReason] = useState('');
  const [notes, setNotes] = useState('');

  const { data: sourcesData } = useQuery<PaginatedResponse<Sale> | PaginatedResponse<Purchase>>({
    queryKey: [isSales ? 'sales-select' : 'purchases-select'],
    queryFn: () => (isSales ? getSales({ page: 1, pageSize: 1000 }) : getPurchases({ page: 1, pageSize: 1000 })),
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-select'],
    queryFn: () => getProducts({ page: 1, pageSize: 1000 }),
  });

  const { data: taxRates } = useQuery({
    queryKey: ['tax-rates'],
    queryFn: () => getTaxRates(),
  });

  const activeTax = (taxRates || []).find((t: any) => t.isActive && t.rate > 0);
  const taxRatePercent = activeTax ? Number(activeTax.rate) : 15;

  const { data: source } = useQuery<Sale | Purchase>({
    queryKey: [isSales ? 'sale' : 'purchase', sourceId],
    queryFn: () => (isSales ? getSale(sourceId) : getPurchase(sourceId)),
    enabled: !!sourceId,
  });

  const productName = (productId: string) => {
    const p = (productsData?.items || []).find((x: any) => String(x.id) === String(productId));
    return p?.name || '';
  };

  const items = useMemo(() => {
    if (!source?.items) return [];
    return source.items.map((it: any) => ({
      productId: it.productId ?? it.product_id,
      productName: it.productName || productName(it.productId ?? it.product_id),
      quantity: it.quantity || 0,
      unitPrice: it.unitPrice ?? it.unit_price ?? it.unitCost ?? it.unit_cost ?? 0,
    }));
  }, [source, productsData]);

  const rows = items.map((it) => {
    const qty = quantities[String(it.productId)] ?? it.quantity;
    return { ...it, qty, lineTotal: qty * it.unitPrice };
  });
  const totalAmount = rows.reduce((s, r) => s + r.lineTotal, 0);
  const taxAmount = totalAmount * (taxRatePercent / 100);
  const finalAmount = totalAmount + taxAmount;

  const mutation = useMutation({
    mutationFn: (data: any) => (isSales ? createSalesReturn(data) : createPurchaseReturn(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [isSales ? 'sales-returns' : 'purchase-returns'] });
      toast.success('تم إنشاء المرتجع بنجاح');
      navigate(basePath);
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const onSubmit = () => {
    if (!sourceId) return;
    const validRows = rows.filter((r) => r.qty > 0);
    const payload: Record<string, unknown> = {
      totalAmount,
      taxAmount,
      finalAmount,
      reason,
      refundMethod,
      isRestocked,
      notes,
      companyId: Number(user?.companyId || 1),
      branchId: branchId ?? 1,
      items: validRows.map((r) =>
        isSales
          ? {
              productId: Number(r.productId),
              quantity: r.qty,
              unitPrice: r.unitPrice,
              totalPrice: r.lineTotal,
              taxAmount: r.lineTotal * (taxRatePercent / 100),
            }
          : {
              productId: Number(r.productId),
              quantity: r.qty,
              unitCost: r.unitPrice,
              totalCost: r.lineTotal,
              taxAmount: r.lineTotal * (taxRatePercent / 100),
            }
      ),
    };
    if (isSales) {
      const sale = source as Sale | undefined;
      payload.saleId = Number(sourceId);
      payload.saleInvoiceNumber = sale?.invoiceNumber || null;
      payload.customerId = Number(sale?.customerId || null);
    } else {
      const purchase = source as Purchase | undefined;
      payload.purchaseId = Number(sourceId);
      payload.purchaseOrderNumber = purchase?.orderNumber || null;
      payload.supplierId = Number(purchase?.supplierId || null);
    }
    mutation.mutate(payload as never);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title={isSales ? 'مرتجع مبيعات جديد' : 'مرتجع مشتريات جديد'}
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 15v-1a4 4 0 00-4-4H8m0 0l3 3m-3-3l3-3m9 14V5a2 2 0 00-2-2H6a2 2 0 00-2 2v16l4-2 4 2 4-2 4 2z" /></svg>}
        actions={<button onClick={() => navigate(basePath)} className="btn-secondary">رجوع</button>}
      />

      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">{isSales ? 'الفاتورة الأصلية' : 'أمر الشراء الأصلي'}</label>
            <select
              value={sourceId}
              onChange={(e) => {
                setSourceId(e.target.value);
                setQuantities({});
              }}
              className="input"
            >
              <option value="">اختر المستند</option>
              {(sourcesData?.items || []).map((s: any) => (
                <option key={s.id} value={s.id}>
                  {s.invoiceNumber || s.orderNumber || `#${s.id}`} — {s.customerName || s.supplierName || '-'}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">طريقة رد المبلغ</label>
            <select value={refundMethod} onChange={(e) => setRefundMethod(e.target.value)} className="input">
              <option value="credit">رصيد دائن</option>
              <option value="cash">نقدي</option>
              <option value="bank">تحويل بنكي</option>
            </select>
          </div>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <input id="restock" type="checkbox" checked={isRestocked} onChange={(e) => setIsRestocked(e.target.checked)} className="h-4 w-4" />
          <label htmlFor="restock" className="text-sm">إعادة إضافة المنتجات إلى المخزون</label>
        </div>
      </div>

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">الأصناف المرتجعة</h3>
        </div>
        <table className="w-full">
          <thead>
            <tr className="table-header">
              <th className="px-3 py-2 text-right text-xs">المنتج</th>
              <th className="px-3 py-2 text-right text-xs">الكمية المرتجعة</th>
              <th className="px-3 py-2 text-right text-xs">السعر</th>
              <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={String(r.productId) + idx} className="border-b border-gray-100 dark:border-zinc-800">
                <td className="px-3 py-2 text-sm">{r.productName || r.productId || '-'}</td>
                <td className="px-3 py-2">
                  <input
                    type="number"
                    min={0}
                    max={r.quantity}
                    value={r.qty}
                    onChange={(e) => setQuantities((prev) => ({ ...prev, [String(r.productId)]: Number(e.target.value) }))}
                    className="input text-sm w-24"
                  />
                </td>
                <td className="px-3 py-2 text-sm">{r.unitPrice.toFixed(2)}</td>
                <td className="px-3 py-2 text-sm font-medium">{r.lineTotal.toFixed(2)}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr><td colSpan={4} className="px-3 py-8 text-center text-sm text-gray-400">اختر مستنداً لعرض أصنافه</td></tr>
            )}
          </tbody>
        </table>
        <div className="flex justify-end mt-6">
          <div className="w-72 space-y-2">
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع</span><span>{totalAmount.toFixed(2)}</span></div>
            <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة ({taxRatePercent}%)</span><span>{taxAmount.toFixed(2)}</span></div>
            <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-2">
              <span>الإجمالي</span><span className="text-primary-600">{finalAmount.toFixed(2)}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">سبب الإرجاع</label>
            <input value={reason} onChange={(e) => setReason(e.target.value)} className="input" placeholder="سبب المرتجع..." />
          </div>
          <div>
            <label className="label">ملاحظات</label>
            <input value={notes} onChange={(e) => setNotes(e.target.value)} className="input" />
          </div>
        </div>
      </div>

      <FormActions
        onSave={onSubmit}
        onCancel={() => navigate(basePath)}
        isSubmitting={mutation.isPending}
        saveLabel={isSales ? 'حفظ مرتجع المبيعات' : 'حفظ مرتجع المشتريات'}
      />
    </div>
  );
}
