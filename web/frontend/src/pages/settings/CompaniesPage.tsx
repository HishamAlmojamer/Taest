import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, put } from '@/api/client';
import type { Company } from '@/types';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';

export default function CompaniesPage() {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState({
    name: '',
    nameAr: '',
    taxNumber: '',
    commercialRegister: '',
    phone: '',
    email: '',
    address: '',
    website: '',
  });

  const { data: company, isLoading } = useQuery({
    queryKey: ['company'],
    queryFn: async () => {
      const res = await get<Company>('/settings/company');
      return res;
    },
  });

  useEffect(() => {
    if (company) {
      setFormData({
        name: company.name || '',
        nameAr: company.nameAr || '',
        taxNumber: company.taxNumber || '',
        commercialRegister: company.commercialRegister || '',
        phone: company.phone || '',
        email: company.email || '',
        address: company.address || '',
        website: company.website || '',
      });
    }
  }, [company]);

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      return await put('/settings/company', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['company'] });
      alert('تم حفظ التغييرات بنجاح');
    },
    onError: (error: any) => {
      alert('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    updateMutation.mutate(formData);
  };

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-zinc-100">إعدادات الشركة</h1>
      <div className="card max-w-2xl">
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">اسم الشركة</label>
              <input
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">الاسم بالعربية</label>
              <input
                value={formData.nameAr}
                onChange={(e) => handleChange('nameAr', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">الرقم الضريبي</label>
              <input
                value={formData.taxNumber}
                onChange={(e) => handleChange('taxNumber', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">السجل التجاري</label>
              <input
                value={formData.commercialRegister}
                onChange={(e) => handleChange('commercialRegister', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">الهاتف</label>
              <input
                value={formData.phone}
                onChange={(e) => handleChange('phone', e.target.value)}
                className="input"
              />
            </div>
            <div>
              <label className="label">البريد الإلكتروني</label>
              <input
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className="input"
              />
            </div>
          </div>
          <div>
            <label className="label">العنوان</label>
            <textarea
              value={formData.address}
              onChange={(e) => handleChange('address', e.target.value)}
              className="input"
              rows={2}
            />
          </div>
          <div>
            <label className="label">الموقع الإلكتروني</label>
            <input
              value={formData.website}
              onChange={(e) => handleChange('website', e.target.value)}
              className="input"
            />
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
