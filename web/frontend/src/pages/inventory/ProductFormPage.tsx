import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { PageHeader } from '@/components/ui/PageHeader';
import { useToast } from '@/components/ui/Toast';
import { createProduct } from '@/api/inventory';
import { getCategories } from '@/api/inventory';
import { getCurrencies } from '@/api/currencies';

const nonNegative = (label: string) =>
  z.number({ invalid_type_error: `${label}: أدخل رقماً صحيحاً` }).min(0, `${label}: لا يمكن أن يكون سالباً`);

const productSchema = z.object({
  sku: z.string().trim().min(1, 'كود المنتج مطلوب'),
  name: z.string().trim().min(1, 'اسم المنتج مطلوب'),
  nameEn: z.string().optional(),
  description: z.string().optional(),
  categoryId: z.string().optional(),
  unit: z.string().trim().min(1, 'الوحدة مطلوبة'),
  costPrice: nonNegative('تكلفة الشراء'),
  sellingPrice: nonNegative('سعر البيع'),
  taxRate: nonNegative('نسبة الضريبة').max(100, 'نسبة الضريبة: الحد الأقصى 100'),
  minStock: nonNegative('الحد الأدنى'),
  maxStock: nonNegative('الحد الأقصى'),
  barcode: z.string().optional(),
  brand: z.string().optional(),
  currencyId: z.string().optional(),
});

type ProductForm = z.infer<typeof productSchema>;

function errorText(e: any): string {
  const detail = e?.response?.data?.detail;
  if (Array.isArray(detail)) return detail.map((d: any) => d?.msg).filter(Boolean).join('، ');
  return detail || e?.message || 'خطأ غير معروف';
}

export default function ProductFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const toast = useToast();
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: () => getCategories({ page: 1, pageSize: 1000 }) });
  const { data: currenciesData } = useQuery({ queryKey: ['currencies'], queryFn: getCurrencies });
  const currencies = Array.isArray(currenciesData) ? currenciesData : (currenciesData as any)?.items || [];

  const mutation = useMutation({
    mutationFn: (data: ProductForm) => createProduct({
      code: data.sku.trim(),
      name: data.name.trim(),
      nameEn: data.nameEn?.trim() || undefined,
      description: data.description?.trim() || undefined,
      categoryId: data.categoryId ? Number(data.categoryId) : undefined,
      unit: data.unit.trim(),
      purchasePrice: data.costPrice,
      sellingPrice: data.sellingPrice,
      currentStock: 0,
      minStock: data.minStock,
      maxStock: data.maxStock,
      taxPercent: data.taxRate,
      barcode: data.barcode?.trim() || undefined,
      brand: data.brand?.trim() || undefined,
      currencyId: data.currencyId ? Number(data.currencyId) : undefined,
      companyId: 1,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['products'] });
      toast.success('تم حفظ المنتج بنجاح');
      navigate('/inventory/products');
    },
    onError: (e: any) => toast.error('تعذّر حفظ المنتج: ' + errorText(e)),
  });

  const { register, handleSubmit, formState: { errors } } = useForm<ProductForm>({
    resolver: zodResolver(productSchema),
    defaultValues: { unit: 'pcs', taxRate: 15, costPrice: 0, sellingPrice: 0, minStock: 0, maxStock: 0 },
  });

  const onInvalid = (formErrors: Record<string, any>) => {
    const first = Object.values(formErrors)[0];
    toast.error('تحقق من البيانات: ' + (first?.message || 'هناك حقول غير صالحة'));
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="منتج جديد"
        icon={<svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>}
        actions={<button onClick={() => navigate('/inventory/products')} className="btn-secondary">رجوع</button>}
      />
      <form onSubmit={handleSubmit((d) => mutation.mutate(d), onInvalid)} className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><label className="label">كود المنتج *</label><input {...register('sku')} className="input" />{errors.sku && <p className="text-xs text-red-600">{errors.sku.message}</p>}</div>
          <div><label className="label">اسم المنتج *</label><input {...register('name')} className="input" />{errors.name && <p className="text-xs text-red-600">{errors.name.message}</p>}</div>
          <div><label className="label">الاسم بالإنجليزية (اختياري)</label><input {...register('nameEn')} className="input" /></div>
          <div>
            <label className="label">التصنيف</label>
            <select {...register('categoryId')} className="input">
              <option value="">اختر التصنيف</option>
              {categories?.items?.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div><label className="label">الوحدة *</label><input {...register('unit')} className="input" />{errors.unit && <p className="text-xs text-red-600">{errors.unit.message}</p>}</div>
          <div>
            <label className="label">عملة المنتج</label>
            <select {...register('currencyId')} className="input">
              <option value="">حسب العملة الافتراضية</option>
              {currencies.map((cur: any) => (
                <option key={cur.id} value={cur.id}>
                  {cur.code} - {cur.nameAr || cur.name}
                </option>
              ))}
            </select>
          </div>
          <div><label className="label">الباركود (اختياري)</label><input {...register('barcode')} className="input" /></div>
          <div><label className="label">العلامة التجارية</label><input {...register('brand')} className="input" /></div>
          <div><label className="label">تكلفة الشراء</label><input {...register('costPrice', { valueAsNumber: true })} type="number" className="input" />{errors.costPrice && <p className="text-xs text-red-600">{errors.costPrice.message}</p>}</div>
          <div><label className="label">سعر البيع</label><input {...register('sellingPrice', { valueAsNumber: true })} type="number" className="input" />{errors.sellingPrice && <p className="text-xs text-red-600">{errors.sellingPrice.message}</p>}</div>
          <div><label className="label">نسبة الضريبة %</label><input {...register('taxRate', { valueAsNumber: true })} type="number" className="input" />{errors.taxRate && <p className="text-xs text-red-600">{errors.taxRate.message}</p>}</div>
          <div><label className="label">الحد الأدنى</label><input {...register('minStock', { valueAsNumber: true })} type="number" className="input" />{errors.minStock && <p className="text-xs text-red-600">{errors.minStock.message}</p>}</div>
          <div><label className="label">الحد الأقصى</label><input {...register('maxStock', { valueAsNumber: true })} type="number" className="input" />{errors.maxStock && <p className="text-xs text-red-600">{errors.maxStock.message}</p>}</div>
        </div>
        <div><label className="label">الوصف</label><textarea {...register('description')} className="input" rows={3} /></div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={() => navigate('/inventory/products')} className="btn-secondary">إلغاء</button>
          <button type="submit" disabled={mutation.isPending} className="btn-primary">{mutation.isPending ? 'جاري الحفظ...' : 'حفظ'}</button>
        </div>
      </form>
    </div>
  );
}
