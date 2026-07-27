# Review generation lifecycle

**Status:** P0–P5 **done** on branch `feat/review-generation-lifecycle` (PR [#54](https://github.com/raimondskrauklis/revy/pull/54); HEAD `6f1afb5`). Dogfood: [REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md](./REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md).

**North star:** Greptile / Bugbot-class **snapshot semantics** — work targets **latest HEAD**, supersede in-flight generation when a newer commit arrives, **publish to GitHub only after the pass completes** (no spill on check, summary, or inline).

**Evidence:** PR [#53](https://github.com/raimondskrauklis/revy/pull/53) dogfood — multi-revision publish overlap; [github-surface-hardening](../github-surface-hardening/) shipped thread resolve on `main`.

| Doc | Role |
|-----|------|
| [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) | Baseline — gaps RG-1–RG-13, locked decisions |
| [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md) | Phased program P0–P5 |
| [REVIEW_GENERATION_LIFECYCLE_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_EXECUTION.md) | LOOP index + locked execution decisions |
| [../github-surface-hardening/](../github-surface-hardening/) | Prerequisite — Option A resolve, GraphQL scale (merged) |
| [REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md](./REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md) | PR #54 dogfood — Revy vs Greptile, Moonshot format |

**Branch:** `feat/review-generation-lifecycle`
