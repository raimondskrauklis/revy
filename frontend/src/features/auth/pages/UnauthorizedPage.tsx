// frontend/src/features/auth/pages/UnauthorizedPage.tsx
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

type UnauthorizedReason = 'profile' | 'permission';

export function UnauthorizedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout, isUserLoading } = useAuth();
  const reason = (location.state as { reason?: UnauthorizedReason } | null)?.reason;
  const permissionDenied = reason === 'permission';
  const sessionWithoutProfile = !user && !isUserLoading;

  useEffect(() => {
    if (permissionDenied || !user) return;
    navigate('/reviewer', { replace: true });
  }, [navigate, permissionDenied, user]);

  if (!user && isUserLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('auth.loading')}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t(
            sessionWithoutProfile
              ? 'auth.unauthorized.sessionFailed.title'
              : 'auth.unauthorized.title',
          )}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t(
            sessionWithoutProfile
              ? 'auth.unauthorized.sessionFailed.body'
              : 'auth.unauthorized.body',
          )}
        </p>
        {user?.email && (
          <p className="text-xs text-[color:var(--app-text-subtle)]">
            {t('auth.unauthorized.signedInAs', { email: user.email })}
          </p>
        )}
        <div className="flex flex-wrap justify-center gap-3">
          {!sessionWithoutProfile ? (
            <button
              type="button"
              onClick={() => navigate(-1)}
            className="min-h-11 px-4 rounded-[var(--app-radius-md)] shadow-[inset_0_0_0_1px_var(--app-ring)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('auth.unauthorized.goBack')}
            </button>
          ) : null}
          {!sessionWithoutProfile ? (
            <Link
              to="/reviewer"
              className="min-h-11 inline-flex items-center px-4 rounded-[var(--app-radius-md)] bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('auth.unauthorized.goHome')}
            </Link>
          ) : null}
          <button
            type="button"
            onClick={() => logout()}
            className="min-h-11 px-4 rounded-[var(--app-radius-md)] text-[color:var(--app-text-muted)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('auth.actions.signOut')}
          </button>
        </div>
      </div>
    </div>
  );
}
