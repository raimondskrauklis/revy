// frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx
import { useTranslation } from 'react-i18next';
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
        {t('dashboard.planSummary.free', { plan: t(`settings.billing.plans.${plan}`) })}
      </p>
    </section>
  );
}