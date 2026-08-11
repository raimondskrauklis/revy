# Model run capture

Durable **which model ran** audit trail for embeddings, reviewer, judge, and publish — survives env/catalog changes over time.

| Doc | Purpose |
|-----|---------|
| [MODEL_RUN_CAPTURE_FINDINGS.md](./MODEL_RUN_CAPTURE_FINDINGS.md) | Baseline — current capture gaps, target catalog |
| [MODEL_RUN_CAPTURE_GENERAL_PLAN.md](./MODEL_RUN_CAPTURE_GENERAL_PLAN.md) | Phased plan — MRC-P0–P3 |
| [waves/README.md](./waves/README.md) | Execution index — phase-execution LOOP order |
| [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](./MODEL_RUN_CAPTURE_STAGING_VALIDATION.md) | Staging sign-off — P0/P1 (#96) + P2 snapshot (#98) |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Architecture peer review — pass index |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/README.md) | Execution peer review — pass index |

**Program status (2026-08-11):** MRC-P0–P3 **shipped + staging sign-off PASS** ([#96](https://github.com/raimondskrauklis/revy/pull/96), [#98](https://github.com/raimondskrauklis/revy/pull/98), [#99](https://github.com/raimondskrauklis/revy/pull/99), dogfood [#97](https://github.com/raimondskrauklis/revy/pull/97) + [#100](https://github.com/raimondskrauklis/revy/pull/100)).

**Related:** [MODEL_POLICY_FINDINGS.md](../MODEL_POLICY_FINDINGS.md) (which model to use) · [voyage-embeddings/](../voyage-embeddings/) (embedding upgrades) · [pipeline-observability](../../review-pipeline/pipeline-observability/) (tokens, latency, failures — sibling program).
