# PSR-Q8 routes audit

**Date:** 2026-08-08  
**Phase:** P1 spike — ship field in P2

## Routes returning `GitHubPublishJobResponse`

| Method | Path | Handler | File |
|--------|------|---------|------|
| GET | `/api/v1/workspaces/{workspace_id}/installations/{installation_id}/review-runs/{review_run_id}/publish-job` | `get_publish_job_for_review_run` | `backend/app/api/v1/workspaces/installation_review.py` |
| GET | `/api/v1/workspaces/{workspace_id}/installations/{installation_id}/pull-requests/{pull_request_id}/publish-job/latest` | `get_latest_publish_job_for_pull_request` | `backend/app/api/v1/workspaces/installation_review.py` |

## P2 ship plan

- Add `pr_resolution_rollup: dict | None` to `GitHubPublishJobResponse` (`backend/app/schemas/github_publish.py`)
- Populate from `job.summary_json.get("pr_resolution_rollup")` in both handlers above
- Route tests in `backend/tests/unit/test_github_publish_routes.py`
