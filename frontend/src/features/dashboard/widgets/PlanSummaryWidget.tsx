// frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';

export function PlanSummaryWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;

  if (!user || !workspaceId) {
    return null;
  }

  const completed = user.completed_review_runs ?? 0;
  const limit = user.review_run_limit ?? null;
  const isPro = limit === null;

  return (
    <section className="space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('dashboard.planSummary.title')}
      </h2>
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {isPro
          ? t('dashboard.planSummary.unlimited')
          : t('dashboard.planSummary.usage', { completed, limit })}
      </p>
      {!isPro && completed >= (limit ?? 0) && (
        <p className="text-sm text-[color:var(--app-warning)]">
          {t('dashboard.planSummary.limitReached')}
        </p>
      )}
    </section>
  );
}