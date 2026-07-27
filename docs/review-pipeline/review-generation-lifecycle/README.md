# Review generation lifecycle

**Status:** Execution plan peer-reviewed (2026-07-28); ready for `phase-execution` from [P0](./REVIEW_GENERATION_LIFECYCLE_P0_EXECUTION.md).

**North star:** Greptile / Bugbot-class **snapshot semantics** — work targets **latest HEAD**, supersede in-flight generation when a newer commit arrives, **publish to GitHub only after the pass completes** (no spill on check, summary, or inline).

**Evidence:** PR [#53](https://github.com/raimondskrauklis/revy/pull/53) dogfood — multi-revision publish overlap; [github-surface-hardening](../github-surface-hardening/) shipped thread resolve on `main`.

| Doc | Role |
|-----|------|
| [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) | Baseline — gaps RG-1–RG-13, locked decisions |
| [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md) | Phased program P0–P5 |
| [REVIEW_GENERATION_LIFECYCLE_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_EXECUTION.md) | LOOP index + locked execution decisions |
| [../github-surface-hardening/](../github-surface-hardening/) | Prerequisite — Option A resolve, GraphQL scale (merged) |
| [../REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Generation row — in flight P2, shipped P5 |

**Branch:** `feat/review-generation-lifecycle`
