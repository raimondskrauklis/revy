// frontend/src/features/marketing/pages/LandingPage.tsx
import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { RevyLogo } from '@/components/auth/RevyLogo';
import { useAuth } from '@/contexts/AuthContext';

/* Cover-the-name / viewport (non-gate): 375 width and ~700–800 height usable. */

export function LandingPage() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      window.location.replace('/reviewer');
    }
  }, [isAuthenticated, isLoading]);

  return (
    <div className="min-h-screen bg-[color:var(--app-canvas)] font-mono">
      <div className="mx-auto flex min-h-screen max-w-3xl flex-col px-6 py-6">
        <header className="flex items-center justify-between gap-4">
          <RevyLogo to="/" />
          <Link
            to="/login"
            className="min-h-11 rounded-[var(--app-radius-md)] px-4 py-2 text-sm text-[color:var(--app-text-strong)] shadow-[inset_0_0_0_1px_var(--app-ring)] hover:bg-[color:var(--app-surface)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--app-ring-strong)]"
          >
            {t('landing.nav.signIn')}
          </Link>
        </header>

        <main className="flex flex-1 flex-col justify-center py-12">
          <p className="flex items-center gap-2 text-sm text-[color:var(--app-primary)]">
            <span aria-hidden>{'>'}</span>
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
          <div className="mt-8 flex flex-col items-start gap-3 sm:flex-row sm:items-center">
            <Link
              to="/login"
              className="inline-flex min-h-11 min-w-44 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-cta-bg)] px-6 text-sm font-medium text-[color:var(--app-cta-fg)] hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            >
              {t('landing.hero.cta')}
            </Link>
            <p className="font-sans text-sm text-[color:var(--app-text-muted)]">
              {t('landing.hero.secondary')}{' '}
              <Link to="/login" className="font-medium text-[color:var(--app-link)] hover:underline">
                {t('landing.nav.signIn')}
              </Link>
            </p>
          </div>
        </main>

        <footer className="py-4 font-sans text-xs text-[color:var(--app-text-muted)]">
          {t('landing.footer')}
        </footer>
      </div>
    </div>
  );
}
