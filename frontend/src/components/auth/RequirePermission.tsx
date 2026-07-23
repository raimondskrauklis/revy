// frontend/src/components/auth/RequirePermission.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { hasPermission } from '@/lib/permissions';
import type { Permission } from '@/lib/permissionTypes';

interface RequirePermissionProps {
  permission: Permission;
}

export function RequirePermission({ permission }: RequirePermissionProps) {
  const { user } = useAuth();

  if (
    !hasPermission(
      user?.role ?? undefined,
      permission,
      user?.platform_role ?? undefined,
    )
  ) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
