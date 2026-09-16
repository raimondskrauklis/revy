// frontend/src/features/reviewer/components/ReviewTriggerBar.test.tsx
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { ReviewTriggerBar } from '@/features/reviewer/components/ReviewTriggerBar';
import * as triggerReview from '@/features/reviewer/triggerReview';

vi.mock('@/features/reviewer/triggerReview', async () => {
  const actual = await vi.importActual<typeof triggerReview>(
    '@/features/reviewer/triggerReview',
  );
  return {
    ...actual,
    triggerReviewWithFullIndexRetry: vi.fn(),
  };
});

function renderBar(reviewInFlight = false) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <ReviewTriggerBar
        workspaceId="ws"
        repositoryId="repo"
        pullRequestId="pr"
        revisionId="rev"
        reviewInFlight={reviewInFlight}
      />
    </QueryClientProvider>,
  );
}

describe('ReviewTriggerBar', () => {
  it('queues a deep review', async () => {
    const trigger = vi.mocked(triggerReview.triggerReviewWithFullIndexRetry);
    trigger.mockResolvedValue({
      id: 'run',
      revision_id: 'rev',
      workspace_id: 'ws',
      status: 'pending',
      profile: 'deep',
      provider: null,
      error_message: null,
      judge_status: 'not_applicable',
      judge_escalation_candidate_count: 0,
      created_at: '2026-01-01T00:00:00Z',
      updated_at: '2026-01-01T00:00:00Z',
    });

    renderBar();
    fireEvent.click(screen.getByRole('button', { name: 'Deep review' }));
    await waitFor(() => {
      expect(trigger).toHaveBeenCalledWith(
        {
          workspaceId: 'ws',
          repositoryId: 'repo',
          pullRequestId: 'pr',
          revisionId: 'rev',
        },
        'deep',
      );
    });
  });

  it('disables buttons while a review is in flight', () => {
    renderBar(true);
    expect(screen.getByRole('button', { name: 'Deep review' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Critical review' })).toBeDisabled();
  });
});
