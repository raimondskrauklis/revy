# Review pipeline R5 — Reconciliation + judge

General plan from [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** workspace tenancy; deterministic fingerprinting; unit tests; hand-written Alembic.

**Authority:** `internal-docs/product/revy/docs/architecture.md`, Celery routes `reconciliation` + `judge` in `celery_app.py`.

---

## Goal

Deduplicate findings across PR revisions and run judge/escalation when models disagree — stable finding identity for UI and publish.

**Scope:** In — `reconcile_tasks` + `judge_tasks` queues; fingerprint per [R5-Q1](./REVIEW_PIPELINE_FINDINGS.md); link findings across revisions per [R5-Q2](./REVIEW_PIPELINE_FINDINGS.md); **Anthropic Claude** judge per [R5-Q3](./REVIEW_PIPELINE_FINDINGS.md); judge outcome persisted; supersede/resolve states; reconciled finding API. Out — human-in-the-loop approval workflow; GitHub comment posting (R6).

**Before execution:** R5-Q1–Q3 locked in findings; `execution-peer-review` on [R5 execution](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) after R4 ships.

**Model policy:** Primary review remains Moonshot Kimi (R4). Judge stage uses **Anthropic** as the secondary model family — `internal-docs/product/revy/docs/architecture.md` §14.

**Deliverables:** Stable `finding_id` across pushes where applicable; reconciliation job after each review run; judge escalation rows; API exposes reconciled finding set.

**Depends on:** R4.

**Status:** Not started.

**Next:** `execution-peer-review` on [waves/REVIEW_PIPELINE_R5_EXECUTION.md](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) after R4 ships (`review-r4-v1`).

**Next phase:** [REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md).
