# Review pipeline R2 — Pull request ingestion

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; link PRs to `github_repositories`; unit tests; hand-written Alembic.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) (Pull requests permission, `pull_request` events), `internal-docs/product/revy/docs/architecture.md`.

---

## Goal

Track pull requests and revisions from GitHub webhook events; enable workspace-scoped PR queries for downstream indexing and review.

**Scope:** In — `github_pull_requests` (or `pull_requests`) + revision table; extend `SUPPORTED_EVENTS` and `github_tasks` for `pull_request`, `pull_request_review` (read path); link to `github_repositories` + installation; list API (member). Out — full diff/blob storage, inline comment threads, GitHub publish (R6).

**Deliverables:** PR rows created/updated from webhooks; revision counter on synchronize; orphan repo → log + skip; cursor list per workspace/installation/repo.

**Depends on:** R1 (`github_repositories` rows exist for known repos).

**Status:** Not started — requires execution file after peer-review.

**Next step:** `create-execution-plan` → [waves/REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) (to be created).

**Next phase:** [REVIEW_PIPELINE_R3_R7_GENERAL_PLAN.md](./REVIEW_PIPELINE_R3_R7_GENERAL_PLAN.md) § R3.

---

## Open questions (lock in findings before execution)

| Q# | Question | Default proposal |
|----|----------|------------------|
| R2-Q1 | Table naming | `github_pull_requests` + `github_pull_request_revisions` (consistent with `github_*`) |
| R2-Q2 | Webhook events v1 | `pull_request` actions: `opened`, `synchronize`, `closed`, `reopened` |
| R2-Q3 | Unknown repository | Log + **200** (match orphan installation policy) |
| R2-Q4 | API surface | `GET …/repositories/{repo_id}/pull-requests` cursor list |
