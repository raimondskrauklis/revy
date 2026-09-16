// frontend/src/features/reviewer/triggerReview.ts
import { fetchIndexJob, triggerReview } from '@/features/reviewer/api';
import type { ReviewProfile, ReviewRun } from '@/features/reviewer/types';
import { mapApiError } from '@/shared/errors';

export const FULL_INDEX_REQUIRED = 'full_index_required';

export const INDEX_POLL_MS = 2_000;
export const INDEX_POLL_ATTEMPTS = 90;
export const FULL_INDEX_TRIGGER_ROUNDS = 5;

export class IndexWaitError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'IndexWaitError';
  }
}

interface TriggerReviewIds {
  workspaceId: string;
  repositoryId: string;
  pullRequestId: string;
  revisionId: string;
}

export interface TriggerReviewDeps {
  trigger: typeof triggerReview;
  fetchIndex: typeof fetchIndexJob;
  sleep: (ms: number) => Promise<void>;
  pollAttempts: number;
}

const defaultDeps: TriggerReviewDeps = {
  trigger: triggerReview,
  fetchIndex: fetchIndexJob,
  sleep: (ms) => new Promise((resolve) => setTimeout(resolve, ms)),
  pollAttempts: INDEX_POLL_ATTEMPTS,
};

function indexJobIdFromError(error: unknown): string | undefined {
  const raw = mapApiError(error).details?.index_job_id;
  return typeof raw === 'string' && raw.trim() ? raw : undefined;
}

async function waitForCompletedFullIndex(
  ids: TriggerReviewIds,
  deps: TriggerReviewDeps,
  indexJobId?: string,
): Promise<void> {
  for (let attempt = 0; attempt < deps.pollAttempts; attempt += 1) {
    const job = await deps.fetchIndex(
      ids.workspaceId,
      ids.repositoryId,
      ids.pullRequestId,
      ids.revisionId,
      indexJobId,
    );
    if (job?.status === 'completed' && job.index_mode === 'full') {
      return;
    }
    if (job?.status === 'failed') {
      throw new IndexWaitError(job.error_message ?? 'Full-repo index failed');
    }
    await deps.sleep(INDEX_POLL_MS);
  }
  throw new IndexWaitError('Timed out waiting for full-repo index');
}

export async function triggerReviewWithFullIndexRetry(
  ids: TriggerReviewIds,
  profile: ReviewProfile,
  deps: TriggerReviewDeps = defaultDeps,
): Promise<ReviewRun> {
  let lastError: unknown;
  for (let round = 0; round < FULL_INDEX_TRIGGER_ROUNDS; round += 1) {
    try {
      return await deps.trigger(
        ids.workspaceId,
        ids.repositoryId,
        ids.pullRequestId,
        ids.revisionId,
        profile,
      );
    } catch (error) {
      lastError = error;
      if (mapApiError(error).code !== FULL_INDEX_REQUIRED) {
        throw error;
      }
      await waitForCompletedFullIndex(ids, deps, indexJobIdFromError(error));
    }
  }
  if (lastError instanceof Error) {
    throw lastError;
  }
  throw new IndexWaitError('Timed out waiting for full-repo index');
}
