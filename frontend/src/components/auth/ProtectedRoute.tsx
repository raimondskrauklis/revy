// frontend/src/components/auth/ProtectedRoute.tsx
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { optionalViteEnv } from '@/lib/env';

const REQUIRE_PROFILE_FORM = optionalViteEnv('VITE_REGISTRATION_REQUIRE_PROFILE_FORM') === 'true';
const REQUIRE_ADMIN_APPROVAL = optionalViteEnv('VITE_REGISTRATION_REQUIRE_ADMIN_APPROVAL') === 'true';

export function ProtectedRoute() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading, isUserLoading, user } = useAuth();
  const location = useLocation();

  if (isLoading || (isAuthenticated && isUserLoading && user == null)) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)]">
        <p className="text-[color:var(--app-text-muted)]">{t('auth.loading')}</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  const status = user?.status;

  if (status === 'pending_email_verification') {
    return <Navigate to="/auth/verify-email" replace />;
  }
  if (status === 'pending_profile' && REQUIRE_PROFILE_FORM) {
    return <Navigate to="/complete-profile" replace />;
  }
  if (status === 'pending_approval' && REQUIRE_ADMIN_APPROVAL) {
    return <Navigate to="/pending-approval" replace />;
  }
  if (status === 'rejected') {
    return <Navigate to="/account-rejected" replace />;
  }
  if (status === 'suspended') {
    return <Navigate to="/account-suspended" replace />;
  }

  return <Outlet />;
}
