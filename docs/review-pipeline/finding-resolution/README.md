# Finding resolution program

**Status:** **shipped on branch** (`feat/finding-resolution`, PR [#57](https://github.com/raimondskrauklis/revy/pull/57)) — code-complete P0–P5; **staging human gate pending** ([validation memo](./FINDING_RESOLUTION_STAGING_VALIDATION.md)).

**LOOP mode (operator):** Agent implements one phase → local commit → operator pushes → validates staging → next phase.

**Migration pause:** Apply `0028` on staging before relying on resolution columns in production paths.

**Thesis:** How Revy decides a finding is **addressed**, **dismissed**, or **still open** — multi-pass closure after each push + resolution-rate metrics.

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_FINDINGS.md](./FINDING_RESOLUTION_FINDINGS.md) | Baseline — current flow, gaps, FR-Q registry |
| [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) | Incident + staging DB evidence |
| [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) | P0–P5 phases, locked FR-Q*, multi-pass model |
| [FINDING_RESOLUTION_STAGING_VALIDATION.md](./FINDING_RESOLUTION_STAGING_VALIDATION.md) | Staging dogfood + human sign-off checklist |
| [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md) | LOOP index + locked decisions |

## Execution (LOOP order)

| Phase | Focus | File | Commit | Status |
|-------|--------|------|--------|--------|
| P0 | Closure model, migration `0028`, compare helper | [P0](./waves/FINDING_RESOLUTION_P0_EXECUTION.md) | `76e8784` | done |
| P1 | Pass 1 stamp + Pass 2 reconcile closure | [P1](./waves/FINDING_RESOLUTION_P1_EXECUTION.md) | `c0522ec` / `97a7e01` | done |
| P2 | Pass 3 verification judge (5/run) | [P2](./waves/FINDING_RESOLUTION_P2_EXECUTION.md) | `c0522ec` | done |
| P3 | FR-Q12 metrics, G9, API fields | [P3](./waves/FINDING_RESOLUTION_P3_EXECUTION.md) | `73401aa` | done |
| P4 | Human dismiss, summary parity, RG-6 | [P4](./waves/FINDING_RESOLUTION_P4_EXECUTION.md) | `8b453aa` | done |
| P5 | Staging validation + doc sync | [P5](./waves/FINDING_RESOLUTION_P5_EXECUTION.md) | (P5 commit) | done (docs) |

**Related shipped programs:** R5 reconcile + judge · RQ6 resolution metrics · github-surface-hardening · generation lifecycle · judge input quality.

**Next wave:** [judge-json-contract](../judge-json-contract/README.md) after merge to `main`.
