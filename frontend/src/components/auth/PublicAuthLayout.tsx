// frontend/src/components/auth/PublicAuthLayout.tsx
import type { ReactNode } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { RevyLogo } from '@/components/auth/RevyLogo';

interface PublicAuthLayoutProps {
  children: ReactNode;
  showBackHome?: boolean;
}

export function PublicAuthLayout({ children, showBackHome = true }: PublicAuthLayoutProps) {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-[color:var(--app-canvas)]">
      <div className="mx-auto grid min-h-screen max-w-6xl lg:grid-cols-2">
        <aside className="relative hidden overflow-hidden border-r border-[color:var(--app-ring)] bg-[color:var(--app-surface)] lg:flex lg:flex-col lg:justify-between lg:p-10">
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_top_left,color-mix(in_srgb,var(--app-primary)_22%,transparent),transparent_55%)]"
          />
          <div className="relative">
            <RevyLogo to="/" />
          </div>
          <div className="relative space-y-4">
            <p className="text-sm font-medium uppercase tracking-wide text-[color:var(--app-primary)]">
              {t('auth.login.panel.eyebrow')}
            </p>
            <h1 className="text-3xl font-semibold leading-tight text-[color:var(--app-text-strong)]">
              {t('auth.login.panel.title')}
            </h1>
            <p className="max-w-md text-base text-[color:var(--app-text-muted)]">
              {t('auth.login.panel.subtitle')}
            </p>
            <ul className="space-y-3 pt-2 text-sm text-[color:var(--app-text)]">
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--app-primary)]" />
                {t('auth.login.panel.bullet1')}
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--app-primary)]" />
                {t('auth.login.panel.bullet2')}
              </li>
              <li className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-[color:var(--app-primary)]" />
                {t('auth.login.panel.bullet3')}
              </li>
            </ul>
          </div>
          <p className="relative text-xs text-[color:var(--app-text-muted)]">{t('landing.footer')}</p>
        </aside>

        <div className="flex flex-col">
          <header className="flex items-center justify-between p-4 lg:justify-end lg:p-6">
            <div className="lg:hidden">
              <RevyLogo to="/" />
            </div>
            {showBackHome ? (
              <Link
                to="/"
                className="text-sm font-medium text-[color:var(--app-link)] hover:underline focus-visible:outline-none focus-visible:ring-2 ring-[color:var(--app-ring-strong)] rounded"
              >
                {t('auth.login.backHome')}
              </Link>
            ) : null}
          </header>
          <main className="flex flex-1 items-center justify-center p-6 pb-10">{children}</main>
        </div>
      </div>
    </div>
  );
}
