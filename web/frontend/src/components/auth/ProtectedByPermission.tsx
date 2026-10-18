import { usePermissions } from '@/hooks/usePermissions';
import type { Permission } from '@/types';
import { Navigate } from 'react-router-dom';

interface ProtectedByPermissionProps {
  permission: Permission;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ProtectedByPermission({ permission, children, fallback }: ProtectedByPermissionProps) {
  const { hasPermission } = usePermissions();
  
  if (!hasPermission(permission)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
}

interface ProtectedByRoleProps {
  roles: Array<'admin' | 'accountant' | 'manager' | 'viewer'>;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export function ProtectedByRole({ roles, children, fallback }: ProtectedByRoleProps) {
  const { role } = usePermissions();
  
  if (!roles.includes(role)) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return <Navigate to="/dashboard" replace />;
  }
  
  return <>{children}</>;
}
