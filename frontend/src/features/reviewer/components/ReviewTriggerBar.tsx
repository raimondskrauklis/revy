// frontend/src/features/reviewer/components/ReviewTriggerBar.tsx
import { useTranslation } from 'react-i18next';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Button } from '@/components/ui/button';
import { reviewerQueryKeys } from '@/features/reviewer/hooks';
import { IndexWaitError, triggerReviewWithFullIndexRetry } from '@/features/reviewer/triggerReview';
import type { ReviewProfile } from '@/features/reviewer/types';
import { mapApiError, notify, showDomainErrorToast } from '@/shared/errors';

interface ReviewTriggerBarProps {
  workspaceId: string;
  repositoryId: string;
  pullRequestId: string;
  revisionId: string;
  reviewInFlight: boolean;
}

export function ReviewTriggerBar({
  workspaceId,
  repositoryId,
  pullRequestId,
  revisionId,
  reviewInFlight,
}: ReviewTriggerBarProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const triggerMutation = useMutation({
    mutationFn: (profile: ReviewProfile) =>
      triggerReviewWithFullIndexRetry(
        { workspaceId, repositoryId, pullRequestId, revisionId },
        profile,
      ),
    onSuccess: async (_run, profile) => {
      notify.success(
        t('reviewer.reviewRun.triggered', {
          profile: t(`reviewer.reviewRun.profiles.${profile}`),
        }),
      );
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: reviewerQueryKeys.reviewRun(
            workspaceId,
            repositoryId,
            pullRequestId,
            revisionId,
          ),
        }),
        queryClient.invalidateQueries({
          queryKey: reviewerQueryKeys.reconciled(workspaceId, repositoryId, pullRequestId),
        }),
        queryClient.invalidateQueries({
          queryKey: reviewerQueryKeys.publishJob(
            workspaceId,
            repositoryId,
            pullRequestId,
            revisionId,
          ),
        }),
      ]);
    },
    onError: (error) => {
      if (error instanceof IndexWaitError) {
        showDomainErrorToast({
          code: 'service_unavailable',
          message: error.message,
          severity: 'error',
          title: t('reviewer.reviewRun.indexFailed'),
          description: error.message,
        });
        return;
      }
      showDomainErrorToast(mapApiError(error));
    },
  });

  const busy = reviewInFlight || triggerMutation.isPending;
  const profiles: ReviewProfile[] = ['deep', 'critical'];

  return (
    <div className="flex flex-wrap items-center gap-2">
      {profiles.map((profile) => (
        <Button
          key={profile}
          type="button"
          variant={profile === 'deep' ? 'default' : 'outline'}
          className="min-h-11"
          disabled={busy}
          onClick={() => triggerMutation.mutate(profile)}
        >
          {triggerMutation.isPending && triggerMutation.variables === profile
            ? t('reviewer.reviewRun.indexing')
            : t(`reviewer.reviewRun.trigger.${profile}`)}
        </Button>
      ))}
    </div>
  );
}
