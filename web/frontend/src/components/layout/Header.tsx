import { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { useUIStore } from '@/stores/uiStore';
import { useCommandPaletteStore } from '@/stores/commandPaletteStore';
import { cn } from '@/lib/utils';

const routeLabels: Record<string, string> = {
  '/dashboard': 'الرئيسية',
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
  '/hr/employees': 'الموظفون',
  '/hr/departments': 'الأقسام',
  '/hr/attendance': 'الحضور والغياب',
  '/hr/leaves': 'الإجازات',
  '/hr/payroll': 'كشف الرواتب',
  '/payments/customers': 'مدفوعات العملاء',
  '/payments/suppliers': 'مدفوعات الموردين',
  '/payments/banks': 'الحسابات البنكية',
  '/projects': 'المشاريع',
  '/crm/customers': 'العملاء',
  '/crm/suppliers': 'الموردين',
  '/crm/leads': 'العملاء المحتملون',
  '/settings/users': 'المستخدمون',
  '/settings/companies': 'الشركات',
  '/settings/workflow': 'سير العمل',
  '/reports/sales': 'تقرير المبيعات',
  '/reports/purchases': 'تقرير المشتريات',
  '/reports/financial': 'التقرير المالي',
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

  const pathParts = location.pathname.split('/').filter(Boolean);
  const breadcrumbs = pathParts.map((part, idx) => {
    const path = '/' + pathParts.slice(0, idx + 1).join('/');
    return { label: routeLabels[path] || part, path };
  });

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-white dark:bg-zinc-900 border-b border-gray-200 dark:border-zinc-800 flex items-center justify-between px-4 lg:px-6 flex-shrink-0">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenuToggle}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-600 dark:text-zinc-400 transition-colors"
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </button>

        <button
          onClick={open}
          className="hidden md:flex items-center gap-2 px-3 py-1.5 text-sm text-gray-400 dark:text-zinc-500 bg-gray-100 dark:bg-zinc-800 rounded-lg hover:bg-gray-200 dark:hover:bg-zinc-700 transition-colors"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span>بحث...</span>
          <kbd className="text-xs px-1.5 py-0.5 bg-white dark:bg-zinc-700 rounded border border-gray-300 dark:border-zinc-600">⌘K</kbd>
        </button>

        <nav className="hidden md:flex items-center gap-2 text-sm">
          {breadcrumbs.map((crumb, idx) => (
            <div key={crumb.path} className="flex items-center gap-2">
              {idx > 0 && (
                <svg className="h-4 w-4 text-gray-300 dark:text-zinc-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              )}
              {idx === breadcrumbs.length - 1 ? (
                <span className="font-medium text-gray-900 dark:text-zinc-100">{crumb.label}</span>
              ) : (
                <button
                  onClick={() => navigate(crumb.path)}
                  className="text-gray-500 dark:text-zinc-400 hover:text-gray-700 dark:hover:text-zinc-200"
                >
                  {crumb.label}
                </button>
              )}
            </div>
          ))}
        </nav>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setLocale(locale === 'ar' ? 'en' : 'ar')}
          className="px-3 py-1.5 text-sm font-medium rounded-lg border border-gray-200 dark:border-zinc-700 hover:bg-gray-50 dark:hover:bg-zinc-800 transition-colors text-gray-700 dark:text-zinc-300"
        >
          {locale === 'ar' ? 'EN' : 'عربي'}
        </button>

        <button
          onClick={toggleTheme}
          className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-600 dark:text-zinc-400 transition-colors"
          title={theme === 'dark' ? 'الوضع الفاتح' : 'الوضع الداكن'}
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

        <button className="relative p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 text-gray-600 dark:text-zinc-400 transition-colors">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <span className="absolute top-1.5 left-1.5 h-2 w-2 bg-red-500 rounded-full" />
        </button>

        <div className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="flex items-center gap-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-zinc-800 transition-colors"
          >
            <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-white text-sm font-bold">
              {user?.fullName?.charAt(0) || 'م'}
            </div>
            <span className="hidden md:block text-sm font-medium text-gray-700 dark:text-zinc-300">
              {user?.fullName || 'المدير'}
            </span>
          </button>

          {userMenuOpen && (
            <>
              <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
              <div className="absolute left-0 top-full mt-2 w-48 bg-white dark:bg-zinc-900 rounded-xl shadow-lg border border-gray-200 dark:border-zinc-700 py-2 z-50 animate-scale-in">
                <div className="px-4 py-2 border-b border-gray-100 dark:border-zinc-800">
                  <p className="text-sm font-medium text-gray-900 dark:text-zinc-100">{user?.fullName || 'المدير'}</p>
                  <p className="text-xs text-gray-500 dark:text-zinc-400">{user?.email || 'admin@erp.com'}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full text-right px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-500/10 flex items-center gap-2 transition-colors"
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
