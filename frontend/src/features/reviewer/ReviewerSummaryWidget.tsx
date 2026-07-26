// frontend/src/features/reviewer/ReviewerSummaryWidget.tsx
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useReviewerAvailability } from '@/features/reviewer/hooks';

export function ReviewerSummaryWidget() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { data: available, isLoading } = useReviewerAvailability(workspaceId);

  if (!workspaceId || isLoading || !available) {
    return null;
  }

  return (
    <article className="flex h-full flex-col justify-between gap-4 rounded-lg bg-[color:var(--app-surface)] p-4 ring-1 ring-[color:var(--app-ring)]">
      <div className="space-y-2">
        <h3 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('reviewer.widget.title')}
        </h3>
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.widget.body')}</p>
      </div>
      <Link
        to="/reviewer"
        className="inline-flex min-h-11 items-center justify-center rounded-lg bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
      >
        {t('reviewer.widget.open')}
      </Link>
    </article>
  );
}
