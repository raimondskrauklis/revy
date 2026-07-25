// frontend/src/features/dashboard/widgets/SetupChecklistWidget.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import {
  evaluateChecklist,
  hasIncompleteChecklistSteps,
} from '@/features/dashboard/checklistSteps';
import { useChecklistContext } from '@/features/dashboard/hooks';

export function SetupChecklistWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { data: context, isLoading } = useChecklistContext(workspaceId);

  if (!user || !workspaceId) {
    return null;
  }

  if (isLoading || !context) {
    return (
      <section className="rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      </section>
    );
  }

  const checklistContext = {
    workspaceId,
    memberCount: context.memberCount,
    installationCount: context.installationCount,
    plan: context.plan,
  };

  if (!hasIncompleteChecklistSteps(user, checklistContext)) {
    return null;
  }

  const steps = evaluateChecklist(user, checklistContext).filter((step) => !step.isComplete);
  const totalSteps = evaluateChecklist(user, checklistContext).length;
  const completedCount = totalSteps - steps.length;

  return (
    <section className="space-y-3 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('dashboard.checklist.title')}
        </h2>
        <span className="text-sm text-[color:var(--app-text-muted)]">
          {t('dashboard.checklist.progress', { completed: completedCount, total: totalSteps })}
        </span>
      </div>
      <ul className="space-y-2">
        {steps.map((step) => (
          <li key={step.id}>
            {step.href ? (
              <Link
                to={step.href}
                className="flex min-h-11 items-center text-sm text-[color:var(--app-cta-bg)] underline-offset-2 hover:underline focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
              >
                {t(step.labelKey)}
              </Link>
            ) : (
              <span className="text-sm text-[color:var(--app-text-strong)]">
                {t(step.labelKey)}
              </span>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
