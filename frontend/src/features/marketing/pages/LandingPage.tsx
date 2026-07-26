// frontend/src/features/marketing/pages/LandingPage.tsx
import { useEffect } from 'react';
import { GitBranch, ShieldCheck, Users } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { RevyLogo } from '@/components/auth/RevyLogo';
import { useAuth } from '@/contexts/AuthContext';

const featureIcons = [GitBranch, ShieldCheck, Users] as const;
const featureKeys = ['github', 'review', 'workspace'] as const;

export function LandingPage() {
  const { t } = useTranslation();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      window.location.replace('/dashboard');
    }
  }, [isAuthenticated, isLoading]);

  return (
    <div className="min-h-screen bg-[color:var(--app-canvas)]">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 top-0 h-72 bg-[radial-gradient(ellipse_at_top,color-mix(in_srgb,var(--app-primary)_18%,transparent),transparent_65%)]"
      />
      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col px-6 py-6">
        <header className="flex items-center justify-between gap-4">
          <RevyLogo to="/" />
          <Link
            to="/login"
            className="min-h-11 rounded-lg px-4 py-2 text-sm font-medium text-[color:var(--app-text-strong)] ring-1 ring-[color:var(--app-ring)] hover:bg-[color:var(--app-surface)] focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('landing.nav.signIn')}
          </Link>
        </header>

        <main className="flex flex-1 flex-col justify-center py-12 lg:py-16">
          <section className="mx-auto max-w-3xl text-center">
            <p className="text-sm font-medium uppercase tracking-wide text-[color:var(--app-primary)]">
              {t('landing.hero.eyebrow')}
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight text-[color:var(--app-text-strong)] sm:text-5xl">
              {t('landing.hero.title')}
            </h1>
            <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-[color:var(--app-text-muted)] sm:text-lg">
              {t('landing.hero.subtitle')}
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                to="/login"
                className="inline-flex min-h-11 min-w-44 items-center justify-center rounded-lg bg-[color:var(--app-cta-bg)] px-6 text-sm font-semibold text-[color:var(--app-cta-fg)] shadow-sm hover:opacity-95 focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
              >
                {t('landing.hero.cta')}
              </Link>
              <p className="text-sm text-[color:var(--app-text-muted)]">
                {t('landing.hero.secondary')}{' '}
                <Link to="/login" className="font-medium text-[color:var(--app-link)] hover:underline">
                  {t('landing.nav.signIn')}
                </Link>
              </p>
            </div>
          </section>

          <section className="mx-auto mt-16 grid w-full max-w-5xl gap-4 sm:grid-cols-3">
            {featureKeys.map((key, index) => {
              const Icon = featureIcons[index];
              return (
                <article
                  key={key}
                  className="rounded-xl bg-[color:var(--app-surface)] p-5 text-left ring-1 ring-[color:var(--app-ring)]"
                >
                  <div className="mb-3 inline-flex rounded-lg bg-[color:color-mix(in_srgb,var(--app-primary)_12%,transparent)] p-2 text-[color:var(--app-primary)]">
                    <Icon className="h-5 w-5" aria-hidden />
                  </div>
                  <h2 className="text-base font-semibold text-[color:var(--app-text-strong)]">
                    {t(`landing.features.${key}.title`)}
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-[color:var(--app-text-muted)]">
                    {t(`landing.features.${key}.body`)}
                  </p>
                </article>
              );
            })}
          </section>
        </main>

        <footer className="py-4 text-center text-xs text-[color:var(--app-text-muted)]">
          {t('landing.footer')}
        </footer>
      </div>
    </div>
  );
}
