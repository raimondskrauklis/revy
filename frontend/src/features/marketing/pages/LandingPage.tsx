// frontend/src/features/marketing/pages/LandingPage.tsx
import { useTranslation } from 'react-i18next';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

/* Cover-the-name / viewport (non-gate): 375 width and ~700–800 height usable. */

export function LandingPage() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading, login } = useAuth();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? '/reviewer';

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/reviewer" replace />;
  }

  return (
    <div className="min-h-screen bg-[color:var(--app-canvas)] font-mono">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-6 py-6">
        <main className="flex flex-1 flex-col justify-center py-12">
          <p className="flex items-center gap-2 text-sm text-[color:var(--app-primary)]">
            <span>{t('landing.hero.eyebrow')}</span>
            <span
              aria-hidden
              className="cursor-block inline-block h-4 w-2 bg-[color:var(--app-primary)]"
            />
          </p>
          <h1 className="mt-4 text-3xl font-medium tracking-tight text-[color:var(--app-text-strong)] sm:text-4xl">
            {t('landing.hero.title')}
          </h1>
          <p className="mt-4 max-w-xl font-sans text-base leading-relaxed text-[color:var(--app-text-muted)]">
            {t('landing.hero.subtitle')}
          </p>
          <div className="mt-8">
            <button
              type="button"
              onClick={() => login(from)}
              className="inline-flex min-h-11 min-w-44 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-cta-bg)] px-6 text-sm font-medium text-[color:var(--app-cta-fg)] hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('landing.hero.cta')}
            </button>
          </div>
        </main>
      </div>
    </div>
  );
}