// frontend/src/features/reviewer/components/JudgeSkippedBadge.tsx
import { useTranslation } from 'react-i18next';
import type { GitHubReviewJudgeStatus } from '@/features/reviewer/types';

interface JudgeSkippedBadgeProps {
  judgeStatus: GitHubReviewJudgeStatus;
}

const SKIPPED_STATUSES = new Set<GitHubReviewJudgeStatus>([
  'skipped_disabled',
  'skipped_unavailable',
]);

export function JudgeSkippedBadge({ judgeStatus }: JudgeSkippedBadgeProps) {
  const { t } = useTranslation();

  if (!SKIPPED_STATUSES.has(judgeStatus)) {
    return null;
  }

  const labelKey =
    judgeStatus === 'skipped_unavailable'
      ? 'reviewer.judge.skippedUnavailable'
      : 'reviewer.judge.skipped';

  return (
    <span className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-[color:var(--app-warning-subtle)] text-[color:var(--app-warning)]">
      {t(labelKey)}
    </span>
  );
}
