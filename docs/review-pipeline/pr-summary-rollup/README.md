# PR summary rollup — program index

**Status:** **shipped** (P0–P3 code) — [staging validation](./PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md) operator sign-off pending post-deploy.

**Thesis:** GitHub issue comment and check run expose **two honest time horizons**: **PR lifetime** (rollup) and **this push** (FR-Q12 manifest). Persisted rollup on every publish from day one.

**Depends on:** [publish-summary-alignment](../publish-summary-alignment/README.md) (PSA), [still-open-summary-dogfood](../still-open-summary-dogfood/README.md) (SOS-5, [#84](https://github.com/raimondskrauklis/revy/pull/84) merged), [finding-resolution](../finding-resolution/README.md) (FR-Q12).

| Doc | Purpose |
|-----|---------|
| [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md) | Baseline — manifest, PSR-Q1–Q10, pass-01 locks |
| [PR_SUMMARY_ROLLUP_GENERAL_PLAN.md](./PR_SUMMARY_ROLLUP_GENERAL_PLAN.md) | P0–P3 phases |
| [waves/PR_SUMMARY_ROLLUP_EXECUTION.md](./waves/PR_SUMMARY_ROLLUP_EXECUTION.md) | LOOP index — P0–P3 |
| [reviews/architecture-peer-review/](./reviews/architecture-peer-review/README.md) | Peer review — pass 1 (2026-08-08) |
| [PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md](./PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md) | Staging dogfood memo (operator sign-off pending) |

## Execution (LOOP)

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Migration, rollup module, compute + persist | [P0](./waves/PR_SUMMARY_ROLLUP_P0_EXECUTION.md) | Done (`3b8ae99`) |
| P1 | Formatter surfaces (comment + check) | [P1](./waves/PR_SUMMARY_ROLLUP_P1_EXECUTION.md) | Done (`6dd7335`) |
| P2 | Moonshot + API + dogfood + trace | [P2](./waves/PR_SUMMARY_ROLLUP_P2_EXECUTION.md) | Done (`6af9c64`) |
| P3 | Staging sign-off + doc sync | [P3](./waves/PR_SUMMARY_ROLLUP_P3_EXECUTION.md) | Done (code); [staging memo](./PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md) pending |

**Next:** Deploy P0–P2 to staging → run dogfood `--psr-gate` → fill [staging memo](./PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md) sign-off.
