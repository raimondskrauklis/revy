// frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx
import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '@/contexts/AuthContext';
import { FindingRow } from '@/features/reviewer/components/FindingRow';
import { MergeReadinessBadge } from '@/features/reviewer/components/MergeReadinessBadge';
import {
  usePublishJob,
  usePullRequest,
  useReconciledFindings,
  useReviewRun,
} from '@/features/reviewer/hooks';
import { deriveMergeConclusion, pickLatestRevisionId } from '@/features/reviewer/mergeConclusion';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function PullRequestDetailPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { repoId, prId } = useParams<{ repoId: string; prId: string }>();

  const {
    items: reconciledFindings,
    isLoading: loadingFindings,
    error: findingsError,
    ref,
  } = useReconciledFindings(workspaceId, repoId, prId);

  const { data: pullRequest } = usePullRequest(workspaceId, repoId, prId);

  const revisionId = useMemo(
    () => pickLatestRevisionId(reconciledFindings),
    [reconciledFindings],
  );

  const { data: reviewRun, error: reviewRunError } = useReviewRun(
    workspaceId,
    repoId,
    prId,
    revisionId,
  );

  const { data: publishJob, error: publishError } = usePublishJob(
    workspaceId,
    repoId,
    prId,
    revisionId,
  );

  const mergeConclusion = useMemo(
    () => deriveMergeConclusion(reconciledFindings),
    [reconciledFindings],
  );

  const published = publishJob?.status === 'completed';

  useEffect(() => {
    const error = findingsError ?? reviewRunError ?? publishError;
    if (error) {
      showDomainErrorToast(mapApiError(error));
    }
  }, [findingsError, reviewRunError, publishError]);

  if (!workspaceId || !repoId || !prId) {
    return (
      <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.noWorkspace')}</p>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center gap-3">
        {pullRequest?.html_url ? (
          <a
            href={pullRequest.html_url}
            target="_blank"
            rel="noreferrer"
            className="text-sm text-[color:var(--app-link)] hover:underline"
          >
            {t('reviewer.viewOnGitHub')}
          </a>
        ) : null}
        <MergeReadinessBadge conclusion={mergeConclusion} published={published} />
        {reviewRun ? (
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('reviewer.reviewRun.status', {
              status: t(`reviewer.reviewRun.${reviewRun.status}`),
            })}
          </span>
        ) : (
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('reviewer.reviewRun.none')}
          </span>
        )}
        {publishJob ? (
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('reviewer.publish.status', {
              status: t(`reviewer.publish.${publishJob.status}`),
            })}
          </span>
        ) : null}
      </div>

      {loadingFindings ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : reconciledFindings.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.findings.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-lg ring-1 ring-[color:var(--app-ring)]">
          <table className="min-w-full text-left text-sm">
            <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              <tr>
                <th className="px-3 py-2 font-medium">{t('reviewer.findings.severity')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.findings.category')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.findings.title')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.findings.file')}</th>
                <th className="px-3 py-2 font-medium">{t('reviewer.findings.message')}</th>
              </tr>
            </thead>
            <tbody>
              {reconciledFindings.map((finding) => (
                <FindingRow key={finding.id} finding={finding} />
              ))}
            </tbody>
          </table>
          <div ref={ref} className="h-4" />
        </div>
      )}
    </div>
  );
}
