// frontend/src/features/reviewer/components/FindingDetailSheet.tsx
import { useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { X } from 'lucide-react';
import type { ReconciledFinding, ReviewFinding } from '@/features/reviewer/types';
import { useRevisionFindings } from '@/features/reviewer/hooks';

interface FindingDetailSheetProps {
  finding: ReconciledFinding | null;
  workspaceId: string;
  repoId: string;
  prId: string;
  revisionId: string | null;
  onClose: () => void;
  canDismiss: boolean;
  dismissPending: boolean;
  onDismiss: (groupId: string) => void;
}

export function FindingDetailSheet({
  finding,
  workspaceId,
  repoId,
  prId,
  revisionId,
  onClose,
  canDismiss,
  dismissPending,
  onDismiss,
}: FindingDetailSheetProps) {
  const { t } = useTranslation();

  const { data: findings } = useRevisionFindings(
    finding ? workspaceId : null,
    finding ? repoId : null,
    finding ? prId : null,
    finding ? revisionId : null,
  );
  const detail: ReviewFinding | undefined = finding
    ? findings?.find((d) => d.id === finding.id)
    : undefined;

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    },
    [onClose],
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [handleKeyDown]);

  if (!finding) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={onClose} aria-hidden />

      {/* Sheet */}
      <div className="relative w-full max-w-lg bg-[color:var(--app-surface)] shadow-xl overflow-y-auto">
        <div className="sticky top-0 z-10 flex items-center justify-between border-b border-[color:var(--app-ring)] bg-[color:var(--app-surface)] px-4 py-3">
          <h2 className="text-lg font-semibold text-[color:var(--app-text-strong)]">
            {finding.title}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-9 w-9 items-center justify-center rounded-[var(--app-radius-md)] text-[color:var(--app-text-muted)] hover:bg-[color:var(--app-chip)] focus-visible:ring-2 ring-[color:var(--app-ring-strong)]"
            aria-label={t('sidebar.close')}
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="space-y-4 p-4">
          {/* Badges row */}
          <div className="flex flex-wrap gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-[color:var(--app-chip)] px-2 py-0.5 text-xs font-medium text-[color:var(--app-text-muted)]">
              {t(`reviewer.findings.${finding.severity}`)}
            </span>
            <span className="rounded-full bg-[color:var(--app-chip)] px-2 py-0.5 text-xs text-[color:var(--app-text-muted)]">
              {finding.category}
            </span>
            <span className="rounded-full bg-[color:var(--app-chip)] px-2 py-0.5 text-xs text-[color:var(--app-text-muted)]">
              {finding.state}
            </span>
          </div>

          {/* File + line range */}
          {detail?.file_path && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--app-text-muted)]">
                {t('reviewer.detail.file')}
              </p>
              <code className="mt-1 block rounded-[var(--app-radius-sm)] bg-[color:var(--app-chip)] px-2 py-1 text-sm text-[color:var(--app-text-strong)]">
                {detail.file_path}
                {detail.start_line && detail.end_line && (
                  <span className="text-[color:var(--app-text-muted)]">
                    {' '}
                    (L{detail.start_line}–L{detail.end_line})
                  </span>
                )}
              </code>
            </div>
          )}

          {/* Full message */}
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--app-text-muted)]">
              {t('reviewer.detail.message')}
            </p>
            <p className="mt-1 whitespace-pre-wrap text-sm text-[color:var(--app-text-strong)]">
              {finding.message}
            </p>
          </div>

          {/* Suggestion / remediation */}
          {detail?.suggestion && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--app-text-muted)]">
                {t('reviewer.detail.suggestion')}
              </p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-[color:var(--app-text-strong)]">
                {detail.suggestion}
              </p>
            </div>
          )}

          {/* Created date */}
          {detail && (
            <div>
              <p className="text-xs font-medium uppercase tracking-wide text-[color:var(--app-text-muted)]">
                {t('reviewer.detail.history')}
              </p>
              <p className="mt-1 text-sm text-[color:var(--app-text-muted)]">
                {t('reviewer.detail.firstSeen', {
                  revision: revisionId ? revisionId.slice(0, 7) : '—',
                })}
              </p>
            </div>
          )}

          {/* Dismiss button */}
          {canDismiss && finding.state === 'active' && (
            <div>
              <button
                type="button"
                disabled={dismissPending}
                onClick={() => onDismiss(finding.id)}
                className="w-full rounded-[var(--app-radius-md)] bg-[color:var(--app-danger)] px-4 py-2 text-sm font-medium text-white hover:opacity-90 disabled:opacity-50"
              >
                {t('reviewer.detail.dismiss')}
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}