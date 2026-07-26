# Review pipeline — execution index

Linear **phase-execution** order.

**Prerequisites (no shortcuts):**

1. [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) — baseline-ready
2. Per-phase [general plan](../REVIEW_PIPELINE_GENERAL_PLAN.md) — peer-reviewed
3. This execution file — `execution-peer-review` before `phase-execution`

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md), [GITHUB_APP_SETUP.md](../../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../../utils/GITHUB_APP_TARGET_CONFIG.md).

| Phase | General plan | Execution | Status |
|-------|--------------|-----------|--------|
| R0 — GitHub webhooks | [R0](../REVIEW_PIPELINE_R0_WEBHOOKS_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R0_EXECUTION.md](./REVIEW_PIPELINE_R0_EXECUTION.md) | done (`review-r0-v1`) |
| R1 — Repository sync | [R1](../REVIEW_PIPELINE_R1_REPO_SYNC_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R1_EXECUTION.md](./REVIEW_PIPELINE_R1_EXECUTION.md) | done (`review-r1-v1`) |
| R2 — PR ingestion | [R2](../REVIEW_PIPELINE_R2_PR_INGESTION_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R2_EXECUTION.md](./REVIEW_PIPELINE_R2_EXECUTION.md) | done (`review-r2-v1`) |
| R3 — Indexing | [R3](../REVIEW_PIPELINE_R3_INDEXING_GENERAL_PLAN.md) | [REVIEW_PIPELINE_R3_EXECUTION.md](./REVIEW_PIPELINE_R3_EXECUTION.md) | done (`review-r3-v1`) |
| R4 — Review run | [R4](../REVIEW_PIPELINE_R4_REVIEW_RUN_GENERAL_PLAN.md) | — | **next** |
| R5 — Reconcile + judge | [R5](../REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md) | — | after R4 |
| R6 — GitHub publish | [R6](../REVIEW_PIPELINE_R6_GITHUB_PUBLISH_GENERAL_PLAN.md) | — | after R5 |
| R7 — Reviewer UI | [R7](../REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md) | — | after R4 API |

**Program status:** R0–R3 shipped; R4 execution is next.
