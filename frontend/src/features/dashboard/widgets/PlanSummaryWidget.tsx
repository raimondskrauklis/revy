// frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

export function PlanSummaryWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const plan = user?.workspace_plan ?? 'free';

  if (!user || !workspaceId) {
    return null;
  }

  return (
    <section className="space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
        {t('dashboard.planSummary.title')}
      </h2>
      <p className="text-sm text-[color:var(--app-text-muted)]">
        {t('dashboard.planSummary.current', {
          plan: t(`settings.billing.plans.${plan}`),
        })}
      </p>
      <Link
        to="/settings/billing"
        className="inline-flex min-h-11 items-center text-sm text-[color:var(--app-cta-bg)] underline-offset-2 hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('dashboard.planSummary.manage')}
      </Link>
    </section>
  );
}
