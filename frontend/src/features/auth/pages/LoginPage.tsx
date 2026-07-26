// frontend/src/features/auth/pages/LoginPage.tsx
import { useEffect } from 'react';
import { LogIn } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';
import { PublicAuthLayout } from '@/components/auth/PublicAuthLayout';
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
    <PublicAuthLayout>
      <div className="w-full max-w-md space-y-6">
        <div className="space-y-2 text-center lg:text-left">
          <h1 className="text-2xl font-semibold text-[color:var(--app-text-strong)]">
            {t('auth.login.title')}
          </h1>
          <p className="text-sm leading-relaxed text-[color:var(--app-text-muted)]">
            {t('auth.login.body')}
          </p>
        </div>

        <div className="rounded-xl bg-[color:var(--app-surface)] p-6 ring-1 ring-[color:var(--app-ring)] shadow-sm">
          <button
            type="button"
            onClick={() => login(from)}
            className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-semibold text-[color:var(--app-cta-fg)] transition hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            <LogIn className="h-4 w-4" aria-hidden />
            {t('auth.login.action')}
          </button>
          <p className="mt-4 text-center text-xs text-[color:var(--app-text-muted)]">
            {t('auth.login.hint')}
          </p>
        </div>
      </div>
    </PublicAuthLayout>
  );
}
