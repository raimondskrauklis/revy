# Review pipeline R0 — GitHub webhook ingestion

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; hand-written Alembic; never call GitHub API in webhook handler.

**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`, [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) (webhook URL + secret), [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md).

---

## Goal

Accept signed GitHub App webhooks and enqueue `github_events` Celery work with idempotent delivery storage.

**Scope:** In — `POST /api/v1/webhooks/github`, HMAC `X-Hub-Signature-256`, `github_webhook_deliveries`, `github_tasks` (`installation`, `installation_repositories` stub, `push` log), env docs. Out — repository/PR entities, OAuth install UI, nginx IP allowlist.

**Deliverables:** Webhook **200**; duplicate deliveries idempotent; installation status sync; task enqueued; local dev runbook.

**Depends on:** P4 installations, SaaS base, `saas-base-v1.1` migration runner.

**Status:** Shipped — tag `review-r0-v1`.

**Execution:** [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md).

**Next:** [REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md).
