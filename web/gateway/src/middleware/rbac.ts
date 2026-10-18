import { Request, Response, NextFunction } from 'express';

const permissionsMap: Record<string, string[]> = {
  admin: ['*'],
  manager: [
    'read:*',
    'write:sales',
    'write:purchases',
    'write:inventory',
    'write:accounting',
    'write:hr',
    'write:payments',
    'write:projects',
    'manage:users',
  ],
  user: [
    'read:sales',
    'read:purchases',
    'read:inventory',
    'read:accounting',
    'read:hr',
    'read:payments',
    'read:projects',
    'write:sales',
    'write:purchases',
    'write:inventory',
  ],
  viewer: ['read:sales', 'read:purchases', 'read:inventory', 'read:accounting', 'read:hr', 'read:payments', 'read:projects'],
};

function matchPermission(userPermissions: string[], required: string): boolean {
  if (userPermissions.includes('*')) return true;

  const [reqAction, reqResource] = required.split(':');

  for (const perm of userPermissions) {
    const [action, resource] = perm.split(':');
    if (action === '*' || (action === reqAction && (resource === '*' || resource === reqResource))) {
      return true;
    }
  }
  return false;
}

export function authorize(...roles: string[]) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Not authenticated' });
      return;
    }

    if (!roles.includes(req.user.role)) {
      res.status(403).json({ error: 'Insufficient role permissions' });
      return;
    }

    next();
  };
}

export function requirePermission(permission: string) {
  return (req: Request, res: Response, next: NextFunction): void => {
    if (!req.user) {
      res.status(401).json({ error: 'Not authenticated' });
      return;
    }

    const rolePerms = permissionsMap[req.user.role] || [];
    if (!matchPermission(rolePerms, permission)) {
      res.status(403).json({ error: `Missing permission: ${permission}` });
      return;
    }

    next();
  };
}
