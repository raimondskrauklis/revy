// frontend/src/features/reviewer/triggerReview.test.ts
import { AxiosError } from 'axios';
import { describe, expect, it, vi } from 'vitest';
import type { IndexJob, ReviewRun } from '@/features/reviewer/types';
import {
  FULL_INDEX_REQUIRED,
  triggerReviewWithFullIndexRetry,
} from '@/features/reviewer/triggerReview';

const ids = {
  workspaceId: 'ws',
  repositoryId: 'repo',
  pullRequestId: 'pr',
  revisionId: 'rev',
};

function reviewRun(): ReviewRun {
  return {
    id: 'run-1',
    revision_id: ids.revisionId,
    workspace_id: ids.workspaceId,
    status: 'pending',
    profile: 'deep',
    provider: 'rtu',
    error_message: null,
    judge_status: 'not_applicable',
    judge_escalation_candidate_count: 0,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

function indexJob(overrides: Partial<IndexJob>): IndexJob {
  return {
    id: 'idx-1',
    revision_id: ids.revisionId,
    workspace_id: ids.workspaceId,
    status: 'pending',
    index_mode: 'full',
    error_message: null,
    chunk_count: null,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  };
}

function conflict(code: string, details?: Record<string, unknown>): AxiosError {
  return new AxiosError('conflict', 'ERR_BAD_REQUEST', undefined, undefined, {
    status: 409,
    data: { error: code, message: 'Full-repo index required', details },
    statusText: 'Conflict',
    headers: {},
    config: { headers: {} },
  } as never);
}

describe('triggerReviewWithFullIndexRetry', () => {
  it('returns on first success', async () => {
    const run = reviewRun();
    const trigger = vi.fn().mockResolvedValue(run);
    const result = await triggerReviewWithFullIndexRetry(ids, 'deep', {
      trigger,
      fetchIndex: vi.fn(),
      sleep: vi.fn(),
      pollAttempts: 2,
    });
    expect(result).toBe(run);
    expect(trigger).toHaveBeenCalledTimes(1);
  });

  it('waits for full index after full_index_required then retries', async () => {
    const run = reviewRun();
    const trigger = vi
      .fn()
      .mockRejectedValueOnce(conflict(FULL_INDEX_REQUIRED, { index_job_id: 'idx-1' }))
      .mockResolvedValueOnce(run);
    const fetchIndex = vi
      .fn()
      .mockResolvedValueOnce(indexJob({ status: 'processing' }))
      .mockResolvedValueOnce(indexJob({ status: 'completed' }));
    const sleep = vi.fn().mockResolvedValue(undefined);

    await expect(
      triggerReviewWithFullIndexRetry(ids, 'deep', {
        trigger,
        fetchIndex,
        sleep,
        pollAttempts: 5,
      }),
    ).resolves.toBe(run);
    expect(trigger).toHaveBeenCalledTimes(2);
    expect(fetchIndex).toHaveBeenCalledTimes(2);
    expect(fetchIndex).toHaveBeenNthCalledWith(1, 'ws', 'repo', 'pr', 'rev', 'idx-1');
    expect(sleep).toHaveBeenCalledTimes(1);
  });

  it('waits on a later full_index_required job id after a newer index is enqueued', async () => {
    const run = reviewRun();
    const trigger = vi
      .fn()
      .mockRejectedValueOnce(conflict(FULL_INDEX_REQUIRED, { index_job_id: 'idx-1' }))
      .mockRejectedValueOnce(conflict(FULL_INDEX_REQUIRED, { index_job_id: 'idx-2' }))
      .mockResolvedValueOnce(run);
    const fetchIndex = vi
      .fn()
      .mockResolvedValueOnce(indexJob({ id: 'idx-1', status: 'completed' }))
      .mockResolvedValueOnce(indexJob({ id: 'idx-2', status: 'completed' }));

    await expect(
      triggerReviewWithFullIndexRetry(ids, 'deep', {
        trigger,
        fetchIndex,
        sleep: vi.fn(),
        pollAttempts: 5,
      }),
    ).resolves.toBe(run);
    expect(trigger).toHaveBeenCalledTimes(3);
    expect(fetchIndex).toHaveBeenNthCalledWith(1, 'ws', 'repo', 'pr', 'rev', 'idx-1');
    expect(fetchIndex).toHaveBeenNthCalledWith(2, 'ws', 'repo', 'pr', 'rev', 'idx-2');
  });

  it('rethrows unrelated conflicts', async () => {
    const trigger = vi.fn().mockRejectedValue(conflict('index_in_progress'));
    await expect(
      triggerReviewWithFullIndexRetry(ids, 'critical', {
        trigger,
        fetchIndex: vi.fn(),
        sleep: vi.fn(),
        pollAttempts: 1,
      }),
    ).rejects.toMatchObject({ response: { status: 409 } });
    expect(trigger).toHaveBeenCalledTimes(1);
  });
});
