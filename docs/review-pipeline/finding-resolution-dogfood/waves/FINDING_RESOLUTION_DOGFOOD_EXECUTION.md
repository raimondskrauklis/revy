# Finding resolution dogfood — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](../FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) · **General plan:** [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md)

**Authority:** [finding-resolution FR-Q1–FR-Q15](../finding-resolution/FINDING_RESOLUTION_GENERAL_PLAN.md) · [GH-1v2 §4c](../github-surface-hardening/GITHUB_SURFACE_HARDENING_FINDINGS.md#gh-1v2--collapse-triggers-shipped-post-p4) · PSA #63 incident timeline in findings § FR-DG1/FR-DG2

**Goal:** Close FR-DG1 + FR-DG2 on staging with chore dogfood; MR-DG1 on parallel branch.

**Branch (wave A):** `chore/finding-resolution-staging-dogfood` from `main`  
**Branch (wave B):** `chore/moonshot-formatter-signature` from `main` (after P0.0)

## How we work (locked)

```text
P0 → P1 → P2 → P3   (wave A — resolution closure)
P4 after P0 on separate branch (wave B — MR-DG1)
each phase: implement → pytest gate → Bugbot → commit → operator push → wait for agent
```

**Operator LOOP:** One push per agent cycle — no back-to-back commits while Revy runs (`skipped_not_head` invalidates resolution sign-off).

**Human gate:** P0.4 (dogfood push 1), P3.2–P3.3 (staging evidence + sign-off).

## Decisions locked for execution

- **FR-DG1 / FR-DG2 / MR-DG1:** see [findings](../FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) — no re-decide in LOOP.
- **Prior revision:** when rev N−1 publish was `skipped_not_head`, manifest uses last **published** prior revision for denominator (P1).
- **Dogfood probe:** ephemeral `backend/tests/fixtures/fr_dogfood/` — removed in P3 doc-sync if merged to `main`.
- **Metrics:** extend `judge_json_contract_staging_metrics.py` with publish `summary_json` resolution fields (P0.3) — read-only.
- **RCX / judge-json:** out of scope — do not touch retrieve or judge JSON parsers.

## LOOP order

| Phase | Focus | Execution | Wave | Status |
|-------|--------|-----------|------|--------|
| P0 — Repro + observability | Probe, memo stub, metrics, SSOT | [FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) | A | pending |
| P1 — FR-DG1 | Manifest pairing + G9 denominator | [FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md) | A | pending |
| P2 — FR-DG2 | Stale group retirement + thread collapse | [FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md) | A | pending |
| P3 — Staging sign-off | Dogfood evidence + doc sync | [FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md) | A | pending |
| P4 — MR-DG1 | Moonshot formatter signature | [FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) | B | pending |

**Peer review:** run `execution-peer-review` on P0–P3 before `phase-execution`.
