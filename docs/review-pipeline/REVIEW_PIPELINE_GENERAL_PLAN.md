# Review pipeline — general plan index

Per-phase goals in **separate files** — same layout as [docs/saas-base](../saas-base/README.md). **No execution steps.**

**Baseline:** [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) must be current before any execution file.

**Workflow:** findings → general plan (this folder) → [waves/](./waves/) execution → `phase-execution` on `feat/review-r*`.

---

## Phases (R0–R7)

| Phase | General plan | Focus | Status |
|-------|--------------|-------|--------|
| R0 | [R0 webhooks](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | Webhook ingest, HMAC, `github_events` | shipped (`review-r0-v1`) |
| R1 | [R1 repo sync](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | `github_repositories`, `repo_sync` | shipped (`review-r1-v1`) |
| R2 | [R2 PR ingestion](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | PR + revision tracking | shipped (`review-r2-v1`) |
| R3 | [R3 indexing](./REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | Chunks, embeddings, pgvector | shipped (`review-r3-v1`) |
| R4 | [R4 review run](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | LLM pipeline, findings | **next** |
| R5 | [R5 reconcile + judge](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | Fingerprints, escalation | not started |
| R6 | [R6 GitHub publish](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | Checks, PR comments | not started |
| R7 | [R7 reviewer UI](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | `features/reviewer/` | not started |

## Execution

| Phase | Execution | Status |
|-------|-----------|--------|
| R0 | [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | done |
| R1 | [waves/REVIEW_PIPELINE_R1_EXECUTION.md](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | done |
| R2 | [waves/REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | done |
| R3 | [waves/REVIEW_PIPELINE_R3_EXECUTION.md](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | done |
| R4 | [waves/REVIEW_PIPELINE_R4_EXECUTION.md](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | pending |
| R5–R7 | — | create per phase after peer-review |

Full table: [waves/README.md](./waves/README.md).

## GitHub App (external)

| Doc | Purpose |
|-----|---------|
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | Step-by-step; phase-minimal config |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | One-time full R0–R7 target values |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local webhook forwarding |

## Cross-cutting (every phase)

Workspace tenancy; audit on mutating routes; EN+LV for UI; unit tests; hand-written Alembic; milestone tags on `main` ([REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md)).

---

## Next

1. `execution-peer-review` → [waves/REVIEW_PIPELINE_R4_EXECUTION.md](./waves/REVIEW_PIPELINE_R4_EXECUTION.md).
2. `phase-execution` on `feat/review-r4-review-run`.
