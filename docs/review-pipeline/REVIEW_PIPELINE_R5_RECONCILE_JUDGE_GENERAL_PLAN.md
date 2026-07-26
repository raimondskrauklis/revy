# Review pipeline R5 — Reconciliation + judge

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; deterministic fingerprinting; unit tests; hand-written Alembic.

**Authority:** `internal-docs/product/revy/docs/architecture.md`, Celery routes `reconciliation` + `judge` in `celery_app.py`.

---

## Goal

Deduplicate findings across PR revisions and run judge/escalation when models disagree — stable finding identity for UI and publish.

**Scope:** In — `reconcile_tasks` + `judge_tasks` queues; fingerprint logic (file + rule + message hash or product-defined key); link findings across revisions; judge outcome persisted; supersede/resolve states. Out — human-in-the-loop approval workflow; GitHub comment posting (R6).

**Deliverables:** Stable `finding_id` across pushes where applicable; reconciliation job after each review run; judge escalation rows; API exposes reconciled finding set.

**Depends on:** R4.

**Status:** Not started.

**Next:** `create-execution-plan` when R4 ships — [waves/REVIEW_PIPELINE_R5_EXECUTION.md](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) (to be created).

**Next phase:** [REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md).
