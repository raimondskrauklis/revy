// frontend/src/features/reviewer/pullRequestLifecycle.ts
import type { GitHubPullRequest, PullRequestLifecycle } from '@/features/reviewer/types';

export function pullRequestLifecycle(
  pullRequest: Pick<GitHubPullRequest, 'state' | 'merged'>,
): PullRequestLifecycle {
  if (pullRequest.merged) {
    return 'merged';
  }
  return pullRequest.state;
}
