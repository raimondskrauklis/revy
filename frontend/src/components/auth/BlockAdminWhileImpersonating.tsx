// frontend/src/components/auth/BlockAdminWhileImpersonating.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function BlockAdminWhileImpersonating() {
  const { user } = useAuth();

  if (user?.impersonation?.active) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Outlet />;
}
