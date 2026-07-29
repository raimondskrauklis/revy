# Finding resolution — post-PSA dogfood

**Status:** **waves A + B complete** — FR-DG1 **PASS**; FR-DG2 **partial PASS** ([#67](https://github.com/raimondskrauklis/revy/pull/67)). **Wave C** — [general plan](../finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) · [execution LOOP](../finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_EXECUTION.md).

**Thesis:** PSA #63 exposed resolution lifecycle gaps; dogfood validated fixes and exposed **cohort scope** as the remaining platform gap (FR-CS1).

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) | Original FR-DG* gaps |
| [FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) | Post–wave A investigation |
| [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md) | Operator locks VAL* |
| [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) | Push rows / sign-off |
| [FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_FINDINGS.md) | **Platform zoom-out** — FR-CS* |
| [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../finding-resolution/FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md) | **Wave C plan** |

## Sign-off summary

| Gap | Result |
|-----|--------|
| FR-DG1 | **PASS** — #65 rev 3 |
| FR-DG2a | **PASS** — #66 deployed `2026-07-29T19:20:33Z` |
| FR-DG2 | **Partial PASS** — #67; orphan VAL10 → **FR-CS1** |
| MR-DG1 | open — P4 |

## Operator rules

1. One push per Revy cycle.
2. `--since` = deploy job completion ([VAL9](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val9--post-66-deploy-fr-dg2a-on-staging)).
3. Dogfood repro pushes: **backend only** ([VAL8](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val8--dogfood-metrics-interpretation)).
4. Primary metric: **per-group** `state` + `resolution_method`, not `pr_active_count` alone.

**Next:** C0 LOOP → `fix/fr-closure-scope-hygiene` (C1+C2).
