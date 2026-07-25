// frontend/src/features/installations/InstallationsSummaryWidget.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useChecklistContext } from '@/features/dashboard/hooks';
import { GitHubInstallationStatus } from '@/shared/types/enums';

export function InstallationsSummaryWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { data: context, isLoading } = useChecklistContext(workspaceId);

  if (!workspaceId) {
    return null;
  }

  const count = context?.installationCount ?? 0;

  return (
    <article className="flex h-full flex-col justify-between gap-4 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <div className="space-y-2">
        <h3 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('dashboard.installationsSummary.title')}
        </h3>
        <p className="text-sm text-[color:var(--app-text-muted)]">
          {isLoading
            ? t('common.loading')
            : t('dashboard.installationsSummary.count', { count })}
        </p>
        {!isLoading && count > 0 ? (
          <p className="text-sm text-[color:var(--app-text-muted)]">
            {t('dashboard.installationsSummary.statusHint', {
              status: t(`installations.status.${GitHubInstallationStatus.active}`),
            })}
          </p>
        ) : null}
      </div>
      <Link
        to="/installations"
        className="inline-flex min-h-11 items-center justify-center rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('dashboard.installationsSummary.manage')}
      </Link>
    </article>
  );
}
