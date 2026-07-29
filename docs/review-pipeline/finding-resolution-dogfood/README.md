# Finding resolution — post-PSA dogfood

**Status:** **execution plans ready** — [waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md](./waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md).

**Thesis:** PSA #62 validated two-block publish shape; PR #63 exposed **resolution lifecycle** failures (G9 prose, stale groups, thread collapse) that need isolated dogfood with **one push per agent cycle**.

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) | Baseline — FR-DG* gaps, evidence, target PRs |
| [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](./FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md) | P0–P4 phases, waves A/B |
| [waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md](./waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md) | LOOP index P0–P4 |
| *(P0)* [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) | Operator memo (created in P0.1) |

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 — Repro + observability | Probe, metrics, SSOT | [P0](./waves/FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) | pending |
| P1 — FR-DG1 | Manifest + G9 | [P1](./waves/FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md) | pending |
| P2 — FR-DG2 | Stale retirement + collapse | [P2](./waves/FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md) | pending |
| P3 — Staging sign-off | Evidence + doc sync | [P3](./waves/FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md) | pending |
| P4 — MR-DG1 | Moonshot signature (wave B) | [P4](./waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) | pending |

## Planned PRs

| PR branch | Gaps | Notes |
|-----------|------|-------|
| `chore/finding-resolution-staging-dogfood` | FR-DG1, FR-DG2 | Wave A — P0–P3 |
| `chore/moonshot-formatter-signature` | MR-DG1 | Wave B — P4 parallel after P0 |

## Operator rules (from PSA #63)

1. **One push per agent cycle** — no back-to-back commits while Revy is running.
2. **Deploy boundary** — `--since` = droplet deploy job completion, not merge time.
3. **Dogfood PR** — `chore/<program>-staging-dogfood`; minimal `backend/**` touch for autostart.

**Parent program:** [finding-resolution](../finding-resolution/README.md) (shipped P0–P5 on #57).

**Excluded:** RCX retrieve, judge-json contract code.

**Next step:** `execution-peer-review` → attach plan folder + `phase-execution` on P0.
