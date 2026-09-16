// frontend/src/features/reviewer/api.ts
import apiClient, { parseSuccess } from '@/lib/api';
import type { CursorPage } from '@/hooks/useInfiniteList';
import type {
  GitHubPullRequest,
  GitHubRepository,
  IndexJob,
  PublishJob,
  ReconciledFinding,
  ReviewFinding,
  ReviewProfile,
  ReviewRun,
} from '@/features/reviewer/types';

interface OffsetPage<T> {
  items: T[];
  offset: number;
  limit: number;
  has_more: boolean;
}

export async function fetchInstallationRepositories(
  workspaceId: string,
  installationId: string,
  cursor?: string | null,
): Promise<CursorPage<GitHubRepository>> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/installations/${installationId}/repositories`,
    { params: { cursor: cursor ?? undefined, limit: 50 } },
  );
  return await parseSuccess<CursorPage<GitHubRepository>>(response);
}

export async function fetchPullRequest(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
): Promise<GitHubPullRequest> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}`,
  );
  return await parseSuccess<GitHubPullRequest>(response);
}

export async function fetchPullRequests(
  workspaceId: string,
  repositoryId: string,
  cursor?: string | null,
): Promise<CursorPage<GitHubPullRequest>> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests`,
    { params: { cursor: cursor ?? undefined, limit: 50 } },
  );
  return await parseSuccess<CursorPage<GitHubPullRequest>>(response);
}

export async function fetchReconciledFindings(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  cursor?: string | null,
): Promise<CursorPage<ReconciledFinding>> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/findings/reconciled`,
    { params: { cursor: cursor ?? undefined, limit: 50 } },
  );
  return await parseSuccess<CursorPage<ReconciledFinding>>(response);
}

export async function dismissFindingGroup(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  groupId: string,
  reason?: string,
): Promise<ReconciledFinding> {
  const response = await apiClient.post(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/finding-groups/${groupId}/dismiss`,
    { reason: reason ?? null },
  );
  return await parseSuccess<ReconciledFinding>(response);
}

export async function fetchReviewRun(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  revisionId: string,
): Promise<ReviewRun | null> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/revisions/${revisionId}/review-run`,
  );
  return await parseSuccess<ReviewRun | null>(response);
}

export async function fetchRevisionFindings(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  revisionId: string,
): Promise<ReviewFinding[]> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/revisions/${revisionId}/findings`,
  );
  const page = await parseSuccess<OffsetPage<ReviewFinding>>(response);
  return page.items;
}

export async function fetchPublishJob(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  revisionId: string,
): Promise<PublishJob | null> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/revisions/${revisionId}/publish-job`,
  );
  return await parseSuccess<PublishJob | null>(response);
}

export async function triggerReview(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  revisionId: string,
  profile: ReviewProfile,
): Promise<ReviewRun> {
  const response = await apiClient.post(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/revisions/${revisionId}/review`,
    { profile },
  );
  return await parseSuccess<ReviewRun>(response);
}

export async function fetchIndexJob(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
  revisionId: string,
  jobId?: string,
): Promise<IndexJob | null> {
  const response = await apiClient.get(
    `/workspaces/${workspaceId}/repositories/${repositoryId}/pull-requests/${pullRequestId}/revisions/${revisionId}/index-job`,
    { params: jobId ? { job_id: jobId } : undefined },
  );
  return await parseSuccess<IndexJob | null>(response);
}

/** Probe whether reviewer APIs are available for the workspace. */
export async function probeReviewerApi(
  workspaceId: string,
  repositoryId: string,
  pullRequestId: string,
): Promise<boolean> {
  try {
    await fetchReconciledFindings(workspaceId, repositoryId, pullRequestId, null);
    return true;
  } catch {
    return false;
  }
}
