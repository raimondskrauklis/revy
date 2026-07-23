// frontend/src/components/auth/RequirePlatformAdmin.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { isPlatformAdmin } from '@/lib/permissions';

export function RequirePlatformAdmin() {
  const { user } = useAuth();

  if (!isPlatformAdmin(user?.platform_role ?? undefined)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
