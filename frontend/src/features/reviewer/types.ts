// frontend/src/features/reviewer/types.ts
export type PullRequestState = 'open' | 'closed';

export type ReviewRunStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type GitHubReviewJudgeStatus =
  | 'not_applicable'
  | 'completed'
  | 'skipped_disabled'
  | 'skipped_unavailable';

export type PublishJobStatus = 'pending' | 'processing' | 'completed' | 'failed';

export type FindingSeverity = 'info' | 'warning' | 'error' | 'critical';

export type FindingCategory =
  | 'security'
  | 'bug'
  | 'performance'
  | 'style'
  | 'maintainability'
  | 'other';

export type FindingGroupState = 'active' | 'superseded' | 'resolved';

export type ResolutionStatus = 'addressed' | 'still_open' | 'judge_dismissed';

export type ResolutionMethod =
  | 'absent_and_addressed'
  | 'judge_dismissed'
  | 'verification_dismissed'
  | 'human_dismissed';

export type MergeConclusion = 'success' | 'neutral' | 'failure';

export interface GitHubRepository {
  id: string;
  installation_id: string;
  workspace_id: string;
  github_repository_id: number;
  name: string;
  full_name: string;
  default_branch: string | null;
  private: boolean;
  html_url: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface GitHubPullRequest {
  id: string;
  repository_id: string;
  workspace_id: string;
  installation_id: string;
  github_pull_request_id: number;
  number: number;
  title: string;
  state: PullRequestState;
  head_sha: string;
  head_ref: string;
  base_ref: string;
  html_url: string | null;
  revision_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReviewRun {
  id: string;
  revision_id: string;
  workspace_id: string;
  status: ReviewRunStatus;
  profile: string;
  provider: string | null;
  error_message: string | null;
  judge_status: GitHubReviewJudgeStatus;
  judge_escalation_candidate_count: number;
  created_at: string;
  updated_at: string;
}

export interface ReviewFinding {
  id: string;
  review_run_id: string;
  severity: FindingSeverity;
  category: FindingCategory;
  title: string;
  message: string;
  file_path: string | null;
  start_line: number | null;
  end_line: number | null;
  suggestion?: string | null;
  created_at: string;
}

export interface ReconciledFinding {
  id: string;
  pull_request_id: string;
  state: FindingGroupState;
  severity: FindingSeverity;
  category: FindingCategory;
  title: string;
  message: string;
  file_path: string | null;
  last_seen_revision_id: string;
  resolution_status?: ResolutionStatus | null;
  resolution_method?: ResolutionMethod | null;
  resolved_at_revision_id?: string | null;
  closure_blocked_reason?: string | null;
  created_at: string;
  updated_at: string;
}

export interface PublishJob {
  id: string;
  review_run_id: string;
  revision_id: string;
  workspace_id: string;
  head_sha: string;
  status: PublishJobStatus;
  github_check_run_id: number | null;
  github_comment_id: number | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}
