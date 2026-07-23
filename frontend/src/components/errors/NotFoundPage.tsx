// frontend/src/components/errors/NotFoundPage.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';

export function NotFoundPage() {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen flex items-center justify-center bg-[color:var(--app-canvas)] p-6">
      <div className="text-center space-y-4">
        <h1 className="text-xl font-semibold text-[color:var(--app-text-strong)]">
          {t('errors.not_found_page.title')}
        </h1>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {t('errors.not_found_page.body')}
        </p>
        <Link
          to="/dashboard"
          className="inline-flex min-h-11 items-center px-4 rounded-lg bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {t('auth.unauthorized.goHome')}
        </Link>
      </div>
    </div>
  );
}
