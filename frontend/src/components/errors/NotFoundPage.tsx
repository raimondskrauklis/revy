// frontend/src/components/errors/NotFoundPage.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div className="flex min-h-screen items-center justify-center bg-[color:var(--app-canvas)] p-6 font-mono">
      <div className="max-w-md space-y-4 text-center rounded-[var(--app-radius-md)] p-6 shadow-[inset_0_0_0_1px_var(--app-ring)]">
        <h1 className="text-xl font-medium text-[color:var(--app-text-strong)]">
          {t('errors.not_found_page.title')}
        </h1>
        <p className="font-sans text-sm text-[color:var(--app-text-muted)]">
          {t('errors.not_found_page.body')}
        </p>
        <Link
          to="/reviewer"
          className="inline-flex min-h-11 items-center rounded-[var(--app-radius-md)] px-4 bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('auth.unauthorized.goHome')}
        </Link>
      </div>
    </div>
  );
}
