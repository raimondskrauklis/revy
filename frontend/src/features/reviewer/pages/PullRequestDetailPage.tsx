// frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx
import { useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '@/contexts/AuthContext';
import { dismissFindingGroup } from '@/features/reviewer/api';
import { FindingRow } from '@/features/reviewer/components/FindingRow';
import { JudgeSkippedBadge } from '@/features/reviewer/components/JudgeSkippedBadge';
import { MergeReadinessBadge } from '@/features/reviewer/components/MergeReadinessBadge';
import { PullRequestStateBadge } from '@/features/reviewer/components/PullRequestStateBadge';
import { ReviewTriggerBar } from '@/features/reviewer/components/ReviewTriggerBar';
import {
  reviewerQueryKeys,
  usePublishJob,
  usePullRequest,
  useReconciledFindings,
  useReviewRun,
} from '@/features/reviewer/hooks';
import { deriveMergeConclusion, pickLatestRevisionId } from '@/features/reviewer/mergeConclusion';
import { hasPermission } from '@/lib/permissions';
import { mapApiError } from '@/shared/errors';
import { showDomainErrorToast } from '@/shared/errors/toasts';

export function PullRequestDetailPage() {
  const { t } = useTranslation();
  const { user } = useAuth();
  const workspaceId = user?.workspace_id ?? null;
  const { repoId, prId } = useParams<{ repoId: string; prId: string }>();
  const queryClient = useQueryClient();
  const canDismiss = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );
  const canTriggerReview = hasPermission(
    user?.role ?? undefined,
    'admin:users',
    user?.platform_role ?? undefined,
  );

  const dismissMutation = useMutation({
    mutationFn: (groupId: string) =>
      dismissFindingGroup(workspaceId!, repoId!, prId!, groupId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({
        queryKey: reviewerQueryKeys.reconciled(workspaceId ?? '', repoId ?? '', prId ?? ''),
      });
    },
    onError: (error) => {
      showDomainErrorToast(mapApiError(error));
    },
  });

  const {
    items: reconciledFindings,
    isLoading: loadingFindings,
    error: findingsError,
    ref,
  } = useReconciledFindings(workspaceId, repoId, prId);

  const { data: pullRequest } = usePullRequest(workspaceId, repoId, prId);

  const revisionId = useMemo(
    () => pullRequest?.latest_revision_id ?? pickLatestRevisionId(reconciledFindings),
    [pullRequest?.latest_revision_id, reconciledFindings],
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

  const reviewInFlight =
    reviewRun?.status === 'pending' || reviewRun?.status === 'processing';

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
        {pullRequest ? <PullRequestStateBadge pullRequest={pullRequest} /> : null}
        <MergeReadinessBadge
          conclusion={mergeConclusion}
          published={published}
          prOpen={pullRequest?.state !== 'closed'}
        />
        {reviewRun?.status === 'completed' &&
        (reviewRun.judge_status === 'skipped_disabled' ||
          reviewRun.judge_status === 'skipped_unavailable') ? (
          <JudgeSkippedBadge judgeStatus={reviewRun.judge_status} />
        ) : null}
        {reviewRun ? (
          <span className="text-sm text-[color:var(--app-text-muted)]">
            {t('reviewer.reviewRun.status', {
              status: t(`reviewer.reviewRun.${reviewRun.status}`),
            })}
            {` · ${t(`reviewer.reviewRun.profiles.${reviewRun.profile}`)}`}
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
        {canTriggerReview && revisionId ? (
          <ReviewTriggerBar
            workspaceId={workspaceId}
            repositoryId={repoId}
            pullRequestId={prId}
            revisionId={revisionId}
            reviewInFlight={reviewInFlight}
          />
        ) : null}
      </div>

      {loadingFindings ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('common.loading')}</p>
      ) : reconciledFindings.length === 0 ? (
        <p className="text-sm text-[color:var(--app-text-muted)]">{t('reviewer.findings.empty')}</p>
      ) : (
        <div className="overflow-x-auto rounded-[var(--app-radius-sm)] shadow-[inset_0_0_0_1px_var(--app-ring)]">
          <table className="min-w-full table-fixed text-left text-sm">
            <thead className="bg-[color:var(--app-chip)] text-[color:var(--app-text-muted)]">
              <tr>
                <th className="w-[12%] px-3 py-2 font-medium">{t('reviewer.findings.severity')}</th>
                <th className="w-[10%] px-3 py-2 font-medium">{t('reviewer.findings.category')}</th>
                <th className="w-[12%] px-3 py-2 font-medium">{t('reviewer.findings.state')}</th>
                <th className="w-[20%] px-3 py-2 font-medium">{t('reviewer.findings.title')}</th>
                <th className="w-[16%] px-3 py-2 font-medium">{t('reviewer.findings.file')}</th>
                <th className="w-[22%] px-3 py-2 font-medium">{t('reviewer.findings.message')}</th>
                <th className="w-[8%] px-3 py-2 font-medium">{t('reviewer.findings.actions')}</th>
              </tr>
            </thead>
            <tbody>
              {reconciledFindings.map((finding) => (
                <FindingRow
                  key={finding.id}
                  finding={finding}
                  canDismiss={canDismiss}
                  dismissPending={dismissMutation.isPending}
                  onDismiss={(groupId) => dismissMutation.mutate(groupId)}
                />
              ))}
            </tbody>
          </table>
          <div ref={ref} className="h-4" />
        </div>
      )}
    </div>
  );
}
