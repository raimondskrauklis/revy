// frontend/src/features/reviewer/components/MergeReadinessBadge.tsx
import { useTranslation } from 'react-i18next';
import type { MergeConclusion } from '@/features/reviewer/types';

interface MergeReadinessBadgeProps {
  conclusion: MergeConclusion | null;
  published: boolean;
  prOpen?: boolean;
}

const BADGE_CLASS: Record<MergeConclusion, string> = {
  success: 'bg-[color:var(--app-success-subtle)] text-[color:var(--app-success)]',
  neutral: 'bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]',
  failure: 'bg-[color:var(--app-danger-subtle)] text-[color:var(--app-danger)]',
};

export function MergeReadinessBadge({
  conclusion,
  published,
  prOpen = true,
}: MergeReadinessBadgeProps) {
  const { t } = useTranslation();

  if (!published) {
    return (
      <span className="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
        {t('reviewer.mergeReadiness.notPublished')}
      </span>
    );
  }

  if (!conclusion) {
    return null;
  }

  return (
    <span
      className={[
        'inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium',
        BADGE_CLASS[conclusion],
      ].join(' ')}
    >
      {t(
        conclusion === 'success' && !prOpen
          ? 'reviewer.mergeReadiness.successClosed'
          : `reviewer.mergeReadiness.${conclusion}`,
      )}
    </span>
  );
}
