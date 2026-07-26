# Review pipeline R0 — GitHub webhook ingestion

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; hand-written Alembic; never call GitHub API in webhook HTTP handler; ops runbooks in `docs/`.

**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`, [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) § R0, [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md).

---

## Goal

Accept signed GitHub App webhooks and enqueue `github_events` Celery work with idempotent delivery storage — foundation for all downstream review pipeline phases.

**Scope:** In — `POST /api/v1/webhooks/github`; HMAC `X-Hub-Signature-256` on raw body; `github_webhook_deliveries` dedupe by `X-GitHub-Delivery`; `github_tasks.process_github_event`; handlers for `installation` (status sync), `push` (log stub), `installation_repositories` (delegate — full apply in R1); `503` when `GITHUB_WEBHOOK_SECRET` empty; dev runbook. Out — `github_repositories` / PR tables; OAuth install UI; nginx IP allowlist; production worker queue change in CI.

**Deliverables:** Webhook returns **200** on valid signed delivery; duplicate deliveries idempotent; `github_installations.status` updated on `installation` events; Celery task enqueued; `docs/review-pipeline/GITHUB_WEBHOOK_DEV.md`; migration `0010`.

**Depends on:** P4 installations (`github_installations`), SaaS base, `saas-base-v1.1` Alembic AUTOCOMMIT.

**Status:** Shipped — tag `review-r0-v1` (`754c88c`).

**Execution:** [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md).

**Next:** [REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md).
