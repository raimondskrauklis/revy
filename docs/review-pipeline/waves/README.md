# Review pipeline — execution index

Linear **phase-execution** order. General plan: [REVIEW_PIPELINE_GENERAL_PLAN.md](../REVIEW_PIPELINE_GENERAL_PLAN.md).

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md), `internal-docs/product/revy/docs/WEBHOOKS.md`.

| Phase | File | Status |
|-------|------|--------|
| R0 — GitHub webhooks | [REVIEW_PIPELINE_R0_EXECUTION.md](./REVIEW_PIPELINE_R0_EXECUTION.md) | ready for LOOP |
| R1 — Repository sync | — | not started |
| R2 — PR ingestion | — | not started |
| R3 — Indexing | — | not started |
| R4 — Review run | — | not started |
| R5 — Reconcile + judge | — | not started |
| R6 — GitHub publish | — | not started |
| R7 — Reviewer UI | — | not started |

**Program status:** Findings + general plan + R0 execution ready. Start branch `feat/review-r0-webhooks`.

**SaaS base:** frozen at tag `saas-base-v1`; infra patch `saas-base-v1.1` (Alembic AUTOCOMMIT).
