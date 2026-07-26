# Review pipeline — general plan

From [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting (every phase):** workspace tenancy, audit where mutating, EN+LV, unit tests, hand-written Alembic.

**Status:** R0–R7 not started.

---

## R0 — GitHub webhook ingestion

**Goal:** Accept signed GitHub App webhooks and enqueue `github_events` work.

**Scope:** In — `POST /api/v1/webhooks/github`, HMAC verify, delivery dedupe table, `github_tasks` module (installation + push handlers), env docs. Out — repo/PR entities, OAuth install UI, production App registration.

**Deliverables:** Webhook returns 200; duplicate deliveries idempotent; installation status sync; Celery task enqueued; dev runbook.

**Depends on:** P4 installations, SaaS base, `saas-base-v1.1` migration runner.

---

## R1 — Repository sync

**Goal:** Mirror installation-linked repositories after webhook or manual trigger.

**Scope:** In — `repositories` table, `repo_sync` tasks, link to `github_installations`. Out — full mirror fetch, branch protection sync.

**Deliverables:** Repo rows per installation; list API stub or admin visibility.

**Depends on:** R0.

---

## R2 — Pull request ingestion

**Goal:** Track PRs and revisions from GitHub events.

**Scope:** In — `pull_request` + revision schema, webhook handlers for `pull_request` / `pull_request_review`. Out — full diff storage.

**Deliverables:** PR rows created/updated from webhooks; workspace-scoped queries.

**Depends on:** R1.

---

## R3 — Indexing

**Goal:** Chunk and embed repository content for review context.

**Scope:** In — pgvector index jobs, `indexing` queue. Out — symbol index, cross-repo search.

**Deliverables:** Embeddings stored; retrieval API for review stage.

**Depends on:** R2.

---

## R4 — Review run

**Goal:** LLM pipeline produces structured findings per PR revision.

**Scope:** In — `review_tasks`, model provider config, finding schema. Out — multi-model judge (→ R5).

**Deliverables:** Review run record + findings rows; gated API for workspace members.

**Depends on:** R3.

---

## R5 — Reconciliation + judge

**Goal:** Deduplicate and escalate findings across revisions.

**Scope:** In — `reconciliation`, `judge` queues, fingerprint logic. Out — human review workflow.

**Deliverables:** Stable finding identity across pushes; judge outcomes persisted.

**Depends on:** R4.

---

## R6 — GitHub publish

**Goal:** Post check runs and review comments to GitHub.

**Scope:** In — `github_publish` tasks, installation token auth. Out — inline suggestion API v2 nuances.

**Deliverables:** Check run status on PR; summary comment posted.

**Depends on:** R5.

---

## R7 — Reviewer UI

**Goal:** In-app surfaces for PR status, findings, and review history.

**Scope:** In — `features/reviewer/`, routes, dashboard widgets, i18n. Out — GitHub.com replacement UI.

**Deliverables:** Member can view findings for workspace PRs; links to GitHub.

**Depends on:** R4 (read-only UI can ship before R6 with caveats).

---

## Next

**`create-execution-plan`** → [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) first; peer-review before `phase-execution` on `feat/review-r0-webhooks`.
