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
  { label: 'دليل الحسابات', path: '/accounting/accounts', group: 'المحاسبة', icon: '📊' },
  { label: 'القيود اليومية', path: '/accounting/journal', group: 'المحاسبة', icon: '📝' },
  { label: 'ميزان المراجعة', path: '/accounting/trial-balance', group: 'المحاسبة', icon: '⚖️' },
  { label: 'مدفوعات العملاء', path: '/payments/customers', group: 'المدفوعات', icon: '💰' },
  { label: 'مدفوعات الموردين', path: '/payments/suppliers', group: 'المدفوعات', icon: '💸' },
  { label: 'الحسابات البنكية', path: '/payments/banks', group: 'المدفوعات', icon: '🏦' },
  { label: 'الموظفون', path: '/hr/employees', group: 'الموارد البشرية', icon: '👤' },
  { label: 'الأقسام', path: '/hr/departments', group: 'الموارد البشرية', icon: '🏛️' },
  { label: 'الحضور والغياب', path: '/hr/attendance', group: 'الموارد البشرية', icon: '⏰' },
  { label: 'الإجازات', path: '/hr/leaves', group: 'الموارد البشرية', icon: '🏖️' },
  { label: 'كشف الرواتب', path: '/hr/payroll', group: 'الموارد البشرية', icon: '💵' },
  { label: 'المشاريع', path: '/projects', group: 'المشاريع', icon: '📁' },
  { label: 'المستخدمون', path: '/settings/users', group: 'الإعدادات', icon: '⚙️' },
  { label: 'الشركات', path: '/settings/companies', group: 'الإعدادات', icon: '🏢' },
  { label: 'سير العمل', path: '/settings/workflow', group: 'الإعدادات', icon: '🔄' },
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
      <div className="w-full max-w-lg mx-4 glass rounded-2xl shadow-2xl animate-scale-in overflow-hidden">
        <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-200 dark:border-zinc-700">
          <svg className="h-5 w-5 text-gray-400 dark:text-zinc-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="ابحث عن صفحة أو وحدة..."
            className="flex-1 bg-transparent outline-none text-gray-900 dark:text-zinc-100 placeholder-gray-400 dark:placeholder-zinc-500"
          />
          <kbd className="hidden sm:inline-flex items-center px-2 py-0.5 text-xs font-medium text-gray-500 dark:text-zinc-400 bg-gray-100 dark:bg-zinc-800 rounded">
            ESC
          </kbd>
        </div>

        <div className="max-h-80 overflow-y-auto p-2">
          {filtered.length === 0 ? (
            <div className="py-8 text-center text-sm text-gray-500 dark:text-zinc-400">
              لا توجد نتائج
            </div>
          ) : (
            filtered.map((item, idx) => (
              <button
                key={item.path}
                onClick={() => handleSelect(item.path)}
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


