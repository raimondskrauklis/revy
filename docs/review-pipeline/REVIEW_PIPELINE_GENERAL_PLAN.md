# Review pipeline — general plan index

Per-phase goals live in **separate files** (same layout as [docs/saas-base](../saas-base/README.md)). This file is the index only — **no execution steps**.

**Baseline:** [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) must be current before writing or updating any general plan.

**Workflow:** findings → general plan (phase) → [waves/](./waves/) execution → `phase-execution` on `feat/review-r*`.

---

## Phases

| Phase | General plan | Focus | Status |
|-------|--------------|-------|--------|
| R0 | [R0 webhooks](./REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | Webhook ingest, HMAC, `github_events` | shipped (`review-r0-v1`) |
| R1 | [R1 repo sync](./REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | `github_repositories`, `repo_sync` | shipped (`review-r1-v1`) |
| R2 | [R2 PR ingestion](./REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | PR + revision tracking | **next** |
| R3–R7 | [R3–R7 outline](./REVIEW_PIPELINE_R3_R7_GENERAL_PLAN.md) | Index → review → publish → UI | not started |

## Execution

| Phase | Execution | Status |
|-------|-----------|--------|
| R0 | [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | done |
| R1 | [waves/REVIEW_PIPELINE_R1_EXECUTION.md](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | done |
| R2 | — | create after R2 general plan peer-review |

Full table: [waves/README.md](./waves/README.md).

## GitHub App (external setup)

| Doc | Purpose |
|-----|---------|
| [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) | Create App; minimal config for current phase |
| [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) | One-time full R0–R7 target values |
| [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md) | Local webhook forwarding |

## Cross-cutting (every phase)

Workspace tenancy; audit on mutating routes; EN+LV for UI; unit tests; hand-written Alembic; releases via tags on `main` ([REVIEW_PIPELINE_PROGRAM.md](./REVIEW_PIPELINE_PROGRAM.md)).

---

## Next

1. Lock R2 open questions in [findings](./REVIEW_PIPELINE_FINDINGS.md).
2. `create-execution-plan` → `waves/REVIEW_PIPELINE_R2_EXECUTION.md`.
3. `execution-peer-review` → `phase-execution` on `feat/review-r2-pr-ingestion`.
