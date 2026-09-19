// frontend/src/features/reviewer/components/FindingRow.tsx
import { useTranslation } from 'react-i18next';
import type { FindingSeverity, ReconciledFinding } from '@/features/reviewer/types';

interface FindingRowProps {
  finding: ReconciledFinding;
  canDismiss?: boolean;
  onDismiss?: (groupId: string) => void;
  dismissPending?: boolean;
}

const SEVERITY_SHAPE_CLASS: Record<FindingSeverity, string> = {
  info: 'h-2.5 w-2.5 rounded-full bg-[color:var(--app-info)]',
  warning:
    'h-0 w-0 border-x-[5px] border-x-transparent border-b-[9px] border-b-[color:var(--app-warning)]',
  error: 'h-2.5 w-2.5 bg-[color:var(--app-danger)]',
  critical: 'h-2.5 w-2.5 rotate-45 bg-[color:var(--app-danger)]',
};

function resolutionBadgeKey(finding: ReconciledFinding): string | null {
  if (finding.resolution_method) {
    return `reviewer.resolution.method.${finding.resolution_method}`;
  }
  if (finding.resolution_status) {
    return `reviewer.resolution.status.${finding.resolution_status}`;
  }
  return null;
}

export function FindingRow({
  finding,
  canDismiss = false,
  onDismiss,
  dismissPending = false,
}: FindingRowProps) {
  const { t } = useTranslation();
  const resolutionKey = resolutionBadgeKey(finding);
  const showDismiss =
    canDismiss && finding.state === 'active' && typeof onDismiss === 'function';

  return (
    <tr className="border-t border-[color:var(--app-ring)]">
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-strong)]">
        <span className="inline-flex items-center gap-2">
          <span
            aria-hidden
            data-severity-shape={finding.severity}
            className={`inline-block shrink-0 ${SEVERITY_SHAPE_CLASS[finding.severity]}`}
          />
          <span>{t(`reviewer.severity.${finding.severity}`)}</span>
        </span>
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-muted)]">
        {t(`reviewer.category.${finding.category}`)}
      </td>
      <td className="px-3 py-2 text-sm text-[color:var(--app-text-muted)]">
        <div className="flex flex-col gap-1">
          <span>{t(`reviewer.groupState.${finding.state}`)}</span>
          {resolutionKey ? (
            <span className="inline-flex w-fit rounded-[var(--app-radius-sm)] px-1.5 py-0.5 text-xs bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              {t(resolutionKey)}
            </span>
          ) : null}
        </div>
      </td>
      <td className="px-3 py-2 text-sm font-sans text-[color:var(--app-text-strong)]">
        {finding.title}
      </td>
      <td className="px-3 py-2 text-sm font-mono text-[color:var(--app-text-muted)]">
        {finding.file_path ?? '—'}
      </td>
      <td
        className="max-w-0 truncate px-3 py-2 text-sm font-sans text-[color:var(--app-text-muted)]"
        title={finding.message}
      >
        {finding.message}
      </td>
      <td className="px-3 py-2 text-sm">
        {showDismiss ? (
          <button
            type="button"
            className="text-[color:var(--app-link)] hover:underline disabled:opacity-50"
            disabled={dismissPending}
            onClick={() => onDismiss(finding.id)}
          >
            {t('reviewer.resolution.dismiss')}
          </button>
        ) : (
          <span className="text-[color:var(--app-text-muted)]">—</span>
        )}
      </td>
    </tr>
  );
}
