import { useAuthStore } from '@/stores/authStore';
import type { Permission, UserRole } from '@/types';

const rolePermissions: Record<UserRole, Permission[]> = {
  admin: [
    'CREATE_SALE',
    'EDIT_SALE',
    'DELETE_SALE',
    'APPROVE_SALE',
    'VIEW_SALE',
    'CREATE_PURCHASE',
    'EDIT_PURCHASE',
    'DELETE_PURCHASE',
    'APPROVE_PURCHASE',
    'VIEW_PURCHASE',
    'CREATE_JOURNAL',
    'EDIT_JOURNAL',
    'DELETE_JOURNAL',
    'POST_JOURNAL',
    'VIEW_JOURNAL',
    'VIEW_REPORTS',
    'MANAGE_USERS',
    'MANAGE_SETTINGS',
    'MANAGE_ASSETS',
    'MANAGE_BUDGETS',
    'RECONCILE_BANK',
    'VIEW_AGING_REPORTS',
  ],
  accountant: [
    'CREATE_SALE',
    'EDIT_SALE',
    'VIEW_SALE',
    'CREATE_PURCHASE',
    'EDIT_PURCHASE',
    'VIEW_PURCHASE',
    'CREATE_JOURNAL',
    'EDIT_JOURNAL',
    'POST_JOURNAL',
    'VIEW_JOURNAL',
    'VIEW_REPORTS',
    'MANAGE_ASSETS',
    'MANAGE_BUDGETS',
    'RECONCILE_BANK',
    'VIEW_AGING_REPORTS',
  ],
  manager: [
    'CREATE_SALE',
    'EDIT_SALE',
    'APPROVE_SALE',
    'VIEW_SALE',
    'CREATE_PURCHASE',
    'EDIT_PURCHASE',
    'APPROVE_PURCHASE',
    'VIEW_PURCHASE',
    'VIEW_JOURNAL',
    'VIEW_REPORTS',
    'MANAGE_BUDGETS',
    'VIEW_AGING_REPORTS',
  ],
  viewer: [
    'VIEW_SALE',
    'VIEW_PURCHASE',
    'VIEW_JOURNAL',
    'VIEW_REPORTS',
    'VIEW_AGING_REPORTS',
  ],
};

export function usePermissions() {
  const { user } = useAuthStore();
  const role = (user?.role || 'viewer') as UserRole;
  const permissions = rolePermissions[role] || rolePermissions.viewer;

  const hasPermission = (permission: Permission): boolean => {
    return permissions.includes(permission);
  };

  const hasAnyPermission = (perms: Permission[]): boolean => {
    return perms.some((p) => permissions.includes(p));
  };

  const hasAllPermissions = (perms: Permission[]): boolean => {
    return perms.every((p) => permissions.includes(p));
  };

  return {
    role,
    permissions,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    isAdmin: role === 'admin',
    isAccountant: role === 'accountant',
    isManager: role === 'manager',
    isViewer: role === 'viewer',
  };
}
