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
  const ready = Boolean(workspaceId && available);

  let body: string;
  if (!workspaceId) {
    body = t('reviewer.noWorkspace');
  } else if (isLoading) {
    body = t('common.loading');
  } else if (ready) {
    body = t('reviewer.widget.body');
  } else {
    body = t('reviewer.widget.unavailable');
  }

  return (
    <article className="flex h-full flex-col justify-between gap-4 rounded-[var(--app-radius-md)] bg-[color:var(--app-surface)] p-4 shadow-[inset_0_0_0_1px_var(--app-ring)]">
      <div className="space-y-2">
        <h3 className="text-base font-medium text-[color:var(--app-text-strong)]">
          {t('reviewer.widget.title')}
        </h3>
        <p className="text-sm text-[color:var(--app-text-muted)]">{body}</p>
      </div>
      {workspaceId && !isLoading ? (
        <Link
          to={ready ? '/reviewer' : '/installations'}
          className="inline-flex min-h-11 items-center justify-center rounded-[var(--app-radius-md)] bg-[color:var(--app-cta-bg)] px-4 text-sm font-medium text-[color:var(--app-cta-fg)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
        >
          {ready ? t('reviewer.widget.open') : t('reviewer.widget.connect')}
        </Link>
      ) : null}
    </article>
  );
}
