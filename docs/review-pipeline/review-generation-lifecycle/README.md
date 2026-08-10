# Review generation lifecycle

**Status:** P0–P5 **shipped** on `main` ([PR #54](https://github.com/raimondskrauklis/revy/pull/54)). Post-ship restart fix merged ([#89](https://github.com/raimondskrauklis/revy/pull/89), `639043e`) — index-job supersede, deferred resolution pairing (G9 before pipeline), event-anchored coalesce, stale coalesce handoff via HEAD resolution task. Dogfood: [REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md](./REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md).

**North star:** Greptile / Bugbot-class **snapshot semantics** — work targets **latest HEAD**, supersede in-flight generation when a newer commit arrives, **publish to GitHub only after the pass completes** (no spill on check, summary, or inline).

**Evidence:** PR [#53](https://github.com/raimondskrauklis/revy/pull/53) dogfood — multi-revision publish overlap; [github-surface-hardening](../github-surface-hardening/) shipped thread resolve on `main`.

| Doc | Role |
|-----|------|
| [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) | Baseline — gaps RG-1–RG-15, locked decisions |
| [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md) | Phased program P0–P5 |
| [REVIEW_GENERATION_LIFECYCLE_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_EXECUTION.md) | LOOP index + locked execution decisions |
| [../github-surface-hardening/](../github-surface-hardening/) | Prerequisite — Option A resolve, GraphQL scale (merged) |
| [REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md](./REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md) | PR #54 dogfood — Revy vs Greptile, Moonshot format |
| [REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md](./REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md) | Post-#89 system probe + RG-15 sign-off |

**Post-ship:** [PR #89](https://github.com/raimondskrauklis/revy/pull/89) merged (`639043e`) — see [P2 post-ship addendum](./REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md#p27--post-ship-restart-hotfix-pr-89).
