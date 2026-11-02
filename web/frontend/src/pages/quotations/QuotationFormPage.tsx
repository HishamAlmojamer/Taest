import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createQuotation } from '@/api/quotations';
import { getCustomers } from '@/api/crm';
import { getProducts } from '@/api/inventory';
import { getTaxRates } from '@/api/taxes';
import { useAuthStore } from '@/stores/authStore';
import { FormActions } from '@/components/ui/FormActions';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';

const quotationSchema = z.object({
  customerId: z.string().min(1, 'العميل مطلوب'),
  quotationDate: z.string().min(1, 'التاريخ مطلوب'),
  validUntil: z.string().min(1, 'تاريخ الصلاحية مطلوب'),
  paymentTerms: z.string().optional(),
  notes: z.string().optional(),
  items: z.array(z.object({
    productId: z.string().min(1, 'المنتج مطلوب'),
    productName: z.string().optional(),
    quantity: z.number().min(1, 'الكمية يجب أن تكون 1 على الأقل'),
    unitPrice: z.number().min(0, 'السعر لا يمكن أن يكون سالباً'),
    discount: z.number().min(0).optional().default(0),
  })).min(1, 'يجب إضافة منتج واحد على الأقل'),
});

type QuotationForm = z.infer<typeof quotationSchema>;

export default function QuotationFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { branchId, user } = useAuthStore();
  const toast = useToast();

  const { data: customersData } = useQuery({
    queryKey: ['customers-select'],
    queryFn: () => getCustomers({ page: 1, pageSize: 1000 }),
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

  const mutation = useMutation({
    mutationFn: createQuotation,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['quotations'] });
      toast.success('تم إنشاء عرض السعر بنجاح');
      navigate('/quotations');
    },
    onError: (e: any) => toast.error('خطأ: ' + (e?.response?.data?.detail || e.message)),
  });

  const { register, handleSubmit, control, watch, formState: { errors } } = useForm<QuotationForm>({
    resolver: zodResolver(quotationSchema),
    defaultValues: {
      quotationDate: new Date().toISOString().split('T')[0],
      validUntil: new Date(Date.now() + 14 * 86400000).toISOString().split('T')[0],
      items: [],
    },
  });

  const { fields, append, remove, update } = useFieldArray({ control, name: 'items' });
  const watchedItems = watch('items');

  const addItem = () => append({ productId: '', productName: '', quantity: 1, unitPrice: 0, discount: 0 });

  const updateItemProduct = (index: number, productId: string) => {
    const product = productsData?.items?.find((p: any) => String(p.id) === String(productId));
    update(index, {
      ...watchedItems[index],
      productId,
      productName: product?.name || '',
      unitPrice: product?.sellingPrice || 0,
    });
  };

  const subtotal = (watchedItems || []).reduce(
    (sum, item) => sum + (item.quantity || 0) * (item.unitPrice || 0) - (item.discount || 0),
    0
  );
  const taxAmount = subtotal * (taxRatePercent / 100);
  const total = subtotal + taxAmount;

  const onSubmit = (data: QuotationForm) => {
    const totalDiscount = data.items.reduce((sum, item) => sum + (item.discount || 0), 0);
    mutation.mutate({
      customerId: data.customerId ? Number(data.customerId) : null,
      quotationDate: data.quotationDate,
      validUntil: data.validUntil,
      totalAmount: subtotal,
      taxAmount,
      discount: totalDiscount,
      finalAmount: total,
      currencyCode: 'SAR',
      paymentTerms: data.paymentTerms,
      notes: data.notes,
      companyId: Number(user?.companyId || 1),
      branchId: branchId ?? 1,
      items: data.items.map((item) => ({
        productId: Number(item.productId),
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        discount: item.discount || 0,
        taxPercent: taxRatePercent,
        taxAmount: (item.quantity * item.unitPrice - (item.discount || 0)) * (taxRatePercent / 100),
        totalPrice: item.quantity * item.unitPrice - (item.discount || 0),
      })),
    } as never);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="عرض سعر جديد"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21l-7-5-7 5V5a2 2 0 012-2h10a2 2 0 012 2v16z" /></svg>}
        actions={<button onClick={() => navigate('/quotations')} className="btn-secondary">رجوع</button>}
      />

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="label">العميل</label>
              <select {...register('customerId')} className="input">
                <option value="">اختر العميل</option>
                {customersData?.items?.map((c: any) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
              {errors.customerId && <p className="text-xs text-red-600 mt-1">{errors.customerId.message}</p>}
            </div>
            <div>
              <label className="label">التاريخ</label>
              <input {...register('quotationDate')} type="date" className="input" />
              {errors.quotationDate && <p className="text-xs text-red-600 mt-1">{errors.quotationDate.message}</p>}
            </div>
            <div>
              <label className="label">صالح حتى</label>
              <input {...register('validUntil')} type="date" className="input" />
              {errors.validUntil && <p className="text-xs text-red-600 mt-1">{errors.validUntil.message}</p>}
            </div>
            <div>
              <label className="label">شروط الدفع</label>
              <input {...register('paymentTerms')} className="input" placeholder="مثال: 30 يوماً" />
            </div>
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

          {errors.items && <p className="text-sm text-red-600 mb-3">{errors.items.message}</p>}

          <table className="w-full">
            <thead>
              <tr className="table-header">
                <th className="px-3 py-2 text-right text-xs">المنتج</th>
                <th className="px-3 py-2 text-right text-xs">الكمية</th>
                <th className="px-3 py-2 text-right text-xs">السعر</th>
                <th className="px-3 py-2 text-right text-xs">الخصم</th>
                <th className="px-3 py-2 text-right text-xs">الإجمالي</th>
                <th className="px-3 py-2 text-center text-xs">حذف</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((field, idx) => (
                <tr key={field.id} className="border-b border-gray-100 dark:border-zinc-800">
                  <td className="px-3 py-2">
                    <select
                      {...register(`items.${idx}.productId`)}
                      onChange={(e) => updateItemProduct(idx, e.target.value)}
                      className="input text-sm"
                    >
                      <option value="">اختر المنتج</option>
                      {productsData?.items?.map((p: any) => (
                        <option key={p.id} value={p.id}>{p.name}</option>
                      ))}
                    </select>
                    {errors.items?.[idx]?.productId && (
                      <p className="text-xs text-red-600 mt-1">{errors.items?.[idx]?.productId?.message}</p>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" {...register(`items.${idx}.quantity`, { valueAsNumber: true })} className="input text-sm w-24" min={1} />
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" {...register(`items.${idx}.unitPrice`, { valueAsNumber: true })} className="input text-sm w-28" min={0} />
                  </td>
                  <td className="px-3 py-2">
                    <input type="number" {...register(`items.${idx}.discount`, { valueAsNumber: true })} className="input text-sm w-24" min={0} />
                  </td>
                  <td className="px-3 py-2 text-sm font-medium">
                    {((watchedItems?.[idx]?.quantity || 0) * (watchedItems?.[idx]?.unitPrice || 0) - (watchedItems?.[idx]?.discount || 0)).toFixed(2)}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button type="button" onClick={() => remove(idx)} className="text-red-500 hover:text-red-700">
                      <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="flex justify-end mt-6">
            <div className="w-72 space-y-2">
              <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">المجموع الفرعي</span><span>{subtotal.toFixed(2)}</span></div>
              <div className="flex justify-between text-sm"><span className="text-gray-500 dark:text-zinc-400">الضريبة ({taxRatePercent}%)</span><span>{taxAmount.toFixed(2)}</span></div>
              <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-2">
                <span>الإجمالي</span><span className="text-primary-600">{total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        <FormActions onSave={handleSubmit(onSubmit)} onCancel={() => navigate('/quotations')} isSubmitting={mutation.isPending} saveLabel="حفظ العرض" />
      </form>
    </div>
  );
}
