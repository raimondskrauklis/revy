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
| R4 | [R4 review run](./REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | LLM pipeline, findings | implemented — PR [#24](https://github.com/raimondskrauklis/revy/pull/24) |
| R5 | [R5 reconcile + judge](./REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | Fingerprints, escalation | implemented — PR [#25](https://github.com/raimondskrauklis/revy/pull/25) |
| R6 | [R6 GitHub publish](./REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | Checks, PR comments | implemented — PR [#26](https://github.com/raimondskrauklis/revy/pull/26) |
| R7 | [R7 reviewer UI](./REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | `features/reviewer/` | implemented — PR [#27](https://github.com/raimondskrauklis/revy/pull/27) |
| R8 | [R8 automation](./REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) | Autostart, `@revy review`, settings | **planned** — execution ready for peer-review |

## Execution

| Phase | Execution | Status |
|-------|-----------|--------|
| R0 | [waves/REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md) | done |
| R1 | [waves/REVIEW_PIPELINE_R1_EXECUTION.md](./waves/REVIEW_PIPELINE_R1_EXECUTION.md) | done |
| R2 | [waves/REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md) | done |
| R3 | [waves/REVIEW_PIPELINE_R3_EXECUTION.md](./waves/REVIEW_PIPELINE_R3_EXECUTION.md) | done |
| R4 | [waves/REVIEW_PIPELINE_R4_EXECUTION.md](./waves/REVIEW_PIPELINE_R4_EXECUTION.md) | done — PR [#24](https://github.com/raimondskrauklis/revy/pull/24) |
| R5 | [waves/REVIEW_PIPELINE_R5_EXECUTION.md](./waves/REVIEW_PIPELINE_R5_EXECUTION.md) | done — PR [#25](https://github.com/raimondskrauklis/revy/pull/25) |
| R6 | [waves/REVIEW_PIPELINE_R6_EXECUTION.md](./waves/REVIEW_PIPELINE_R6_EXECUTION.md) | done — PR [#26](https://github.com/raimondskrauklis/revy/pull/26) |
| R7 | [waves/REVIEW_PIPELINE_R7_EXECUTION.md](./waves/REVIEW_PIPELINE_R7_EXECUTION.md) | done — PR [#27](https://github.com/raimondskrauklis/revy/pull/27) |
| R8 | [waves/REVIEW_PIPELINE_R8_EXECUTION.md](./waves/REVIEW_PIPELINE_R8_EXECUTION.md) | pending peer-review |

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

1. **Merge PR stack** — [#26](https://github.com/raimondskrauklis/revy/pull/26) → [#27](https://github.com/raimondskrauklis/revy/pull/27); then **r7 → main**; tag `review-r5-v1` … `review-r7-v1`.
2. **Post-merge ops** — staging e2e per [GITHUB_WEBHOOK_DEV.md](./GITHUB_WEBHOOK_DEV.md).
3. **R8** — [general plan](./REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md) + [execution](./waves/REVIEW_PIPELINE_R8_EXECUTION.md); peer-review → `phase-execution` on `feat/review-r8-automation`.
