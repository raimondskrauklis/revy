# Review pipeline R6 — GitHub publish

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** installation token auth; never publish from webhook HTTP handler; unit tests; idempotent publish per revision.

**Authority:** [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R6 (Checks Write, Pull requests Write), `integrations/github_api.py` (extend for Checks + PR reviews).

---

## Goal

Post check runs and PR review comments to GitHub so developers see Revy results in the PR — outbound only via `github_publish` queue.

**Scope:** In — `publish_tasks` on `github_publish` queue; create/update check run on PR head SHA; summary review comment (and optional inline comments v1 subset); map reconciled findings to GitHub API payloads; optional subscribe `check_run` / `check_suite` for CI context. Out — full inline suggestion API v2; check run annotations for every line.

**Deliverables:** Check run status `completed` with conclusion; summary comment on PR; publish job linked to review run; failures retried with backoff.

**Depends on:** R5 (reconciled findings ready to publish).

**Status:** Not started.

**Next:** `create-execution-plan` when R5 ships — [waves/REVIEW_PIPELINE_R6_EXECUTION.md](./waves/REVIEW_PIPELINE_R6_EXECUTION.md) (to be created).

**Next phase:** [REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md).
