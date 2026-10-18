import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { createSale } from '@/api/sales';
import { getCustomers } from '@/api/crm';
import { getProducts } from '@/api/inventory';
import { FormActions } from '@/components/ui/FormActions';

const saleSchema = z.object({
  customerId: z.string().min(1, 'العميل مطلوب'),
  date: z.string().min(1, 'التاريخ مطلوب'),
  dueDate: z.string().min(1, 'تاريخ الاستحقاق مطلوب'),
  notes: z.string().optional(),
  items: z.array(z.object({
    productId: z.string().min(1, 'المنتج مطلوب'),
    productName: z.string().optional(),
    quantity: z.number().min(1, 'الكمية يجب أن تكون 1 على الأقل'),
    unitPrice: z.number().min(0, 'السعر لا يمكن أن يكون سالباً'),
    discount: z.number().min(0).optional().default(0),
  })).min(1, 'يجب إضافة منتج واحد على الأقل'),
});

type SaleForm = z.infer<typeof saleSchema>;

export default function SaleFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: customersData } = useQuery({
    queryKey: ['customers-select'],
    queryFn: () => getCustomers({ page: 1, pageSize: 1000 }),
  });

  const { data: productsData } = useQuery({
    queryKey: ['products-select'],
    queryFn: () => getProducts({ page: 1, pageSize: 1000 }),
  });

  const mutation = useMutation({
    mutationFn: createSale,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sales'] });
      navigate('/sales');
    },
  });

  const { register, handleSubmit, control, watch, formState: { errors } } = useForm<SaleForm>({
    resolver: zodResolver(saleSchema),
    defaultValues: {
      date: new Date().toISOString().split('T')[0],
      dueDate: new Date(Date.now() + 30 * 86400000).toISOString().split('T')[0],
      items: [],
    },
  });

  const { fields, append, remove, update } = useFieldArray({
    control,
    name: 'items',
  });

  const watchedItems = watch('items');

  const addItem = () => {
    append({ productId: '', productName: '', quantity: 1, unitPrice: 0, discount: 0 });
  };

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
  const taxAmount = subtotal * 0.15;
  const total = subtotal + taxAmount;

  const onSubmit = (data: SaleForm) => {
    const totalAmount = subtotal;
    const finalAmount = total;
    mutation.mutate({
      customerId: data.customerId ? Number(data.customerId) : null,
      totalAmount,
      discount: data.items.reduce((sum, item) => sum + (item.discount || 0), 0),
      finalAmount,
      paymentMethod: 'cash',
      paymentStatus: 'paid',
      companyId: 1,
      branchId: 1,
      invoiceNumber: `INV-${Date.now()}`,
      taxAmount,
      notes: data.notes,
      items: data.items.map((item) => ({
        productId: Number(item.productId),
        quantity: item.quantity,
        unitPrice: item.unitPrice,
        totalPrice: item.quantity * item.unitPrice,
      })),
    } as never);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">فاتورة مبيعات جديدة</h1>
        <button onClick={() => navigate('/sales')} className="btn-secondary">رجوع</button>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="card">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
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
              <input {...register('date')} type="date" className="input" />
              {errors.date && <p className="text-xs text-red-600 mt-1">{errors.date.message}</p>}
            </div>
            <div>
              <label className="label">تاريخ الاستحقاق</label>
              <input {...register('dueDate')} type="date" className="input" />
              {errors.dueDate && <p className="text-xs text-red-600 mt-1">{errors.dueDate.message}</p>}
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
                    <input
                      type="number"
                      {...register(`items.${idx}.quantity`, { valueAsNumber: true })}
                      className="input text-sm w-24"
                      min={1}
                    />
                    {errors.items?.[idx]?.quantity && (
                      <p className="text-xs text-red-600 mt-1">{errors.items?.[idx]?.quantity?.message}</p>
                    )}
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="number"
                      {...register(`items.${idx}.unitPrice`, { valueAsNumber: true })}
                      className="input text-sm w-28"
                      min={0}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <input
                      type="number"
                      {...register(`items.${idx}.discount`, { valueAsNumber: true })}
                      className="input text-sm w-24"
                      min={0}
                    />
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
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-zinc-400">المجموع الفرعي</span>
                <span>{subtotal.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500 dark:text-zinc-400">الضريبة (15%)</span>
                <span>{taxAmount.toFixed(2)}</span>
              </div>
              <div className="flex justify-between text-base font-bold border-t border-gray-200 dark:border-zinc-700 pt-2">
                <span>الإجمالي</span>
                <span className="text-primary-600">{total.toFixed(2)}</span>
              </div>
            </div>
          </div>
        </div>

        <FormActions onSave={handleSubmit(onSubmit)} onCancel={() => navigate('/sales')} isSubmitting={mutation.isPending} saveLabel="حفظ الفاتورة" />
      </form>
    </div>
  );
}
