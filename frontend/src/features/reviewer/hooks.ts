// frontend/src/features/reviewer/hooks.ts
import { useQuery } from '@tanstack/react-query';
import { useInfiniteList } from '@/hooks/useInfiniteList';
import { fetchInstallations } from '@/features/installations/api';
import {
  fetchInstallationRepositories,
  fetchPublishJob,
  fetchPullRequest,
  fetchPullRequests,
  fetchReconciledFindings,
  fetchReviewRun,
  fetchRevisionFindings,
  probeReviewerApi,
} from '@/features/reviewer/api';
import type { GitHubPullRequest } from '@/features/reviewer/types';

/** Cap list scans until GET …/pull-requests/{id} exists (R7.1 / R8). */
export const MAX_PULL_REQUEST_SCAN_PAGES = 50;

export const reviewerQueryKeys = {
  repositories: (workspaceId: string, installationId: string) =>
    ['reviewer', 'repositories', workspaceId, installationId] as const,
  pullRequests: (workspaceId: string, repositoryId: string) =>
    ['reviewer', 'pullRequests', workspaceId, repositoryId] as const,
  pullRequest: (workspaceId: string, repositoryId: string, pullRequestId: string) =>
    ['reviewer', 'pullRequest', workspaceId, repositoryId, pullRequestId] as const,
  reconciled: (workspaceId: string, repositoryId: string, pullRequestId: string) =>
    ['reviewer', 'reconciled', workspaceId, repositoryId, pullRequestId] as const,
  reviewRun: (
    workspaceId: string,
    repositoryId: string,
    pullRequestId: string,
    revisionId: string,
  ) => ['reviewer', 'reviewRun', workspaceId, repositoryId, pullRequestId, revisionId] as const,
  findings: (
    workspaceId: string,
    repositoryId: string,
    pullRequestId: string,
    revisionId: string,
  ) => ['reviewer', 'findings', workspaceId, repositoryId, pullRequestId, revisionId] as const,
  publishJob: (
    workspaceId: string,
    repositoryId: string,
    pullRequestId: string,
    revisionId: string,
  ) => ['reviewer', 'publishJob', workspaceId, repositoryId, pullRequestId, revisionId] as const,
  availability: (workspaceId: string) => ['reviewer', 'availability', workspaceId] as const,
};

export async function findPullRequestInList(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
): Promise<GitHubPullRequest | null> {
  let cursor: string | null = null;
  for (let page = 0; page < MAX_PULL_REQUEST_SCAN_PAGES; page += 1) {
    const result = await fetchPullRequests(workspaceId, repositoryId, cursor);
    const found = result.items.find((item) => item.id === pullRequestId);
    if (found) {
      return found;
    }
    if (!result.cursor.has_next || !result.cursor.next_cursor) {
      return null;
    }
    cursor = result.cursor.next_cursor;
  }
  return null;
}

export function useInstallationRepositories(
  workspaceId: string | null | undefined,
  installationId: string | null | undefined,
) {
  return useInfiniteList({
    queryKey: [...reviewerQueryKeys.repositories(workspaceId ?? '', installationId ?? '')],
    queryFn: (cursor) => fetchInstallationRepositories(workspaceId!, installationId!, cursor),
    enabled: Boolean(workspaceId && installationId),
  });
}

export function usePullRequests(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
) {
  return useInfiniteList({
    queryKey: [...reviewerQueryKeys.pullRequests(workspaceId ?? '', repositoryId ?? '')],
    queryFn: (cursor) => fetchPullRequests(workspaceId!, repositoryId!, cursor),
    enabled: Boolean(workspaceId && repositoryId),
  });
}

export function usePullRequest(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
  pullRequestId: string | null | undefined,
) {
  return useQuery({
    queryKey: reviewerQueryKeys.pullRequest(
      workspaceId ?? '',
      repositoryId ?? '',
      pullRequestId ?? '',
    ),
    queryFn: () => fetchPullRequest(workspaceId!, repositoryId!, pullRequestId!),
    enabled: Boolean(workspaceId && repositoryId && pullRequestId),
  });
}

export function useReconciledFindings(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
  pullRequestId: string | null | undefined,
) {
  return useInfiniteList({
    queryKey: [
      ...reviewerQueryKeys.reconciled(workspaceId ?? '', repositoryId ?? '', pullRequestId ?? ''),
    ],
    queryFn: (cursor) =>
      fetchReconciledFindings(workspaceId!, repositoryId!, pullRequestId!, cursor),
    enabled: Boolean(workspaceId && repositoryId && pullRequestId),
  });
}

export function useReviewRun(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
  pullRequestId: string | null | undefined,
  revisionId: string | null | undefined,
) {
  return useQuery({
    queryKey: reviewerQueryKeys.reviewRun(
      workspaceId ?? '',
      repositoryId ?? '',
      pullRequestId ?? '',
      revisionId ?? '',
    ),
    queryFn: () => fetchReviewRun(workspaceId!, repositoryId!, pullRequestId!, revisionId!),
    enabled: Boolean(workspaceId && repositoryId && pullRequestId && revisionId),
  });
}

export function useRevisionFindings(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
  pullRequestId: string | null | undefined,
  revisionId: string | null | undefined,
) {
  return useQuery({
    queryKey: reviewerQueryKeys.findings(
      workspaceId ?? '',
      repositoryId ?? '',
      pullRequestId ?? '',
      revisionId ?? '',
    ),
    queryFn: () => fetchRevisionFindings(workspaceId!, repositoryId!, pullRequestId!, revisionId!),
    enabled: Boolean(workspaceId && repositoryId && pullRequestId && revisionId),
  });
}

export function usePublishJob(
  workspaceId: string | null | undefined,
  repositoryId: string | null | undefined,
  pullRequestId: string | null | undefined,
  revisionId: string | null | undefined,
) {
  return useQuery({
    queryKey: reviewerQueryKeys.publishJob(
      workspaceId ?? '',
      repositoryId ?? '',
      pullRequestId ?? '',
      revisionId ?? '',
    ),
    queryFn: () => fetchPublishJob(workspaceId!, repositoryId!, pullRequestId!, revisionId!),
    enabled: Boolean(workspaceId && repositoryId && pullRequestId && revisionId),
  });
}

export function useReviewerAvailability(workspaceId: string | null | undefined) {
  return useQuery({
    queryKey: reviewerQueryKeys.availability(workspaceId ?? ''),
    queryFn: async () => {
      if (!workspaceId) {
        return false;
      }
      const installations = await fetchInstallations(workspaceId);
      if (installations.length === 0) {
        return false;
      }
      const repos = await fetchInstallationRepositories(workspaceId, installations[0]!.id, null);
      if (repos.items.length === 0) {
        return false;
      }
      const prs = await fetchPullRequests(workspaceId, repos.items[0]!.id, null);
      if (prs.items.length === 0) {
        return false;
      }
      return probeReviewerApi(workspaceId, repos.items[0]!.id, prs.items[0]!.id);
    },
    enabled: Boolean(workspaceId),
    staleTime: 60_000,
  });
}
