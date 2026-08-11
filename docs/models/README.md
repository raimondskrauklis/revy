# Model policy & providers

**Status:** Shipped M0–M3 on branch `feat/model-policy-m0` (PR #35).

Findings and plans for **which models run where** in the review pipeline — embeddings, reviewer, judge, and future jury.

| Doc | Purpose |
|-----|---------|
| [MODEL_POLICY_FINDINGS.md](./MODEL_POLICY_FINDINGS.md) | Baseline — current code, gaps, Bedrock, UI, deferred patterns |
| [MODEL_POLICY_GENERAL_PLAN.md](./MODEL_POLICY_GENERAL_PLAN.md) | Phased plan — M0–M3 (locked decisions) |
| [voyage-embeddings/](./voyage-embeddings/) | Voyage R3 embedding upgrades (`voyage-code-4` discovery) |
| [model-run-capture/](./model-run-capture/) | Per-run model identity — MRC-P0–P3 shipped; API exposes `models_snapshot` |
| [waves/README.md](./waves/README.md) | Execution index — phase-execution LOOP order |

**Related:** [review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md) (cross-model jury, grounding, R9), [utils/GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md) (today’s env vars).

**Authority (product):** `internal-docs/product/revy/docs/architecture.md` §11.3 (embeddings), §13–14 (LLM review + judge).
