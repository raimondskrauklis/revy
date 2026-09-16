// frontend/src/features/reviewer/components/PullRequestStateBadge.tsx
import { useTranslation } from 'react-i18next';
import { pullRequestLifecycle } from '@/features/reviewer/pullRequestLifecycle';
import type { GitHubPullRequest, PullRequestLifecycle } from '@/features/reviewer/types';

interface PullRequestStateBadgeProps {
  pullRequest: Pick<GitHubPullRequest, 'state' | 'merged'>;
}

const BADGE_CLASS: Record<PullRequestLifecycle, string> = {
  open: 'bg-[color:var(--app-success-subtle)] text-[color:var(--app-success)]',
  merged: 'bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]',
  closed: 'bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]',
};

export function PullRequestStateBadge({ pullRequest }: PullRequestStateBadgeProps) {
  const { t } = useTranslation();
  const lifecycle = pullRequestLifecycle(pullRequest);

  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
        BADGE_CLASS[lifecycle],
      ].join(' ')}
    >
      {t(`reviewer.pullRequests.state.${lifecycle}`)}
    </span>
  );
}
