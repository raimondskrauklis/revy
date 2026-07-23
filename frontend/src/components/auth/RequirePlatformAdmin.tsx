// frontend/src/components/auth/RequirePlatformAdmin.tsx
import { Navigate, Outlet } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { isPlatformAdmin } from '@/lib/permissions';

export function RequirePlatformAdmin() {
  const { t } = useTranslation();
  const { user, isLoading, isUserLoading } = useAuth();

  if (isLoading || (isUserLoading && user == null)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)]">
        <p className="text-[color:var(--app-text-muted)]">{t('auth.loading')}</p>
      </div>
    );
  }

  if (!isPlatformAdmin(user?.platform_role ?? undefined)) {
    return <Navigate to="/unauthorized" replace />;
  }

  return <Outlet />;
}
