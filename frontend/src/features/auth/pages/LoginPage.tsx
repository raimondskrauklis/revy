// frontend/src/features/auth/pages/LoginPage.tsx
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function LoginPage() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading, login } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? '/dashboard';

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      window.location.replace(from);
    }
  }, [from, isAuthenticated, isLoading]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <div className="w-full max-w-md rounded-xl bg-[color:var(--app-surface)] ring-1 ring-[color:var(--app-ring)] p-6 space-y-4">
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('auth.login.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('auth.login.body')}</p>
        <button
          type="button"
          onClick={() => login(from)}
          className="min-h-11 w-full rounded-lg bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('auth.login.action')}
        </button>
      </div>
    </div>
  );
}
