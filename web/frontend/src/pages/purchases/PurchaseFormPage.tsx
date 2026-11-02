import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createPurchase } from '@/api/purchases';
import { getSuppliers } from '@/api/crm';
import { getProducts } from '@/api/inventory';
import { getTaxRates } from '@/api/taxes';
import { useAuthStore } from '@/stores/authStore';
import { FormActions } from '@/components/ui/FormActions';
import { FormSummary } from '@/components/ui/FormSummary';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const purchaseSchema = z.object({
  supplierId: z.string().min(1, 'المورد مطلوب'),
  date: z.string().min(1, 'التاريخ مطلوب'),
  dueDate: z.string().min(1, 'تاريخ الاستحقاق مطلوب'),
  notes: z.string().optional(),
});

type PurchaseForm = z.infer<typeof purchaseSchema>;

export default function PurchaseFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { branchId, fiscalYearId, user } = useAuthStore();
  const [items, setItems] = useState<{ productId: string; quantity: number; unitCost: number; discount: number }[]>([]);
  const toast = useToast();

  const { data: suppliersData } = useQuery({
    queryKey: ['suppliers-select'],
    queryFn: () => getSuppliers({ page: 1, pageSize: 1000 }),
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-select'],
    queryFn: () => getProducts({ page: 1, pageSize: 1000 }),
  });

  const { data: taxRates } = useQuery({
    queryKey: ['tax-rates'],
    queryFn: () => getTaxRates(),
  });

  const activeTax = (taxRates || []).find(
    (t: any) => t.isActive && t.rate > 0 && (!t.appliesTo || t.appliesTo === 'PURCHASES' || t.appliesTo === 'BOTH')
  );
  const taxRatePercent = activeTax ? Number(activeTax.rate) : 15;

  const mutation = useMutation({
    mutationFn: createPurchase,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['purchases'] });
      toast.success('تم إنشاء أمر الشراء بنجاح');
      navigate('/purchases');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const { register, handleSubmit, formState: { errors } } = useForm<PurchaseForm>({
    resolver: zodResolver(purchaseSchema),
    defaultValues: { date: new Date().toISOString().split('T')[0], dueDate: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0] },
  });

  const addItem = () => setItems([...items, { productId: '', quantity: 1, unitCost: 0, discount: 0 }]);
  const removeItem = (i: number) => setItems(items.filter((_, idx) => idx !== i));
  const updateItem = (i: number, field: string, val: string | number) => {
    const u = [...items];
    (u[i] as Record<string, unknown>)[field] = val;
    if (field === 'productId') {
      const p = productsData?.items?.find((pr: any) => pr.id === val);
      if (p) u[i].unitCost = p.purchasePrice;
    }
    setItems(u);
  };

  const subtotal = items.reduce((s, i) => s + i.quantity * i.unitCost, 0);
  const taxAmount = subtotal * (taxRatePercent / 100);
  const totalDiscount = items.reduce((s, i) => s + (i.discount || 0), 0);
  const total = subtotal + taxAmount - totalDiscount;

  const buildPayload = (supplierId: string | undefined, dueDate: string | undefined, notes: string | undefined) => ({
    supplierId: supplierId ? Number(supplierId) : null,
    totalAmount: subtotal,
    discount: totalDiscount,
    finalAmount: total,
    paymentStatus: 'pending',
    companyId: Number(user?.companyId || 1),
    branchId: branchId ?? 1,
    fiscalPeriodId: fiscalYearId,
    dueDate: dueDate || undefined,
    taxAmount,
    taxId: activeTax ? activeTax.id : undefined,
    notes,
    items: items.map((item) => ({
      productId: Number(item.productId),
      quantity: item.quantity,
      unitPrice: item.unitCost,
      totalPrice: item.quantity * item.unitCost,
    })),
  } as never);

  return (
    <div className="space-y-6">
      <PageHeader
        title="أمر شراء جديد"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>}
        actions={<button onClick={() => navigate('/purchases')} className="btn-secondary">رجوع</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(buildPayload(d.supplierId, d.dueDate, d.notes)))} className="space-y-6">
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">المورد</label>
              <select {...register('supplierId')} className="input">
                <option value="">اختر المورد</option>
                {suppliersData?.items?.map((s: any) => <option key={s.id} value={s.id}>{s.name}</option>)}
              </select>
              {errors.supplierId && <p className="text-xs text-red-600 mt-1">{errors.supplierId.message}</p>}
            </div>
            <div><label className="label">التاريخ</label><input {...register('date')} type="date" className="input" /></div>
            <div><label className="label">الاستحقاق</label><input {...register('dueDate')} type="date" className="input" /></div>
          </div>
          <div className="mt-4">
            <label className="label">ملاحظات</label>
            <textarea {...register('notes')} className="input" rows={2} />
          </div>
        </div>
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">الأصناف</h3>
            <button type="button" onClick={addItem} className="btn-primary text-sm">+ إضافة صنف</button>
          </div>
          <table className="w-full">
            <thead><tr className="table-header">
              <th className="px-3 py-2 text-right text-xs">المنتج</th>
              <th className="px-3 py-2 text-right text-xs">الكمية</th>
              <th className="px-3 py-2 text-right text-xs">التكلفة</th>
              <th className="px-3 py-2 text-right text-xs">الخصم</th>
              <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
              <th className="px-3 py-2 text-center text-xs">حذف</th>
            </tr></thead>
            <tbody>
              {items.map((item, idx) => (
                <tr key={idx} className="border-b border-gray-100 dark:border-zinc-800">
                  <td className="px-3 py-2">
                    <select value={item.productId} onChange={(e) => updateItem(idx, 'productId', e.target.value)} className="input text-sm">
                      <option value="">اختر</option>
                      {productsData?.items?.map((p: any) => <option key={p.id} value={p.id}>{p.name}</option>)}
                    </select>
                  </td>
                  <td className="px-3 py-2"><input type="number" value={item.quantity} onChange={(e) => updateItem(idx, 'quantity', Number(e.target.value))} className="input text-sm w-24" min={1} /></td>
                  <td className="px-3 py-2"><input type="number" value={item.unitCost} onChange={(e) => updateItem(idx, 'unitCost', Number(e.target.value))} className="input text-sm w-28" min={0} /></td>
                  <td className="px-3 py-2"><input type="number" value={item.discount} onChange={(e) => updateItem(idx, 'discount', Number(e.target.value))} className="input text-sm w-24" min={0} /></td>
                  <td className="px-3 py-2 text-sm font-medium">{(item.quantity * item.unitCost - item.discount).toFixed(2)}</td>
                  <td className="px-3 py-2 text-center"><button type="button" onClick={() => removeItem(idx)} className="text-red-500 hover:text-red-700">حذف</button></td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="flex justify-end mt-6">
            <div className="w-72 space-y-2">
              <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع</span><span>{subtotal.toFixed(2)}</span></div>
              <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة ({taxRatePercent}%)</span><span>{taxAmount.toFixed(2)}</span></div>
              <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-2"><span>الإجمالي</span><span className="text-primary-600">{total.toFixed(2)}</span></div>
            </div>
          </div>
        </div>
        <FormActions onSave={handleSubmit((d) => mutation.mutate(buildPayload(d.supplierId, d.dueDate, d.notes)))} onCancel={() => navigate('/purchases')} isSubmitting={mutation.isPending} />
      </form>
    </div>
  );
}
