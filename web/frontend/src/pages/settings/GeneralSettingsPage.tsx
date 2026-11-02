import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { get, put } from '@/api/client';
import type { AppSetting } from '@/types';
import { PageHeader } from '@/components/ui/PageHeader';
import { LoadingSpinner } from '@/components/ui/LoadingSpinner';
import { useToast } from '@/components/ui/Toast';
import { cn } from '@/lib/utils';

function toSnakeCase(str: string): string {
  return str.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

interface GeneralSettingsResponse {
  items: AppSetting[];
  values: Record<string, string>;
}

const GROUP_LABELS: Record<string, string> = {
  general: 'عام',
  numbering: 'الترقيم والمستندات',
  inventory: 'المخزون',
  finance: 'المحاسبة والعملات',
  invoice: 'الفواتير',
  ui: 'الواجهة والمظهر',
};

const GROUP_ICONS: Record<string, string> = {
  general: '🏢',
  numbering: '🔢',
  inventory: '📦',
  finance: '💰',
  invoice: '🧾',
  ui: '🎨',
};

const GROUP_ORDER = ['general', 'numbering', 'finance', 'invoice', 'inventory', 'ui'];

function SettingField({
  item,
  value,
  onChange,
}: {
  item: AppSetting;
  value: string;
  onChange: (v: string) => void;
}) {
  const dataType = item.dataType || 'text';
  const id = `setting-${item.key}`;

  if (dataType === 'boolean') {
    const checked = value === 'true';
    return (
      <label className="flex items-center gap-3 cursor-pointer">
        <input
          id={id}
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(String(e.target.checked))}
          className="h-4 w-4 rounded border-gray-300 text-primary-600 dark:border-zinc-600 dark:bg-zinc-800"
        />
        <span className="text-sm text-gray-700 dark:text-zinc-300">
          {item.description || item.key}
        </span>
      </label>
    );
  }

  if (dataType === 'select' && item.options && item.options.length > 0) {
    return (
      <div>
        <label className="label">{item.description || item.key}</label>
        <select
          id={id}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className="input"
        >
          {item.options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    );
  }

  if (dataType === 'number') {
    return (
      <div>
        <label className="label">{item.description || item.key}</label>
        <input
          id={id}
          type="number"
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className="input"
        />
      </div>
    );
  }

  if (dataType === 'textarea') {
    return (
      <div>
        <label className="label">{item.description || item.key}</label>
        <textarea
          id={id}
          value={value ?? ''}
          onChange={(e) => onChange(e.target.value)}
          className="input"
          rows={2}
        />
      </div>
    );
  }

  return (
    <div>
      <label className="label">{item.description || item.key}</label>
      <input
        id={id}
        value={value ?? ''}
        onChange={(e) => onChange(e.target.value)}
        className="input"
      />
    </div>
  );
}

export default function GeneralSettingsPage() {
  const queryClient = useQueryClient();
  const [values, setValues] = useState<Record<string, string>>({});
  const [activeGroup, setActiveGroup] = useState<string>('general');
  const toast = useToast();

  const { data, isLoading } = useQuery({
    queryKey: ['general-settings'],
    queryFn: async () => get<GeneralSettingsResponse>('/settings/general'),
  });

  useEffect(() => {
    if (data?.values) {
      const normalized: Record<string, string> = {};
      for (const [key, val] of Object.entries(data.values)) {
        normalized[toSnakeCase(key)] = val ?? '';
      }
      setValues(normalized);
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: (payload: Record<string, string>) => put('/settings/general', payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['general-settings'] });
      toast.success('تم حفظ الإعدادات بنجاح');
    },
    onError: (error: any) => {
      toast.error('حدث خطأ أثناء الحفظ: ' + (error?.response?.data?.detail || error.message));
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    saveMutation.mutate(values);
  };

  const handleChange = (key: string, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }));
  };

  if (isLoading) return <LoadingSpinner />;

  const items = (data?.items || []).filter((i) => i.isVisible !== false);
  const groups = Array.from(
    new Set(items.map((i) => i.group || 'general'))
  ).sort((a, b) => {
    const ia = GROUP_ORDER.indexOf(a);
    const ib = GROUP_ORDER.indexOf(b);
    return (ia === -1 ? 99 : ia) - (ib === -1 ? 99 : ib);
  });

  const activeGroupItems = items.filter((i) => (i.group || 'general') === activeGroup);

  return (
    <div className="space-y-6">
      <PageHeader
        title="الإعدادات العامة"
        subtitle="تخصيص إعدادات النظام والشركة بطريقة قابلة للتهيئة"
        icon={
          <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        }
      />

      <div className="flex flex-wrap gap-2">
        {groups.map((group) => (
          <button
            key={group}
            type="button"
            onClick={() => setActiveGroup(group)}
            className={cn(
              'px-4 py-2 rounded-xl text-sm font-medium transition-colors',
              activeGroup === group
                ? 'bg-primary-600 text-white shadow-sm'
                : 'bg-white dark:bg-zinc-800 text-gray-600 dark:text-zinc-300 border border-gray-200 dark:border-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-700'
            )}
          >
            <span className="me-1.5">{GROUP_ICONS[group] || '⚙️'}</span>
            {GROUP_LABELS[group] || group}
          </button>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <div key={activeGroup} className="card max-w-3xl">
          <h2 className="text-lg font-semibold text-gray-800 dark:text-zinc-200 mb-4 border-b border-gray-100 dark:border-zinc-800 pb-3 flex items-center gap-2">
            <span>{GROUP_ICONS[activeGroup] || '⚙️'}</span>
            {GROUP_LABELS[activeGroup] || activeGroup}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {activeGroupItems.map((item) => (
              <div key={item.key} className={item.dataType === 'textarea' || item.dataType === 'boolean' ? 'md:col-span-2' : ''}>
                <SettingField
                  item={item}
                  value={values[item.key] ?? ''}
                  onChange={(v) => handleChange(item.key, v)}
                />
              </div>
            ))}
          </div>
        </div>
        <div className="flex justify-end">
          <button type="submit" className="btn-primary" disabled={saveMutation.isPending}>
            {saveMutation.isPending ? 'جاري الحفظ...' : 'حفظ الإعدادات'}
          </button>
        </div>
      </form>
    </div>
  );
}
