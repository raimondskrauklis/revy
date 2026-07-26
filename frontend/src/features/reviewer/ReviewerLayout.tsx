// frontend/src/features/reviewer/ReviewerLayout.tsx
import { Outlet, Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

export function ReviewerLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const onHome = location.pathname === '/reviewer';

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-[color:var(--app-text-strong)]">
            {t('reviewer.title')}
          </h1>
          <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.subtitle')}</p>
        </div>
        {!onHome ? (
          <Link
            to="/reviewer"
            className="ml-auto text-sm text-[color:var(--app-link)] hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
          >
            {t('reviewer.backToRepositories')}
          </Link>
        ) : null}
      </div>
      <Outlet />
    </div>
  );
}
