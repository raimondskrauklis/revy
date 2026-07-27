# Post review-quality program (v1.1+)

**Status:** findings baseline — opens after PR [#51](https://github.com/raimondskrauklis/revy/pull/51) (RQ9) dogfood.

**Prerequisite:** RQ0–RQ9 on `main`; tag `review-quality-v1` after human gate (AS2 + staging `0026`).

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) | Baseline — gaps from PR #51 dogfood + deferred tracks |
| 2 | General plan | *TBD* — after findings peer-review |
| 3 | Execution | *TBD* — under `waves/` when phased |

---

## Tracks (from dogfood)

| Track | Focus | When |
|-------|--------|------|
| **PQ-OPS** | Human gate AS2, staging `0026`, deploy on merge | Before tag |
| **PQ-UX** | G-UX+ ack affordances; Revy publish narrative vs Greptile | v1.1 |
| **PQ-RC** | RQ-RC-1 — scoped Greptile/Bugbot context | After tag |
| **PQ-STRUCT** | RQ-STRUCT-1 — SC3 population, cross-file graph | After tag |
| **PQ-CI** | `SKIP_CI_TESTS=false`, deploy visibility on PR | Ops |

**Evidence:** [DOGFOOD § PR #51](../review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#dogfood-pr-51--docsagent-work-rq9) · [review-quality program](../review-quality/README.md)
