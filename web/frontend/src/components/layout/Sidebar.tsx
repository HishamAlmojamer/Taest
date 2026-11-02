import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import { usePermissions } from '@/hooks/usePermissions';
import { cn } from '@/lib/utils';
import type { Permission } from '@/types';

interface NavItem {
  label: string;
  path?: string;
  icon: React.ReactNode;
  badge?: number;
  children?: { label: string; path: string; requiredPermission?: Permission }[];
  requiredPermission?: Permission;
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
      {
        label: 'الإشعارات',
        path: '/notifications',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
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
          { label: 'نقطة البيع (POS)', path: '/pos' },
          { label: 'عروض الأسعار', path: '/quotations' },
          { label: 'عرض سعر جديد', path: '/quotations/new' },
          { label: 'العروض الترويجية', path: '/promotions' },
          { label: 'مرتجعات المبيعات', path: '/returns/sales' },
          { label: 'مرتجع مبيعات جديد', path: '/returns/sales/new' },
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
          { label: 'مرتجعات المشتريات', path: '/returns/purchases' },
          { label: 'مرتجع مشتريات جديد', path: '/returns/purchases/new' },
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
        label: 'برنامج الولاء',
        path: '/crm/loyalty',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.196-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
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
      {
        label: 'شجرة العملاء والموردين',
        path: '/crm/tree',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5h6a1 1 0 011 1v5a1 1 0 01-1 1H4a1 1 0 01-1-1V6a1 1 0 011-1zm10 0h6a1 1 0 011 1v5a1 1 0 01-1 1h-6a1 1 0 01-1-1V6a1 1 0 011-1zM4 16h6a1 1 0 011 1v3a1 1 0 01-1 1H4a1 1 0 01-1-1v-3a1 1 0 011-1zm10 0h6a1 1 0 011 1v3a1 1 0 01-1 1h-6a1 1 0 01-1-1v-3a1 1 0 011-1z" />
          </svg>
        ),
      },
      {
        label: 'فرص البيع',
        path: '/crm/opportunities',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3v18h18" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 14l3-3 3 2 4-5" />
          </svg>
        ),
      },
      {
        label: 'المتابعات',
        path: '/crm/follow-ups',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        ),
      },
      {
        label: 'شرائح العملاء',
        path: '/crm/segments',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 4v16" />
          </svg>
        ),
      },
      {
        label: 'لوحة CRM',
        path: '/crm/dashboard',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
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
          { label: 'دفتر الأستاذ العام', path: '/accounting/general-ledger' },
          { label: 'القوائم المالية', path: '/accounting/financial-statements' },
          { label: 'الأصول الثابتة', path: '/accounting/fixed-assets' },
          { label: 'الميزانيات', path: '/accounting/budgets' },
          { label: 'أعمار الذمم', path: '/accounting/aging-reports' },
          { label: 'المدينون والدائنون', path: '/accounting/debtors-creditors' },
          { label: 'سندات القبض والصرف', path: '/accounting/vouchers' },
          { label: 'إدارة الفترات', path: '/accounting/periods' },
          { label: 'مراكز التكلفة', path: '/accounting/cost-centers' },
          { label: 'قوالب القيود الدورية', path: '/accounting/recurring-je' },
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
          { label: 'الشيكات', path: '/payments/cheques' },
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
          { label: 'لوحة الموارد البشرية', path: '/hr/dashboard' },
          { label: 'الموظفون', path: '/hr/employees' },
          { label: 'شجرة الأقسام', path: '/hr/departments' },
          { label: 'الوظائف', path: '/hr/positions' },
          { label: 'ورديات العمل', path: '/hr/shifts' },
          { label: 'الحضور والغياب', path: '/hr/attendance' },
          { label: 'الإجازات', path: '/hr/leaves' },
          { label: 'أنواع وأرصدة الإجازات', path: '/hr/leave-types' },
          { label: 'الإضافي', path: '/hr/overtime' },
          { label: 'البدلات والمكافآت', path: '/hr/salary-adjustments' },
          { label: 'سلف الموظفين', path: '/hr/advances' },
          { label: 'كشف الرواتب', path: '/hr/payroll' },
          { label: 'العقود', path: '/hr/contracts' },
          { label: 'الاستقالات', path: '/hr/resignations' },
          { label: 'التقييمات', path: '/hr/performance-reviews' },
          { label: 'التوظيف', path: '/hr/recruitment' },
          { label: 'التدريب والتطوير', path: '/hr/training' },
          { label: 'مستندات الموظفين', path: '/hr/documents' },
          { label: 'الإجازات الرسمية', path: '/hr/holidays' },
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
          { label: 'الإعدادات العامة', path: '/settings/general' },
          { label: 'سياسة الترقيم', path: '/settings/numbering' },
          { label: 'الفروع', path: '/settings/branches' },
          { label: 'المستخدمون', path: '/settings/users' },
          { label: 'الأدوار والصلاحيات', path: '/settings/roles' },
          { label: 'الشركات', path: '/settings/companies' },
          { label: 'سير العمل', path: '/settings/workflow' },
          { label: 'سجل التدقيق', path: '/settings/audit-log' },
          { label: 'العملات وأسعار الصرف', path: '/settings/currencies' },
          { label: 'نِسب الضرائب', path: '/settings/tax-rates' },
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
  {
    title: 'التحليلات',
    items: [
      {
        label: 'التحليلات',
        icon: (
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        ),
        path: '/analytics',
      },
    ],
  },
];

interface SidebarProps {
  collapsed: boolean;
  onNavigate: () => void;
  onExpand: () => void;
  onClose?: () => void;
}

function pathMatches(base: string, pathname: string) {
  return pathname === base || pathname.startsWith(base.endsWith('/') ? base : `${base}/`);
}

function itemIsActive(item: NavItem, pathname: string) {
  if (item.path && pathMatches(item.path, pathname)) return true;
  return item.children?.some((child) => pathMatches(child.path, pathname)) ?? false;
}

function matchesQuery(text: string, query: string) {
  return text.toLowerCase().includes(query);
}

export function Sidebar({ collapsed, onNavigate, onExpand, onClose }: SidebarProps) {
  const location = useLocation();
  const { user } = useAuthStore();
  const { hasPermission } = usePermissions();
  const [search, setSearch] = useState('');
  const [expandedGroups, setExpandedGroups] = useState<Record<string, boolean>>(() => {
    const initial: Record<string, boolean> = {};
    navGroups.forEach((group) => {
      if (group.items.some((item) => itemIsActive(item, location.pathname))) {
        initial[group.title] = true;
      }
    });
    return initial;
  });

  useEffect(() => {
    const activeGroup = navGroups.find((group) =>
      group.items.some((item) => itemIsActive(item, location.pathname))
    );
    if (activeGroup) {
      setExpandedGroups((prev) =>
        prev[activeGroup.title] ? prev : { ...prev, [activeGroup.title]: true }
      );
    }
    setSearch('');
  }, [location.pathname]);

  useEffect(() => {
    if (collapsed) setSearch('');
  }, [collapsed]);

  const handleNavigate = () => {
    setSearch('');
    onNavigate();
  };

  const toggleGroup = (title: string) => {
    if (collapsed) {
      onExpand();
      setExpandedGroups((prev) => ({ ...prev, [title]: true }));
      return;
    }
    setExpandedGroups((prev) => ({ ...prev, [title]: !prev[title] }));
  };

  const query = search.trim().toLowerCase();
  const isSearching = query.length > 0;

  // Filter nav groups by permissions and by the search query.
  const filteredGroups = navGroups
    .map((group) => {
      const items = group.items
        .filter((item) => !item.requiredPermission || hasPermission(item.requiredPermission))
        .map((item) => ({
          ...item,
          children: item.children?.filter(
            (child) => !child.requiredPermission || hasPermission(child.requiredPermission)
          ),
        }))
        .filter((item) => !item.children || item.children.length > 0)
        .filter((item) => {
          if (!isSearching) return true;
          if (matchesQuery(item.label, query) || matchesQuery(group.title, query)) return true;
          return item.children?.some((child) => matchesQuery(child.label, query)) ?? false;
        })
        .map((item) => {
          if (!isSearching || !item.children) return item;
          const groupMatches = matchesQuery(item.label, query) || matchesQuery(group.title, query);
          if (groupMatches) return item;
          return {
            ...item,
            children: item.children.filter((child) => matchesQuery(child.label, query)),
          };
        });
      return { ...group, items };
    })
    .filter((group) => group.items.length > 0);

  const displayName = user?.fullName || 'المدير';
  const initial = displayName.charAt(0) || 'م';

  return (
    <div className="flex h-full flex-col bg-zinc-950 text-white">
      {/* Logo */}
      <div
        className={cn(
          'flex h-16 flex-shrink-0 items-center gap-2 border-b border-zinc-800/80 px-3',
          collapsed ? 'justify-center' : 'justify-between'
        )}
      >
        <Link
          to="/dashboard"
          onClick={handleNavigate}
          className="flex min-w-0 items-center gap-3"
          title="الرئيسية"
        >
          <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-primary-500 to-primary-700 shadow-lg shadow-primary-500/20">
            <svg className="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            </svg>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <h1 className="truncate text-sm font-bold tracking-tight">نظام ERP</h1>
              <p className="truncate text-[11px] text-zinc-400">إدارة متكاملة</p>
            </div>
          )}
        </Link>

        {onClose && !collapsed && (
          <button
            type="button"
            onClick={onClose}
            aria-label="إغلاق القائمة"
            className="rounded-lg p-2 text-zinc-400 transition-colors hover:bg-zinc-800 hover:text-white lg:hidden"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Search */}
      {!collapsed && (
        <div className="px-3 pt-3">
          <div className="relative">
            <svg
              className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="ابحث في القائمة..."
              aria-label="بحث في القائمة"
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/80 py-2 pl-7 pr-9 text-sm text-zinc-200 outline-none transition-colors placeholder:text-zinc-500 focus:border-primary-500/60 focus:ring-2 focus:ring-primary-500/20"
            />
            {search && (
              <button
                type="button"
                onClick={() => setSearch('')}
                aria-label="مسح البحث"
                className="absolute left-2 top-1/2 -translate-y-1/2 rounded p-0.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-300"
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Navigation */}
      <nav
        className="sidebar-scroll flex-1 overflow-y-auto px-2 py-3"
        role="navigation"
        aria-label="القائمة الرئيسية"
      >
        {filteredGroups.length === 0 && (
          <p className="px-3 py-10 text-center text-xs text-zinc-500">
            لا توجد نتائج لـ «{search.trim()}»
          </p>
        )}

        {filteredGroups.map((group, groupIndex) => {
          const showGroupLabel =
            !collapsed &&
            group.items.every((item) => !item.children) &&
            group.title !== 'القائمة' &&
            !group.items.some((item) => item.label === group.title);

          return (
            <div
              key={group.title}
              className={cn(groupIndex > 0 && 'mt-2 border-t border-zinc-800/60 pt-2')}
            >
              {showGroupLabel && (
                <p className="px-3 pb-1 pt-1 text-[10px] font-semibold uppercase tracking-wider text-zinc-500">
                  {group.title}
                </p>
              )}

              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const active = itemIsActive(item, location.pathname);

                  if (item.children && item.children.length > 0) {
                    const isOpen = isSearching || expandedGroups[group.title] === true;
                    return (
                      <div key={`${group.title}-${item.label}`}>
                        <button
                          type="button"
                          onClick={() => toggleGroup(group.title)}
                          title={collapsed ? item.label : undefined}
                          aria-label={collapsed ? item.label : undefined}
                          aria-expanded={collapsed ? undefined : isOpen}
                          className={cn(
                            'group relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                            active
                              ? 'bg-zinc-800/80 text-white'
                              : 'text-zinc-300 hover:bg-zinc-800/50 hover:text-white',
                            collapsed && 'justify-center'
                          )}
                        >
                          {active && (
                            <span className="absolute inset-y-2 right-0 w-0.5 rounded-full bg-primary-500" />
                          )}
                          <span
                            className={cn(
                              'flex-shrink-0 transition-colors',
                              active ? 'text-primary-400' : 'text-zinc-400 group-hover:text-zinc-200'
                            )}
                          >
                            {item.icon}
                          </span>
                          {!collapsed && (
                            <>
                              <span className="flex-1 truncate text-right">{item.label}</span>
                              {item.badge !== undefined && item.badge > 0 && (
                                <span className="rounded-full bg-primary-500/20 px-1.5 py-0.5 text-[10px] font-semibold text-primary-400">
                                  {item.badge}
                                </span>
                              )}
                              <svg
                                className={cn(
                                  'h-3.5 w-3.5 flex-shrink-0 text-zinc-500 transition-transform duration-200',
                                  isOpen && 'rotate-180'
                                )}
                                fill="none"
                                viewBox="0 0 24 24"
                                stroke="currentColor"
                              >
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                              </svg>
                            </>
                          )}
                        </button>

                        {!collapsed && isOpen && (
                          <div className="mr-5 mt-0.5 space-y-0.5 border-r border-zinc-800 pr-3">
                            {item.children.map((child) => {
                              const childActive = pathMatches(child.path, location.pathname);
                              return (
                                <Link
                                  key={child.path}
                                  to={child.path}
                                  onClick={handleNavigate}
                                  aria-current={childActive ? 'page' : undefined}
                                  className={cn(
                                    'block rounded-md px-3 py-1.5 text-sm transition-colors',
                                    childActive
                                      ? 'bg-primary-500/10 font-medium text-primary-400'
                                      : 'text-zinc-400 hover:bg-zinc-800/40 hover:text-zinc-100'
                                  )}
                                >
                                  {child.label}
                                </Link>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  }

                  return (
                    <Link
                      key={item.path ?? `${group.title}-${item.label}`}
                      to={item.path ?? '/dashboard'}
                      onClick={handleNavigate}
                      title={collapsed ? item.label : undefined}
                      aria-label={collapsed ? item.label : undefined}
                      aria-current={active ? 'page' : undefined}
                      className={cn(
                        'relative flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all duration-150',
                        active
                          ? 'bg-gradient-to-l from-primary-600 to-primary-700 text-white shadow-lg shadow-primary-600/20'
                          : 'text-zinc-300 hover:bg-zinc-800/50 hover:text-white',
                        collapsed && 'justify-center'
                      )}
                    >
                      <span className={cn('flex-shrink-0', active ? 'text-white' : 'text-zinc-400')}>
                        {item.icon}
                      </span>
                      {!collapsed && <span className="truncate">{item.label}</span>}
                    </Link>
                  );
                })}
              </div>
            </div>
          );
        })}
      </nav>

      {/* User footer */}
      <div
        className={cn(
          'flex-shrink-0 border-t border-zinc-800/80 p-3',
          collapsed && 'flex justify-center'
        )}
      >
        {collapsed ? (
          <Link
            to="/settings/general"
            onClick={handleNavigate}
            title={displayName}
            aria-label={`الإعدادات — ${displayName}`}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-sm font-bold shadow-md"
          >
            {initial}
          </Link>
        ) : (
          <div className="flex items-center gap-3 rounded-xl bg-zinc-900/70 p-2">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-primary-500 to-primary-700 text-sm font-bold shadow-md">
              {initial}
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">{displayName}</p>
              <p className="truncate text-[11px] text-zinc-400">{user?.email || 'admin@erp.com'}</p>
            </div>
            <Link
              to="/settings/general"
              onClick={handleNavigate}
              title="الإعدادات"
              aria-label="الإعدادات العامة"
              className="rounded-lg p-1.5 text-zinc-500 transition-colors hover:bg-zinc-800 hover:text-zinc-200"
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
