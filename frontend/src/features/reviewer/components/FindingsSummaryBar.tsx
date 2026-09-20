// frontend/src/features/reviewer/components/FindingsSummaryBar.tsx
import { useTranslation } from 'react-i18next';
import type { ReconciledFinding } from '@/features/reviewer/types';

interface SeverityCounts {
  critical: number;
  error: number;
  warning: number;
  info: number;
  active: number;
  dismissed: number;
}

function computeCounts(findings: ReconciledFinding[]): SeverityCounts {
  const counts: SeverityCounts = { critical: 0, error: 0, warning: 0, info: 0, active: 0, dismissed: 0 };
  for (const f of findings) {
    counts[f.severity]++;
    if (f.state === 'active') {
      counts.active++;
    } else {
      counts.dismissed++;
    }
  }
  return counts;
}

interface FindingsSummaryBarProps {
  findings: ReconciledFinding[];
  conclusion: string;
}

export function FindingsSummaryBar({ findings, conclusion }: FindingsSummaryBarProps) {
  const { t } = useTranslation();
  const counts = computeCounts(findings);

  const parts: string[] = [];
  if (counts.critical > 0) parts.push(t('reviewer.summary.criticalCount', { count: counts.critical }));
  if (counts.error > 0) parts.push(t('reviewer.summary.errorCount', { count: counts.error }));
  if (counts.warning > 0) parts.push(t('reviewer.summary.warningCount', { count: counts.warning }));
  if (counts.info > 0) parts.push(t('reviewer.summary.infoCount', { count: counts.info }));

  let nextAction: string;
  if (findings.length === 0) {
    nextAction = t('reviewer.summary.noFindings');
  } else if (conclusion === 'failure') {
    nextAction = t('reviewer.summary.nextAction.blocked', {
      blocking: counts.critical + counts.error,
    });
  } else if (conclusion === 'neutral') {
    nextAction = t('reviewer.summary.nextAction.needsReview', {
      blocking: counts.warning,
    });
  } else {
    nextAction = t('reviewer.summary.nextAction.ready');
  }

  return (
    <div className="sticky top-0 z-10 rounded-[var(--app-radius-md)] bg-[color:var(--app-surface)] border border-[color:var(--app-ring)] px-4 py-3 space-y-1 shadow-sm">
      <div className="flex flex-wrap items-center gap-x-2 gap-y-1 text-sm">
        {parts.map((part) => (
          <span key={part}>{part}</span>
        ))}
        {counts.dismissed > 0 && (
          <span className="text-[color:var(--app-text-muted)]">
            {t('reviewer.summary.dismissedCount', { count: counts.dismissed })}
          </span>
        )}
      </div>
      <p className="text-sm text-[color:var(--app-text-muted)]">{nextAction}</p>
    </div>
  );
}