import { useEffect, useState, useMemo, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCommandPaletteStore } from '@/stores/commandPaletteStore';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path: string;
  group: string;
  icon: string;
}

const allNavItems: NavItem[] = [
  { label: 'الرئيسية', path: '/dashboard', group: 'القائمة', icon: '🏠' },
  { label: 'الإشعارات', path: '/notifications', group: 'القائمة', icon: '🔔' },
  { label: 'العروض الترويجية', path: '/promotions', group: 'المبيعات', icon: '🎯' },
  { label: 'برنامج الولاء', path: '/crm/loyalty', group: 'العملاء والموردين', icon: '⭐' },
  { label: 'فواتير المبيعات', path: '/sales', group: 'المبيعات', icon: '📄' },
  { label: 'فاتورة مبيعات جديدة', path: '/sales/new', group: 'المبيعات', icon: '➕' },
  { label: 'أوامر الشراء', path: '/purchases', group: 'المشتريات', icon: '🛒' },
  { label: 'أمر شراء جديد', path: '/purchases/new', group: 'المشتريات', icon: '➕' },
  { label: 'المنتجات', path: '/inventory/products', group: 'المخزون', icon: '📦' },
  { label: 'منتج جديد', path: '/inventory/products/new', group: 'المخزون', icon: '➕' },
  { label: 'التصنيفات', path: '/inventory/categories', group: 'المخزون', icon: '🏷️' },
  { label: 'المخازن', path: '/inventory/warehouses', group: 'المخزون', icon: '🏭' },
  { label: 'حركة المخزون', path: '/inventory/movements', group: 'المخزون', icon: '🔄' },
  { label: 'العملاء', path: '/crm/customers', group: 'العملاء والموردين', icon: '👥' },
  { label: 'الموردين', path: '/crm/suppliers', group: 'العملاء والموردين', icon: '🏢' },
  { label: 'العملاء المحتملون', path: '/crm/leads', group: 'العملاء والموردين', icon: '⚡' },
  { label: 'شجرة العملاء والموردين', path: '/crm/tree', group: 'العملاء والموردين', icon: '🌳' },
  { label: 'دليل الحسابات', path: '/accounting/accounts', group: 'المحاسبة', icon: '📊' },
  { label: 'القيود اليومية', path: '/accounting/journal', group: 'المحاسبة', icon: '📝' },
  { label: 'ميزان المراجعة', path: '/accounting/trial-balance', group: 'المحاسبة', icon: '⚖️' },
  { label: 'القوائم المالية', path: '/accounting/financial-statements', group: 'المحاسبة', icon: '📋' },
  { label: 'الفترات المالية', path: '/accounting/periods', group: 'المحاسبة', icon: '🗓️' },
  { label: 'الأصول الثابتة', path: '/accounting/fixed-assets', group: 'المحاسبة', icon: '🏗️' },
  { label: 'الميزانيات', path: '/accounting/budgets', group: 'المحاسبة', icon: '🎯' },
  { label: 'تقارير الأعمار', path: '/accounting/aging-reports', group: 'المحاسبة', icon: '⏳' },
  { label: 'دفتر الأستاذ العام', path: '/accounting/general-ledger', group: 'المحاسبة', icon: '📒' },
  { label: 'مراكز التكلفة', path: '/accounting/cost-centers', group: 'المحاسبة', icon: '📊' },
  { label: 'قوالب القيود الدورية', path: '/accounting/recurring-je', group: 'المحاسبة', icon: '🔄' },
  { label: 'مدفوعات العملاء', path: '/payments/customers', group: 'المدفوعات', icon: '💰' },
  { label: 'مدفوعات الموردين', path: '/payments/suppliers', group: 'المدفوعات', icon: '💸' },
  { label: 'الحسابات البنكية', path: '/payments/banks', group: 'المدفوعات', icon: '🏦' },
  { label: 'الشيكات', path: '/payments/cheques', group: 'المدفوعات', icon: '🪙' },
  { label: 'التسوية البنكية', path: '/payments/bank-reconciliation', group: 'المدفوعات', icon: '🔄' },
  { label: 'الموظفون', path: '/hr/employees', group: 'الموارد البشرية', icon: '👤' },
  { label: 'الأقسام', path: '/hr/departments', group: 'الموارد البشرية', icon: '🏛️' },
  { label: 'الحضور والغياب', path: '/hr/attendance', group: 'الموارد البشرية', icon: '⏰' },
  { label: 'الإجازات', path: '/hr/leaves', group: 'الموارد البشرية', icon: '🏖️' },
  { label: 'كشف الرواتب', path: '/hr/payroll', group: 'الموارد البشرية', icon: '💵' },
  { label: 'سلف الموظفين', path: '/hr/advances', group: 'الموارد البشرية', icon: '💳' },
  { label: 'لوحة الموارد البشرية', path: '/hr/dashboard', group: 'الموارد البشرية', icon: '📊' },
  { label: 'الوظائف', path: '/hr/positions', group: 'الموارد البشرية', icon: '🎖️' },
  { label: 'ورديات العمل', path: '/hr/shifts', group: 'الموارد البشرية', icon: '🕐' },
  { label: 'أنواع وأرصدة الإجازات', path: '/hr/leave-types', group: 'الموارد البشرية', icon: '🗂️' },
  { label: 'الإضافي', path: '/hr/overtime', group: 'الموارد البشرية', icon: '⚡' },
  { label: 'البدلات والمكافآت', path: '/hr/salary-adjustments', group: 'الموارد البشرية', icon: '🎁' },
  { label: 'العقود', path: '/hr/contracts', group: 'الموارد البشرية', icon: '📄' },
  { label: 'الاستقالات', path: '/hr/resignations', group: 'الموارد البشرية', icon: '🚪' },
  { label: 'التقييمات', path: '/hr/performance-reviews', group: 'الموارد البشرية', icon: '⭐' },
  { label: 'التوظيف', path: '/hr/recruitment', group: 'الموارد البشرية', icon: '🎯' },
  { label: 'التدريب والتطوير', path: '/hr/training', group: 'الموارد البشرية', icon: '🎓' },
  { label: 'مستندات الموظفين', path: '/hr/documents', group: 'الموارد البشرية', icon: '🗃️' },
  { label: 'الإجازات الرسمية', path: '/hr/holidays', group: 'الموارد البشرية', icon: '🎉' },
  { label: 'المشاريع', path: '/projects', group: 'المشاريع', icon: '📁' },
  { label: 'الإعدادات العامة', path: '/settings/general', group: 'الإعدادات', icon: '⚙️' },
  { label: 'الفروع', path: '/settings/branches', group: 'الإعدادات', icon: '🏬' },
  { label: 'المستخدمون', path: '/settings/users', group: 'الإعدادات', icon: '👤' },
  { label: 'الأدوار والصلاحيات', path: '/settings/roles', group: 'الإعدادات', icon: '🔐' },
  { label: 'الشركات', path: '/settings/companies', group: 'الإعدادات', icon: '🏢' },
  { label: 'سير العمل', path: '/settings/workflow', group: 'الإعدادات', icon: '🔄' },
  { label: 'سجل التدقيق', path: '/settings/audit-log', group: 'الإعدادات', icon: '📜' },
  { label: 'العملات وأسعار الصرف', path: '/settings/currencies', group: 'الإعدادات', icon: '💱' },
  { label: 'نِسب الضرائب', path: '/settings/tax-rates', group: 'الإعدادات', icon: '🏛️' },
  { label: 'تقرير المبيعات', path: '/reports/sales', group: 'التقارير', icon: '📈' },
  { label: 'تقرير المشتريات', path: '/reports/purchases', group: 'التقارير', icon: '📉' },
  { label: 'التقرير المالي', path: '/reports/financial', group: 'التقارير', icon: '💹' },
];

export function CommandPalette() {
  const { isOpen, close } = useCommandPaletteStore();
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const filtered = useMemo(() => {
    if (!query.trim()) return allNavItems;
    const q = query.toLowerCase();
    return allNavItems.filter(
      (item) =>
        item.label.toLowerCase().includes(q) ||
        item.group.toLowerCase().includes(q) ||
        item.path.toLowerCase().includes(q)
    );
  }, [query]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        useCommandPaletteStore.getState().toggle();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setActiveIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    setActiveIndex(0);
  }, [query]);

  useEffect(() => {
    if (!isOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [isOpen]);

  useEffect(() => {
    const activeItem = listRef.current?.querySelector<HTMLElement>('[data-active="true"]');
    activeItem?.scrollIntoView({ block: 'nearest' });
  }, [activeIndex]);

  const handleSelect = useCallback(
    (path: string) => {
      navigate(path);
      close();
    },
    [navigate, close]
  );

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setActiveIndex((prev) => Math.min(prev + 1, filtered.length - 1));
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        setActiveIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === 'Enter' && filtered[activeIndex]) {
        handleSelect(filtered[activeIndex].path);
      } else if (e.key === 'Escape') {
        close();
      }
    },
    [filtered, activeIndex, handleSelect, close]
  );

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center pt-[15vh] bg-black/50 dark:bg-black/70 animate-fade-in"
      onClick={(e) => {
        if (e.target === e.currentTarget) close();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="البحث السريع"
        className="mx-4 w-full max-w-lg animate-scale-in overflow-hidden rounded-2xl shadow-2xl glass"
      >
        <div className="flex items-center gap-3 border-b border-gray-200 px-4 py-3 dark:border-zinc-700">
          <svg className="h-5 w-5 flex-shrink-0 text-gray-400 dark:text-zinc-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="ابحث عن صفحة أو وحدة..."
            aria-label="ابحث عن صفحة أو وحدة"
            role="combobox"
            aria-expanded="true"
            aria-controls="command-palette-results"
            aria-activedescendant={
              filtered[activeIndex] ? `command-palette-item-${activeIndex}` : undefined
            }
            className="flex-1 bg-transparent text-gray-900 outline-none placeholder-gray-400 dark:text-zinc-100 dark:placeholder-zinc-500"
          />
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-500 dark:text-zinc-400 bg-gray-100 dark:bg-zinc-800 rounded">
            ESC
          </kbd>
        </div>

        <div
          ref={listRef}
          id="command-palette-results"
          role="listbox"
          aria-label="نتائج البحث"
          className="max-h-80 overflow-y-auto p-2"
        >
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500 dark:text-zinc-400">
              لا توجد نتائج لـ «{query.trim()}»
            </div>
          ) : (
            filtered.map((item, idx) => (
              <button
                key={item.path}
                id={`command-palette-item-${idx}`}
                role="option"
                aria-selected={idx === activeIndex}
                data-active={idx === activeIndex}
                onClick={() => handleSelect(item.path)}
                onMouseEnter={() => setActiveIndex(idx)}
                className={cn(
                  'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors text-right',
                  idx === activeIndex
                    ? 'bg-primary-500/10 text-primary-600 dark:text-primary-400'
                    : 'text-gray-700 dark:text-zinc-300 hover:bg-gray-100 dark:hover:bg-zinc-800'
                )}
              >
                <span className="text-base">{item.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="font-medium truncate">{item.label}</div>
                  <div className="text-xs text-gray-400 dark:text-zinc-500 truncate">{item.group}</div>
                </div>
                <svg className="h-4 w-4 text-gray-300 dark:text-zinc-600 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))
          )}
        </div>

        <div className="flex items-center justify-between px-4 py-2 border-t border-gray-200 dark:border-zinc-700 text-xs text-gray-400 dark:text-zinc-500">
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-zinc-800 rounded">↑↓</kbd>
            <span>للتنقل</span>
          </div>
          <div className="flex items-center gap-2">
            <kbd className="px-1.5 py-0.5 bg-gray-100 dark:bg-zinc-800 rounded">↵</kbd>
            <span>للتحديد</span>
          </div>
        </div>
      </div>
    </div>
  );
}


