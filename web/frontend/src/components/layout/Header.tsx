import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { useCommandPaletteStore } from '@/stores/commandPaletteStore';
import { getUnreadCount } from '@/api/notifications';
import { getCommandShortcutLabel } from '@/lib/utils';

const routeLabels: Record<string, string> = {
  '/dashboard': 'الرئيسية',
  '/notifications': 'الإشعارات',
  '/pos': 'نقطة البيع (POS)',
  '/analytics': 'التحليلات',
  '/promotions': 'العروض الترويجية',
  '/quotations': 'عروض الأسعار',
  '/quotations/new': 'عرض سعر جديد',
  '/returns/sales': 'مرتجعات المبيعات',
  '/returns/sales/new': 'مرتجع مبيعات جديد',
  '/returns/purchases': 'مرتجعات المشتريات',
  '/returns/purchases/new': 'مرتجع مشتريات جديد',
  '/accounting/financial-statements': 'القوائم المالية',
  '/accounting/fixed-assets': 'الأصول الثابتة',
  '/accounting/budgets': 'الميزانيات',
  '/accounting/aging-reports': 'أعمار الذمم',
  '/accounting/periods': 'إدارة الفترات',
  '/payments/bank-reconciliation': 'التسوية البنكية',
  '/settings/audit-log': 'سجل التدقيق',
  '/crm/loyalty': 'برنامج الولاء',
  '/crm/opportunities': 'فرص البيع',
  '/crm/follow-ups': 'المتابعات',
  '/crm/segments': 'شرائح العملاء',
  '/crm/dashboard': 'لوحة CRM',
  '/sales': 'فواتير المبيعات',
  '/sales/new': 'فاتورة مبيعات جديدة',
  '/purchases': 'أوامر الشراء',
  '/purchases/new': 'أمر شراء جديد',
  '/inventory/products': 'المنتجات',
  '/inventory/products/new': 'منتج جديد',
  '/inventory/categories': 'التصنيفات',
  '/inventory/warehouses': 'المخازن',
  '/inventory/movements': 'حركة المخزون',
  '/accounting/accounts': 'دليل الحسابات',
  '/accounting/journal': 'القيود اليومية',
  '/accounting/trial-balance': 'ميزان المراجعة',
  '/accounting/vouchers': 'سندات القبض والصرف',
  '/accounting/debtors-creditors': 'المدينون والدائنون',
  '/hr/employees': 'الموظفون',
  '/hr/departments': 'شجرة الأقسام',
  '/hr/attendance': 'الحضور والغياب',
  '/hr/leaves': 'الإجازات',
  '/hr/payroll': 'كشف الرواتب',
  '/hr/advances': 'سلف الموظفين',
  '/hr/dashboard': 'لوحة الموارد البشرية',
  '/hr/positions': 'الوظائف',
  '/hr/shifts': 'ورديات العمل',
  '/hr/leave-types': 'أنواع وأرصدة الإجازات',
  '/hr/overtime': 'الإضافي',
  '/hr/salary-adjustments': 'البدلات والمكافآت',
  '/hr/contracts': 'العقود',
  '/hr/resignations': 'الاستقالات',
  '/hr/performance-reviews': 'التقييمات',
  '/hr/recruitment': 'التوظيف',
  '/hr/training': 'التدريب والتطوير',
  '/hr/documents': 'مستندات الموظفين',
  '/hr/holidays': 'الإجازات الرسمية',
  '/payments/customers': 'مدفوعات العملاء',
  '/payments/suppliers': 'مدفوعات الموردين',
  '/payments/banks': 'الحسابات البنكية',
  '/projects': 'المشاريع',
  '/crm/customers': 'العملاء',
  '/crm/suppliers': 'الموردين',
  '/crm/leads': 'العملاء المحتملون',
  '/crm/tree': 'شجرة العملاء والموردين',
  '/settings/general': 'الإعدادات العامة',
  '/settings/numbering': 'سياسة الترقيم',
  '/settings/branches': 'الفروع',
  '/settings/users': 'المستخدمون',
  '/settings/roles': 'الأدوار والصلاحيات',
  '/settings/companies': 'الشركات',
  '/settings/workflow': 'سير العمل',
  '/reports/sales': 'تقرير المبيعات',
  '/reports/purchases': 'تقرير المشتريات',
  '/reports/financial': 'التقرير المالي',
  '/accounting/general-ledger': 'دفتر الأستاذ العام',
  '/accounting/cost-centers': 'مراكز التكلفة',
  '/accounting/recurring-je': 'قوالب القيود الدورية',
  '/settings/currencies': 'العملات وأسعار الصرف',
  '/settings/tax-rates': 'نِسب الضرائب',
  '/payments/cheques': 'إدارة الشيكات',
};

interface HeaderProps {
  onMenuToggle: () => void;
}

export function Header({ onMenuToggle }: HeaderProps) {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const { locale, setLocale, theme, toggleTheme } = useUIStore();
  const { open } = useCommandPaletteStore();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const shortcutLabel = getCommandShortcutLabel();

  const { data: unreadData } = useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: getUnreadCount,
    refetchInterval: 60_000,
  });
  const unreadCount = unreadData?.count ?? 0;

  useEffect(() => {
    setUserMenuOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!userMenuOpen) return;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setUserMenuOpen(false);
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [userMenuOpen]);

  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = pathParts.map((part, idx) => {
    const path = '/' + pathParts.slice(0, idx + 1).join('/');
    return { label: routeLabels[path] || decodeURIComponent(part), path };
  });

  const displayName = user?.fullName || 'المدير';

  const handleLogout = () => {
    setUserMenuOpen(false);
    logout();
    navigate('/login');
  };

  return (
    <header className="z-20 flex h-16 flex-shrink-0 items-center justify-between gap-2 border-b border-gray-200 bg-white/95 px-3 backdrop-blur transition-colors sm:px-4 lg:px-6 dark:border-zinc-800 dark:bg-zinc-900/95">
      <div className="flex min-w-0 items-center gap-2">
        <button
          onClick={onMenuToggle}
          aria-label="تبديل القائمة"
          title="تبديل القائمة"
          className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <button
          onClick={open}
          className="hidden items-center gap-2 rounded-lg bg-gray-100 px-3 py-1.5 text-sm text-gray-500 transition-colors hover:bg-gray-200 md:flex dark:bg-zinc-800 dark:text-zinc-400 dark:hover:bg-zinc-700"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span>بحث سريع...</span>
          <kbd className="rounded border border-gray-300 bg-white px-1.5 py-0.5 text-[11px] font-medium dark:border-zinc-600 dark:bg-zinc-700">
            {shortcutLabel}
          </kbd>
        </button>

        <button
          onClick={open}
          aria-label="بحث سريع"
          className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 md:hidden dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </button>

        <nav aria-label="مسار التنقل" className="hidden min-w-0 items-center gap-2 text-sm lg:flex">
          {breadcrumbs.map((crumb, idx) => (
            <div key={crumb.path} className="flex min-w-0 items-center gap-2">
              {idx > 0 && (
                <svg className="h-4 w-4 flex-shrink-0 text-gray-300 dark:text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              )}
              {idx === breadcrumbs.length - 1 ? (
                <span className="max-w-[14rem] truncate font-medium text-gray-900 dark:text-zinc-100" title={crumb.label}>
                  {crumb.label}
                </span>
              ) : (
                <button
                  onClick={() => navigate(crumb.path)}
                  className="max-w-[10rem] truncate text-gray-500 transition-colors hover:text-gray-700 dark:text-zinc-400 dark:hover:text-zinc-200"
                  title={crumb.label}
                >
                  {crumb.label}
                </button>
              )}
            </div>
          ))}
        </nav>
      </div>

      <div className="flex flex-shrink-0 items-center gap-1 sm:gap-2">
        <button
          onClick={() => setLocale(locale === 'ar' ? 'en' : 'ar')}
          aria-label={locale === 'ar' ? 'Switch to English' : 'التبديل إلى العربية'}
          className="hidden rounded-lg border border-gray-200 px-3 py-1.5 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 sm:inline-flex dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
        >
          {locale === 'ar' ? 'EN' : 'عربي'}
        </button>

        <button
          onClick={toggleTheme}
          aria-label={theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}
          title={theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}
          className="rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          {theme === 'dark' ? (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
            </svg>
          )}
        </button>

        <Link
          to="/notifications"
          aria-label={unreadCount > 0 ? `الإشعارات (${unreadCount} غير مقروء)` : 'الإشعارات'}
          title="الإشعارات"
          className="relative rounded-lg p-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-zinc-400 dark:hover:bg-zinc-800"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          {unreadCount > 0 && (
            <span className="absolute -left-0.5 -top-0.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold leading-none text-white ring-2 ring-white dark:ring-zinc-900">
              {unreadCount > 99 ? '99+' : unreadCount}
            </span>
          )}
        </Link>

        <div className="relative">
          <button
            onClick={() => setUserMenuOpen((openMenu) => !openMenu)}
            aria-haspopup="menu"
            aria-expanded={userMenuOpen}
            aria-label="قائمة المستخدم"
            className="flex items-center gap-2 rounded-lg p-1.5 transition-colors hover:bg-gray-100 dark:hover:bg-zinc-800"
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary-600 text-sm font-bold text-white">
              {displayName.charAt(0) || 'م'}
            </div>
            <span className="hidden max-w-32 truncate text-sm font-medium text-gray-700 md:block dark:text-zinc-300">
              {displayName}
            </span>
            <svg className="hidden h-3.5 w-3.5 text-gray-400 md:block" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>

          {userMenuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
              <div
                role="menu"
                aria-label="قائمة المستخدم"
                className="absolute left-0 top-full z-50 mt-2 w-56 animate-scale-in overflow-hidden rounded-xl border border-gray-200 bg-white py-1 shadow-xl dark:border-zinc-700 dark:bg-zinc-900"
              >
                <div className="border-b border-gray-100 px-4 py-3 dark:border-zinc-800">
                  <p className="truncate text-sm font-medium text-gray-900 dark:text-zinc-100">{displayName}</p>
                  <p className="truncate text-xs text-gray-500 dark:text-zinc-400">{user?.email || 'admin@erp.com'}</p>
                </div>
                <Link
                  to="/settings/general"
                  role="menuitem"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                  الإعدادات العامة
                </Link>
                <Link
                  to="/notifications"
                  role="menuitem"
                  onClick={() => setUserMenuOpen(false)}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 transition-colors hover:bg-gray-50 dark:text-zinc-300 dark:hover:bg-zinc-800"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                  </svg>
                  الإشعارات
                  {unreadCount > 0 && (
                    <span className="mr-auto rounded-full bg-red-100 px-1.5 py-0.5 text-[10px] font-semibold text-red-600 dark:bg-red-500/15 dark:text-red-400">
                      {unreadCount}
                    </span>
                  )}
                </Link>
                <div className="my-1 h-px bg-gray-100 dark:bg-zinc-800" />
                <button
                  role="menuitem"
                  onClick={handleLogout}
                  className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 transition-colors hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-500/10"
                >
                  <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  تسجيل الخروج
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
