# Finding resolution program

**Status:** execution plans ready (peer-reviewed 2026-07-28) — **`phase-execution`** on `feat/finding-resolution` from P0.

**LOOP mode (operator):** Agent implements **one phase at a time**, runs gate + Bugbot, **commits locally** — **no push**. Operator pushes, validates Revy on staging, fills [FINDING_RESOLUTION_STAGING_VALIDATION.md](./FINDING_RESOLUTION_STAGING_VALIDATION.md), then requests next phase.

**Migration pause:** After P0.2 (`0028`), apply migration on staging/dev before P0.3+ or P1.

**Thesis:** How Revy decides a finding is **addressed**, **dismissed**, or **still open** — multi-pass closure after each push + resolution-rate metrics (Bugbot/Greptile-inspired).

| Doc | Purpose |
|-----|---------|
| [FINDING_RESOLUTION_FINDINGS.md](./FINDING_RESOLUTION_FINDINGS.md) | Baseline — current flow, gaps, industry patterns |
| [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](./FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) | Incident + staging DB evidence (not validation) |
| [FINDING_RESOLUTION_GENERAL_PLAN.md](./FINDING_RESOLUTION_GENERAL_PLAN.md) | P0–P5 phases, locked FR-Q*, multi-pass model |
| [FINDING_RESOLUTION_STAGING_VALIDATION.md](./FINDING_RESOLUTION_STAGING_VALIDATION.md) | Staging dogfood — fill per phase as outputs are checked |
| [waves/FINDING_RESOLUTION_EXECUTION.md](./waves/FINDING_RESOLUTION_EXECUTION.md) | LOOP index + locked decisions (incl. worker order, trace split) |

## Execution (LOOP order)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Closure model, migration `0028`, compare helper | [waves/FINDING_RESOLUTION_P0_EXECUTION.md](./waves/FINDING_RESOLUTION_P0_EXECUTION.md) | done (local) |
| P1 | Pass 1 stamp + Pass 2 reconcile closure | [waves/FINDING_RESOLUTION_P1_EXECUTION.md](./waves/FINDING_RESOLUTION_P1_EXECUTION.md) | pending |
| P2 | Pass 3 verification judge (5/run) | [waves/FINDING_RESOLUTION_P2_EXECUTION.md](./waves/FINDING_RESOLUTION_P2_EXECUTION.md) | pending |
| P3 | FR-Q12 metrics, G9, API fields | [waves/FINDING_RESOLUTION_P3_EXECUTION.md](./waves/FINDING_RESOLUTION_P3_EXECUTION.md) | done (local) |
| P4 | Human dismiss, summary parity, RG-6 | [waves/FINDING_RESOLUTION_P4_EXECUTION.md](./waves/FINDING_RESOLUTION_P4_EXECUTION.md) | done (local) |
| P5 | Staging validation + doc sync | [waves/FINDING_RESOLUTION_P5_EXECUTION.md](./waves/FINDING_RESOLUTION_P5_EXECUTION.md) | pending |

**Related shipped programs:** R5 reconcile + judge · RQ6 resolution metrics · github-surface-hardening Option A · generation lifecycle RG-Q10 · judge input quality.

**Next:** `phase-execution` from **P5** on `feat/finding-resolution` (P4 done locally).
