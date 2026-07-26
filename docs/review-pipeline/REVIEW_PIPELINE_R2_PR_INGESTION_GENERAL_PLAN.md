# Review pipeline R2 — Pull request ingestion

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; link PRs to `github_repositories` and `github_installations`; unit tests; hand-written Alembic; orphan repo → log + **200**.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R2, `internal-docs/product/revy/docs/architecture.md`, `WEBHOOKS.md`.

---

## Goal

Track pull requests and per-push revisions from GitHub webhook events; enable workspace-scoped PR queries for R3 indexing and R4 review runs.

**Scope:** In — `github_pull_requests` + `github_pull_request_revisions` tables; extend `SUPPORTED_EVENTS` for `pull_request` and `pull_request_review`; `github_tasks` handlers for actions `opened`, `synchronize`, `closed`, `reopened`; revision row on each `synchronize`; cursor list API `GET …/repositories/{repo_id}/pull-requests`. Out — full diff/blob storage; inline review comment threads; GitHub publish (R6); re-review trigger on `push` (wire in R3/R4).

**Deliverables:** PR rows created/updated from webhooks; monotonic revision counter; `pull_request_review` stored for activity audit; member list API; migration `0012+`.

**Depends on:** R1 (`github_repositories` rows for known repos).

**Status:** Not started — general plan baseline-ready; execution file + peer-review required before code.

**Next:** `create-execution-plan` → [waves/REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) (to be created) → `execution-peer-review` → `phase-execution`.

**Next phase:** [REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md](./REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md).
