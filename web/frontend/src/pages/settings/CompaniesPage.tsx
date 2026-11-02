import { useState, useEffect, useRef } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, put } from '@/api/client';
import type { Company } from '@/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';

export default function CompaniesPage() {
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const toast = useToast();
  const [formData, setFormData] = useState({
    name: '', nameAr: '', taxNumber: '', commercialRegister: '',
    phone: '', email: '', address: '', website: '', logo: '',
    defaultCurrency: '', fiscalYearStart: '', dateFormat: '',
  });

  const { data: company, isLoading } = useQuery({
    queryKey: ['company'],
    queryFn: async () => get<Company>('/settings/company'),
  });

  useEffect(() => {
    if (company) {
      setFormData({
        name: company.name || '', nameAr: company.nameAr || '',
        taxNumber: company.taxNumber || '', commercialRegister: company.commercialRegister || '',
        phone: company.phone || '', email: company.email || '', address: company.address || '',
        website: company.website || '', logo: company.logo || '',
        defaultCurrency: company.defaultCurrency || '', fiscalYearStart: company.fiscalYearStart || '',
        dateFormat: company.dateFormat || '',
      });
    }
  }, [company]);

  const updateMutation = useMutation({
    mutationFn: async (data: any) => put('/settings/company', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company'] });
      toast.success('تم حفظ التغييرات بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const handleSubmit = (e: React.FormEvent) => { e.preventDefault(); updateMutation.mutate(formData); };
  const handleChange = (field: string, value: string) => setFormData((prev) => ({ ...prev, [field]: value }));
  const handleLogoFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => handleChange('logo', String(reader.result || ''));
    reader.readAsDataURL(file);
    e.target.value = '';
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="إعدادات الشركة"
        subtitle="بيانات الشركة والمعلومات القانونية"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        }
      />
      <div className="card max-w-3xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">اسم الشركة</label><input value={formData.name} onChange={(e) => handleChange('name', e.target.value)} className="input" /></div>
            <div><label className="label">الاسم بالعربية</label><input value={formData.nameAr} onChange={(e) => handleChange('nameAr', e.target.value)} className="input" /></div>
            <div><label className="label">الرقم الضريبي</label><input value={formData.taxNumber} onChange={(e) => handleChange('taxNumber', e.target.value)} className="input" /></div>
            <div><label className="label">السجل التجاري</label><input value={formData.commercialRegister} onChange={(e) => handleChange('commercialRegister', e.target.value)} className="input" /></div>
            <div><label className="label">الهاتف</label><input value={formData.phone} onChange={(e) => handleChange('phone', e.target.value)} className="input" /></div>
            <div><label className="label">البريد الإلكتروني</label><input value={formData.email} onChange={(e) => handleChange('email', e.target.value)} className="input" type="email" /></div>
          </div>
          <div><label className="label">العنوان</label><textarea value={formData.address} onChange={(e) => handleChange('address', e.target.value)} className="input" rows={2} /></div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">الموقع الإلكتروني</label><input value={formData.website} onChange={(e) => handleChange('website', e.target.value)} className="input" /></div>
            <div><label className="label">رمز العملة الافتراضي</label><input value={formData.defaultCurrency} onChange={(e) => handleChange('defaultCurrency', e.target.value)} className="input" placeholder="SAR" /></div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div><label className="label">بداية السنة المالية</label><input value={formData.fiscalYearStart} onChange={(e) => handleChange('fiscalYearStart', e.target.value)} className="input" type="date" /></div>
            <div><label className="label">تنسيق التاريخ</label><input value={formData.dateFormat} onChange={(e) => handleChange('dateFormat', e.target.value)} className="input" placeholder="YYYY-MM-DD" /></div>
          </div>
          <div className="flex items-start gap-4">
            <div className="flex-1">
              <label className="label">الشعار</label>
              <input value={formData.logo.startsWith('data:') ? '' : formData.logo} onChange={(e) => handleChange('logo', e.target.value)} className="input" placeholder="رابط الشعار أو رفع صورة" />
              <p className="text-xs text-gray-400 mt-1">يمكنك إدخال رابط مباشر أو رفع صورة من الجهاز</p>
            </div>
            <div className="flex flex-col items-center gap-2 pt-6">
              {formData.logo ? (
                <img src={formData.logo} alt="الشعار" className="h-16 w-16 object-contain rounded-lg border border-gray-200 dark:border-zinc-700 bg-white" />
              ) : (
                <div className="h-16 w-16 rounded-lg bg-gray-100 dark:bg-zinc-800 flex items-center justify-center text-gray-400 text-sm">لا شعار</div>
              )}
              <div className="flex gap-2">
                <button type="button" onClick={() => fileInputRef.current?.click()} className="btn-secondary text-xs px-3 py-1.5">رفع صورة</button>
                {formData.logo && <button type="button" onClick={() => handleChange('logo', '')} className="text-red-500 text-xs hover:underline">إزالة</button>}
              </div>
              <input ref={fileInputRef} type="file" accept="image/*" className="hidden" onChange={handleLogoFile} />
            </div>
          </div>
          <div className="flex justify-end">
            <button type="submit" className="btn-primary" disabled={updateMutation.isPending}>
              {updateMutation.isPending ? 'جاري الحفظ...' : 'حفظ التغييرات'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
