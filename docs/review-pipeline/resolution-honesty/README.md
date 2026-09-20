# docs/review-pipeline/resolution-honesty/README.md

# Resolution honesty

**Status:** execution P0–P5 ready. Execution peer review pass 3 — **BLOCK phase-execution: no.**

**Trigger:** dogfood PR [rtudatadev-dotcom/revy-dogfood#1](https://github.com/rtudatadev-dotcom/revy-dogfood/pull/1) — four real code fixes, GitHub threads collapsed, comment still said **Resolved (lifetime) 0** and **this push 0/0**.

**Does not replace:** [finding-resolution](../finding-resolution/README.md) (how groups close) or [pr-summary-rollup](../pr-summary-rollup/README.md) (lifetime vs this-push *layout*). This slice is **whether the numbers and GitHub thread state tell the truth**. This program **supersedes FR-Q3** (Pass 2 needs `addressed`), PSR raised = non-superseded **forward**, and **R5-Q1** / D10 title+line fingerprint; it **keeps GH-Q9**.

**Authority:** [RESOLUTION_HONESTY_FINDINGS.md](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q1–Q12 · [RESOLUTION_HONESTY_GENERAL_PLAN.md](./RESOLUTION_HONESTY_GENERAL_PLAN.md)

| Doc | Purpose |
|-----|---------|
| [RESOLUTION_HONESTY_FINDINGS.md](./RESOLUTION_HONESTY_FINDINGS.md) | Baseline — identity, supersede, outdated, this-push vs lifetime |
| [RESOLUTION_HONESTY_GENERAL_PLAN.md](./RESOLUTION_HONESTY_GENERAL_PLAN.md) | P0–P5 — what we solve (not execution) |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Architecture peer review — pass 2 **BLOCK create-execution-plan: no** |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/README.md) | Execution peer review |

## Execution (LOOP)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Persistent identity cutover (`claim_slot`, continuation, retire peer supersede, inline keys) | [RESOLUTION_HONESTY_P0_EXECUTION.md](./RESOLUTION_HONESTY_P0_EXECUTION.md) | done (`98a3523`) |
| P1 | Honest H2 closure (Pass 2 without `addressed`; skip ambiguous leftovers) | [RESOLUTION_HONESTY_P1_EXECUTION.md](./RESOLUTION_HONESTY_P1_EXECUTION.md) | done (`6c674d0`) |
| P2 | This-push prior set = last published group ids; empty denom → N/A | [RESOLUTION_HONESTY_P2_EXECUTION.md](./RESOLUTION_HONESTY_P2_EXECUTION.md) | done (`5825547`) |
| P3 | Lifetime rollup / PSR-Q15 on new PRs | [RESOLUTION_HONESTY_P3_EXECUTION.md](./RESOLUTION_HONESTY_P3_EXECUTION.md) | done (`9c4d989`) |
| P4 | Comment copy + keep GH-Q9 Outdated UI collapse | [RESOLUTION_HONESTY_P4_EXECUTION.md](./RESOLUTION_HONESTY_P4_EXECUTION.md) | done (`83aa3bd`) |
| P5 | Equivalent new dogfood PR + doc-sync | [RESOLUTION_HONESTY_P5_EXECUTION.md](./RESOLUTION_HONESTY_P5_EXECUTION.md) | done |

**Depends:** P1 → P0 · P2 → P1 · P3 → P2 · P4 → P3 · P5 → P4.

**Next:** `phase-execution` from P0 when invoked. Do not start the LOOP from this status update.
