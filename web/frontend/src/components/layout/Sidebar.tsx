import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { cn } from '@/lib/utils';

interface NavItem {
  label: string;
  path?: string;
  icon: React.ReactNode;
  children?: { label: string; path: string }[];
}

const navGroups: { title: string; items: NavItem[] }[] = [
  {
    title: 'القائمة',
    items: [
      {
        label: 'الرئيسية',
        path: '/dashboard',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
          </svg>
        ),
      },
    ],
  },
  {
    title: 'المبيعات',
    items: [
      {
        label: 'المبيعات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 14l6-6m-5.5.5h.01m4.99 5h.01M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16l3.5-2 3.5 2 3.5-2 3.5 2z" />
          </svg>
        ),
        children: [
          { label: 'فواتير المبيعات', path: '/sales' },
          { label: 'فاتورة جديدة', path: '/sales/new' },
        ],
      },
    ],
  },
  {
    title: 'المشتريات',
    items: [
      {
        label: 'المشتريات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
          </svg>
        ),
        children: [
          { label: 'أوامر الشراء', path: '/purchases' },
          { label: 'أمر شراء جديد', path: '/purchases/new' },
        ],
      },
    ],
  },
  {
    title: 'المخزون',
    items: [
      {
        label: 'المنتجات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        ),
        children: [
          { label: 'قائمة المنتجات', path: '/inventory/products' },
          { label: 'منتج جديد', path: '/inventory/products/new' },
          { label: 'التصنيفات', path: '/inventory/categories' },
          { label: 'المخازن', path: '/inventory/warehouses' },
          { label: 'حركة المخزون', path: '/inventory/movements' },
        ],
      },
    ],
  },
  {
    title: 'العملاء والموردين',
    items: [
      {
        label: 'العملاء',
        path: '/crm/customers',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        ),
      },
      {
        label: 'الموردين',
        path: '/crm/suppliers',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        ),
      },
      {
        label: 'العملاء المحتملون',
        path: '/crm/leads',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        ),
      },
    ],
  },
  {
    title: 'المحاسبة',
    items: [
      {
        label: 'المحاسبة',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
        ),
        children: [
          { label: 'دليل الحسابات', path: '/accounting/accounts' },
          { label: 'القيود اليومية', path: '/accounting/journal' },
          { label: 'ميزان المراجعة', path: '/accounting/trial-balance' },
          { label: 'القوائم المالية', path: '/accounting/financial-statements' },
          { label: 'الأصول الثابتة', path: '/accounting/fixed-assets' },
          { label: 'الميزانيات', path: '/accounting/budgets' },
          { label: 'أعمار الذمم', path: '/accounting/aging-reports' },
        ],
      },
    ],
  },
  {
    title: 'المدفوعات',
    items: [
      {
        label: 'المدفوعات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
          </svg>
        ),
        children: [
          { label: 'مدفوعات العملاء', path: '/payments/customers' },
          { label: 'مدفوعات الموردين', path: '/payments/suppliers' },
          { label: 'الحسابات البنكية', path: '/payments/banks' },
          { label: 'التسوية البنكية', path: '/payments/bank-reconciliation' },
        ],
      },
    ],
  },
  {
    title: 'الموارد البشرية',
    items: [
      {
        label: 'الموارد البشرية',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
          </svg>
        ),
        children: [
          { label: 'الموظفون', path: '/hr/employees' },
          { label: 'الأقسام', path: '/hr/departments' },
          { label: 'الحضور والغياب', path: '/hr/attendance' },
          { label: 'الإجازات', path: '/hr/leaves' },
          { label: 'كشف الرواتب', path: '/hr/payroll' },
        ],
      },
    ],
  },
  {
    title: 'المشاريع',
    items: [
      {
        label: 'المشاريع',
        path: '/projects',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
          </svg>
        ),
      },
    ],
  },
  {
    title: 'الإعدادات',
    items: [
      {
        label: 'الإعدادات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        ),
        children: [
          { label: 'المستخدمون', path: '/settings/users' },
          { label: 'الشركات', path: '/settings/companies' },
          { label: 'سير العمل', path: '/settings/workflow' },
          { label: 'سجل التدقيق', path: '/settings/audit-log' },
        ],
      },
    ],
  },
  {
    title: 'التقارير',
    items: [
      {
        label: 'التقارير',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        ),
        children: [
          { label: 'تقرير المبيعات', path: '/reports/sales' },
          { label: 'تقرير المشتريات', path: '/reports/purchases' },
          { label: 'التقرير المالي', path: '/reports/financial' },
        ],
      },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onNavigate: () => void;
}

export function Sidebar({ collapsed, onNavigate }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuthStore();
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    navGroups.forEach((g) => {
      initial[g.title] = g.items.some(
        (item) =>
          item.path === location.pathname ||
          item.children?.some((c) => location.pathname.startsWith(c.path))
      );
    });
    return initial;
  });

  const toggleGroup = (title: string) => {
    if (collapsed) return;
    setExpandedGroups((prev) => ({ ...prev, [title]: !prev[title] }));
  };

  const isActive = (path: string) => location.pathname === path;
  const isGroupActive = (item: NavItem) =>
    item.path === location.pathname ||
    item.children?.some((c) => location.pathname.startsWith(c.path));

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-white">
      <div className={cn('flex items-center h-16 px-4 border-b border-zinc-800', collapsed && 'justify-center')}>
        <div className="h-8 w-8 bg-primary-500 rounded-lg flex items-center justify-center flex-shrink-0">
          <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        {!collapsed && (
          <div className="mr-3">
            <h1 className="text-sm font-bold">نظام ERP</h1>
            <p className="text-xs text-zinc-400">إدارة المخازن</p>
          </div>
        )}
      </div>

      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-1" role="navigation" aria-label="القائمة الرئيسية">
        {navGroups.map((group) => (
          <div key={group.title}>
            {!collapsed && (
              <button
                onClick={() => toggleGroup(group.title)}
                className="flex items-center justify-between w-full px-3 py-2 text-xs font-semibold text-zinc-500 uppercase tracking-wider hover:text-zinc-300 transition-colors"
              >
                {group.title}
                <svg
                  className={cn(
                    'h-3 w-3 transition-transform duration-200',
                    expandedGroups[group.title] !== false && 'rotate-180'
                  )}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
            )}

            {group.items.map((item) => {
              if (item.children && !collapsed && expandedGroups[group.title] !== false) {
                return (
                  <div key={item.label}>
                    <div
                      className={cn(
                        'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                        isGroupActive(item) ? 'text-white bg-zinc-800' : 'text-zinc-300 hover:bg-zinc-800/50'
                      )}
                    >
                      <span className="flex-shrink-0 text-zinc-400">{item.icon}</span>
                      <span>{item.label}</span>
                    </div>
                    <div className="mr-8 mt-1 space-y-0.5">
                      {item.children.map((child) => (
                        <Link
                          key={child.path}
                          to={child.path}
                          onClick={onNavigate}
                          className={cn(
                            'block px-3 py-2 rounded-lg text-sm transition-colors',
                            isActive(child.path)
                              ? 'text-primary-400 bg-primary-500/10 font-medium'
                              : 'text-zinc-400 hover:text-white hover:bg-zinc-800/50'
                          )}
                        >
                          {child.label}
                        </Link>
                      ))}
                    </div>
                  </div>
                );
              }

              if (!item.children || collapsed) {
                return (
                  <Link
                    key={item.path}
                    to={item.path!}
                    onClick={onNavigate}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                      isActive(item.path!)
                        ? 'text-white bg-primary-600'
                        : 'text-zinc-300 hover:bg-zinc-800/50',
                      collapsed && 'justify-center'
                    )}
                    title={collapsed ? item.label : undefined}
                  >
                    <span className="flex-shrink-0">{item.icon}</span>
                    {!collapsed && <span>{item.label}</span>}
                  </Link>
                );
              }

              return null;
            })}
          </div>
        ))}
      </nav>

      {!collapsed && (
        <div className="border-t border-zinc-800 p-4">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center text-sm font-bold">
              {user?.fullName?.charAt(0) || 'م'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.fullName || 'المدير'}</p>
              <p className="text-xs text-zinc-400 truncate">{user?.email || 'admin@erp.com'}</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
