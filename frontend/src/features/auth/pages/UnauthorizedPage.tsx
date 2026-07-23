// frontend/src/features/auth/pages/UnauthorizedPage.tsx
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function UnauthorizedPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <div className="max-w-md space-y-4 text-center">
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('auth.unauthorized.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('auth.unauthorized.body')}</p>
        {user?.email && (
          <p className="text-xs text-[color:var(--app-text-subtle)]">
            {t('auth.unauthorized.signedInAs', { email: user.email })}
          </p>
        )}
        <div className="flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="min-h-11 px-4 rounded-lg ring-1 ring-[color:var(--app-ring)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('auth.unauthorized.goBack')}
          </button>
          <Link
            to="/dashboard"
            className="min-h-11 inline-flex items-center px-4 rounded-lg bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('auth.unauthorized.goHome')}
          </Link>
          <button
            type="button"
            onClick={() => logout()}
            className="min-h-11 px-4 rounded-lg text-[color:var(--app-text-muted)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('auth.actions.signOut')}
          </button>
        </div>
      </div>
    </div>
  );
}
