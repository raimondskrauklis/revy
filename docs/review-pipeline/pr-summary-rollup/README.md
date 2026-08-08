# PR summary rollup — program index

**Status:** **execution plans** (P0–P3) — `execution-peer-review` pass 1 complete; ready for `phase-execution`.

**Thesis:** GitHub issue comment and check run expose **two honest time horizons**: **PR lifetime** (rollup) and **this push** (FR-Q12 manifest). Persisted rollup on every publish from day one.

**Depends on:** [publish-summary-alignment](../publish-summary-alignment/README.md) (PSA), [still-open-summary-dogfood](../still-open-summary-dogfood/README.md) (SOS-5, [#84](https://github.com/raimondskrauklis/revy/pull/84) merged), [finding-resolution](../finding-resolution/README.md) (FR-Q12).

| Doc | Purpose |
|-----|---------|
| [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md) | Baseline — manifest, PSR-Q1–Q10, pass-01 locks |
| [PR_SUMMARY_ROLLUP_GENERAL_PLAN.md](./PR_SUMMARY_ROLLUP_GENERAL_PLAN.md) | P0–P3 phases |
| [waves/PR_SUMMARY_ROLLUP_EXECUTION.md](./waves/PR_SUMMARY_ROLLUP_EXECUTION.md) | LOOP index — P0–P3 |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Peer review — pass 1 (2026-08-08) |
| [reviews/execution-peer-review/](./reviews/execution-peer-review/README.md) | Execution peer review — pass 1 (2026-08-08) |

## Execution (LOOP)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Migration, rollup module, compute + persist | [P0](./waves/PR_SUMMARY_ROLLUP_P0_EXECUTION.md) | Done (`3b8ae99`) |
| P1 | Formatter surfaces (comment + check) | [P1](./waves/PR_SUMMARY_ROLLUP_P1_EXECUTION.md) | pending |
| P2 | Moonshot + API + dogfood + trace | [P2](./waves/PR_SUMMARY_ROLLUP_P2_EXECUTION.md) | pending |
| P3 | Staging sign-off + doc sync | [P3](./waves/PR_SUMMARY_ROLLUP_P3_EXECUTION.md) | pending |

**Next:** `phase-execution` on `feat/pr-summary-rollup` from `main`.
