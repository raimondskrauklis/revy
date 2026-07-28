# Review engineering context — program index

**Status:** Execution plans ready — `phase-execution` from P0.

**Problem:** Revy Moonshot has no engineering-context layer. Greptile loads 15 programs from `files.json`. **RCX P2** = Moonshot inject; **P3** = Greptile generated from SSOT; Bugbot manual.

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — RCX-D1–D12, validation metrics |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](./REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | Phases P0–P5 — execution authority |
| [waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md) | LOOP index + locked execution decisions |

## Execution table

| Phase | File | Status |
|-------|------|--------|
| P0 — Foundations | Migration `0029`, SSOT, caps (settings only), path-exists CI | [waves/REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md) | done |
| P1 — Loader + extract | [waves/REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md) | done |
| P2 — Moonshot inject | [waves/REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md) | pending |
| P3 — Greptile sync | [waves/REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md) | pending |
| P4 — Judge reuse | [waves/REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md) | pending |
| P5 — Validation + closeout | [waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md) | pending |

**Branch:** `docs/judge-json-contract-staging-validation` — **docs + code ship in one PR** (agent context for Greptile/Bugbot).

**Supersedes:** [RQ-RC-1](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) dogfood items (RC1, RC2, RC5 inject).

**Related:** [review-quality/README.md](../review-quality/README.md) · [judge-json-contract](../judge-json-contract/README.md)

**Next step:** `phase-execution` → P0 (migration `0029` — LOOP pauses after P0.1).
