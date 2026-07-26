// frontend/src/features/reviewer/hooks.test.ts
import { afterEach, describe, expect, it, vi } from 'vitest';
import * as api from '@/features/reviewer/api';
import { findPullRequestInList, MAX_PULL_REQUEST_SCAN_PAGES } from '@/features/reviewer/hooks';
import type { GitHubPullRequest } from '@/features/reviewer/types';

function makePullRequest(id: string): GitHubPullRequest {
  return {
    id,
    repository_id: 'repo',
    workspace_id: 'ws',
    installation_id: 'inst',
    github_pull_request_id: 1,
    number: 1,
    title: 'PR',
    state: 'open',
    head_sha: 'sha',
    head_ref: 'main',
    base_ref: 'main',
    html_url: null,
    revision_count: 1,
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  };
}

describe('findPullRequestInList', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns the pull request when found on a later page', async () => {
    const target = makePullRequest('pr-2');
    vi.spyOn(api, 'fetchPullRequests')
      .mockResolvedValueOnce({
        items: [makePullRequest('pr-1')],
        cursor: { has_next: true, next_cursor: 'c1' },
      })
      .mockResolvedValueOnce({
        items: [target],
        cursor: { has_next: false, next_cursor: null },
      });

    await expect(findPullRequestInList('ws', 'repo', 'pr-2')).resolves.toBe(target);
  });

  it('stops after MAX_PULL_REQUEST_SCAN_PAGES', async () => {
    vi.spyOn(api, 'fetchPullRequests').mockResolvedValue({
      items: [makePullRequest('other')],
      cursor: { has_next: true, next_cursor: 'next' },
    });

    await expect(findPullRequestInList('ws', 'repo', 'missing')).resolves.toBeNull();
    expect(api.fetchPullRequests).toHaveBeenCalledTimes(MAX_PULL_REQUEST_SCAN_PAGES);
  });
});
