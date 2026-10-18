import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { createProduct } from '@/api/inventory';
import { getCategories } from '@/api/inventory';

const productSchema = z.object({
  sku: z.string().min(1, 'الكود مطلوب'),
  name: z.string().min(1, 'الاسم مطلوب'),
  nameEn: z.string().optional(),
  description: z.string().optional(),
  categoryId: z.string().optional(),
  unit: z.string().min(1, 'الوحدة مطلوبة'),
  costPrice: z.number().min(0),
  sellingPrice: z.number().min(0),
  taxRate: z.number().min(0).max(100),
  minStock: z.number().min(0),
  maxStock: z.number().min(0),
  barcode: z.string().optional(),
  brand: z.string().optional(),
});

type ProductForm = z.infer<typeof productSchema>;

export default function ProductFormPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { data: categories } = useQuery({ queryKey: ['categories'], queryFn: () => getCategories({ page: 1, pageSize: 1000 }) });

  const mutation = useMutation({
    mutationFn: (data: ProductForm) => createProduct({
      code: data.sku,
      name: data.name,
      nameEn: data.nameEn,
      description: data.description,
      categoryId: data.categoryId ? Number(data.categoryId) : undefined,
      unit: data.unit,
      purchasePrice: data.costPrice,
      sellingPrice: data.sellingPrice,
      currentStock: 0,
      minStock: data.minStock,
      maxStock: data.maxStock,
      taxPercent: data.taxRate,
      barcode: data.barcode,
      brand: data.brand,
      companyId: 1,
    } as never),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['products'] }); navigate('/inventory/products'); },
  });

  const { register, handleSubmit, formState: { errors } } = useForm<ProductForm>({
    resolver: zodResolver(productSchema),
    defaultValues: { unit: 'pcs', taxRate: 15, costPrice: 0, sellingPrice: 0, minStock: 0, maxStock: 0 },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">منتج جديد</h1>
        <button onClick={() => navigate('/inventory/products')} className="btn-secondary">رجوع</button>
      </div>
      <form onSubmit={handleSubmit((d) => mutation.mutate(d))} className="card space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div><label className="label">كود المنتج</label><input {...register('sku')} className="input" />{errors.sku && <p className="text-xs text-red-600">{errors.sku.message}</p>}</div>
          <div><label className="label">الاسم بالإنجليزية</label><input {...register('name')} className="input" />{errors.name && <p className="text-xs text-red-600">{errors.name.message}</p>}</div>
          <div><label className="label">الاسم بالعربية</label><input {...register('nameEn')} className="input" /></div>
          <div>
            <label className="label">التصنيف</label>
            <select {...register('categoryId')} className="input">
              <option value="">اختر التصنيف</option>
              {categories?.items?.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </div>
          <div><label className="label">الوحدة</label><input {...register('unit')} className="input" /></div>
          <div><label className="label">الباركود</label><input {...register('barcode')} className="input" /></div>
          <div><label className="label">العلامة التجارية</label><input {...register('brand')} className="input" /></div>
          <div><label className="label">تكلفة الشراء</label><input {...register('costPrice', { valueAsNumber: true })} type="number" className="input" /></div>
          <div><label className="label">سعر البيع</label><input {...register('sellingPrice', { valueAsNumber: true })} type="number" className="input" /></div>
          <div><label className="label">نسبة الضريبة %</label><input {...register('taxRate', { valueAsNumber: true })} type="number" className="input" /></div>
          <div><label className="label">الحد الأدنى</label><input {...register('minStock', { valueAsNumber: true })} type="number" className="input" /></div>
          <div><label className="label">الحد الأقصى</label><input {...register('maxStock', { valueAsNumber: true })} type="number" className="input" /></div>
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
