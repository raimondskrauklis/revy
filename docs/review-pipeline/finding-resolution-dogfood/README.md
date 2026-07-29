# Finding resolution — post-PSA dogfood

**Status:** **wave A staging complete** — FR-DG1 **PASS**; FR-DG2 **PARTIAL** ([#65](https://github.com/raimondskrauklis/revy/pull/65)). Follow-up: [post-validation findings](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) (Track A code + Track B repro).

**Thesis:** PSA #63 validated two-block publish shape; PR #63 exposed **resolution lifecycle** failures (G9 prose, stale groups, thread collapse) that need isolated dogfood with **one push per agent cycle**.

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) | Baseline — FR-DG* gaps, evidence, target PRs |
| [FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) | **Post-staging** — root cause, improvements, FR-DG2a |
| [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](./FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md) | P0–P4 phases, waves A/B |
| [waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md](./waves/FINDING_RESOLUTION_DOGFOOD_EXECUTION.md) | LOOP index P0–P4 |
| [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md) | Operator locks — FR-DG-VAL* post-merge protocol |
| [FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md](./FINDING_RESOLUTION_DOGFOOD_STAGING_VALIDATION.md) | Operator memo (push rows) |

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 — Repro + observability | Probe, metrics, SSOT | [P0](./waves/FINDING_RESOLUTION_DOGFOOD_P0_EXECUTION.md) | done |
| P1 — FR-DG1 | Manifest + G9 | [P1](./waves/FINDING_RESOLUTION_DOGFOOD_P1_EXECUTION.md) | done — staging PASS |
| P2 — FR-DG2 | Stale retirement + collapse | [P2](./waves/FINDING_RESOLUTION_DOGFOOD_P2_EXECUTION.md) | code done — staging PARTIAL |
| P3 — Staging sign-off | Evidence + doc sync | [P3](./waves/FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md) | done — memo + post-validation |
| P4 — MR-DG1 | Moonshot signature (wave B) | [P4](./waves/FINDING_RESOLUTION_DOGFOOD_P4_EXECUTION.md) | pending |

## Planned PRs

| PR branch | Gaps | Notes |
|-----------|------|-------|
| `chore/finding-resolution-staging-dogfood` | FR-DG1, FR-DG2 partial | [#65](https://github.com/raimondskrauklis/revy/pull/65) — merge for FR-DG1; not FR-DG2 sign-off |
| `fix/fr-dg2-file-deletion-pass1` | FR-DG2a | Proposed — Track A in post-validation findings |
| `chore/moonshot-formatter-signature` | MR-DG1 | Wave B — P4 parallel |

## Operator rules (from PSA #63)

1. **One push per agent cycle** — no back-to-back commits while Revy is running.
2. **Deploy boundary** — `--since` = droplet deploy job completion, not merge time.
3. **Dogfood PR** — `chore/<program>-staging-dogfood`; minimal `backend/**` touch for autostart.
4. **FR-DG2 repro** — no program-doc edits in pushes 1–3 ([VAL8](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val8--dogfood-metrics-interpretation)).

**Parent program:** [finding-resolution](../finding-resolution/README.md) (shipped P0–P5 on #57).

**Excluded:** RCX retrieve, judge-json contract code.

**Next step:** Implement **Track A** (file-deletion Pass 1) from [post-validation findings](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md), then Track B staging repro.
