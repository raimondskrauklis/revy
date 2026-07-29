# Review engineering context — program index

**Status:** P0–P4 shipped on `main` (#60) · **P6–P8 closeout wave** ready for `phase-execution`.

**Problem:** Revy Moonshot has engineering-context inject (P2). **Closeout:** Greptile-depth issue comment (P6), operator API + metrics gate (P7), staging sign-off (P8).

| Doc | Purpose |
|-----|---------|
| [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) | Baseline — RCX-D1–D17, Wave 2, validation metrics |
| [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](./REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md) | Phases P0–P8 — execution authority |
| [waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md) | LOOP index + locked execution decisions |

## Execution table

| Phase | File | Status |
|-------|------|--------|
| P0 — Foundations | Migration `0029`, SSOT, caps (settings only), path-exists pytest | [waves/REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md) | done |
| P1 — Loader + extract | [waves/REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md) | done |
| P2 — Moonshot inject | [waves/REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md) | done |
| P3 — Greptile sync | [waves/REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md) | done |
| P4 — Judge reuse | [waves/REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md) | done |
| P5 — Validation stub | Memo + P5.5 moved to P6 | [waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md) | stub done |
| P6 — Publish surface | Greptile-depth issue comment | [waves/REVIEW_ENGINEERING_CONTEXT_P6_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P6_EXECUTION.md) | done |
| P7 — Operator visibility | `context_stats` API + `--rcx-gate` | [waves/REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md) | planned |
| P8 — Closeout | Staging validation + sign-off | [waves/REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md](./waves/REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md) | human gate |

**Supersedes:** [RQ-RC-1](../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) dogfood items (RC1, RC2, RC5 inject).

**Related:** [review-quality/README.md](../review-quality/README.md) · [judge-json-contract](../judge-json-contract/README.md) · [post-review-quality L2](../post-review-quality/POST_REVIEW_QUALITY_FINDINGS.md)

**Next step:** `phase-execution` → **P6** (real `backend/**` PR = dogfood + RCX validation).

**Program status:** P0–P4 code shipped · P6–P8 execution plans ready · staging human gate pending.
