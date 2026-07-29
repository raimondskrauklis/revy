# Finding resolution dogfood — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) · **General plan:** [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md)

**Authority:** [finding-resolution FR-Q1–FR-Q15](../finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md) · [GH-1v2 §4c](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md#gh-1v2--collapse-triggers-shipped-post-p4) · PSA #63 incident timeline in findings § FR-DG1/FR-DG2

**Goal:** Close FR-DG1 + FR-DG2 on staging with chore dogfood; MR-DG1 on parallel branch.

**Branch (wave A):** `chore/finding-resolution-staging-dogfood` from `main`  
**Branch (wave B):** `chore/moonshot-formatter-signature` from `main` (after P0.0)

## How we work (locked)

```text
P0 → merge → P1 → merge → deploy → dogfood push 2 (FR-DG1)
              → P2 → merge → deploy → dogfood push 3 (FR-DG2)
              → P3 sign-off (+ optional push 4 regrowth)
P4 parallel after P0.0 (wave B)
each phase: implement → pytest gate → Bugbot → commit → merge to main → deploy → chore push → wait for agent
```

**Operator LOOP:** One push per agent cycle — no back-to-back commits while Revy runs (`skipped_not_head` invalidates resolution sign-off).

## Deploy boundaries

| Boundary | `--since` | Dogfood push |
|----------|-----------|--------------|
| PSA baseline | `2026-07-29T11:38:12Z` | P0 metrics reference only |
| Post-P1 deploy | operator records ISO | **Push 2** — FR-DG1 |
| Post-P2 deploy | operator records ISO | **Push 3** — FR-DG2; P3.1 sign-off metrics |

## Decisions locked for execution

- **FR-DG1 sign-off:** `resolution_pass.denominator_active_prior` ≥ 1 and `transitions_addressed` ≥ 1; G9 + `summary_json.resolution` from `resolution_metrics_manifest` (P1.3).
- **FR-DG2 sign-off:** separate dogfood **push 3** after P2 deploy — probe **code removal**, not push 2.
- **Prior revision:** shared `get_last_published_prior_revision` in `reconcile_tasks.py`, `github_resolution_metrics.py`, `github_finding_closure.py` (not read-path only).
- **Dogfood probe:** ephemeral `backend/tests/fixtures/fr_dogfood/` — removed in P3 doc-sync.
- **RCX / judge-json:** out of scope.

## LOOP order

| Phase | Focus | Execution | Wave | Status |
|-------|--------|-----------|------|--------|
| P0 — Repro + observability | Probe, memo stub, metrics, SSOT | [P0](./FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) | A | done `4830ff7` |
| P1 — FR-DG1 | Manifest + G9 wiring | [P1](./FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md) | A | done `c2c255c` |
| P2 — FR-DG2 | Stale retirement + collapse | [P2](./FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md) | A | done `b521d23` |
| P3 — Staging sign-off | Evidence + doc sync | [P3](./FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md) | A | in progress |
| P4 — MR-DG1 | Moonshot signature | [P4](./FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) | B | pending |

**Peer review:** applied 2026-07-29 — ready for `phase-execution`.
