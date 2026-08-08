# docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md

# PR summary rollup — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PR_SUMMARY_ROLLUP_FINDINGS.md](./PR_SUMMARY_ROLLUP_FINDINGS.md)

**Status:** *pending operator sign-off* — memo stub created 2026-08-08; fill after P2 deploy to staging.

---

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSR P0–P2 merge | TBD | first metrics window after deploy |
| Post-deploy dogfood | TBD | fill after next `main` deploy |

**Rule:** Use deploy job completion time, not merge time.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| TBD | `feat/pr-summary-rollup` | [#85](https://github.com/raimondskrauklis/revy/pull/85) — pre-staging |

---

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Baseline rev 1 — PR summary + rollup persist | pending |
| 2 | Rev ≥2 — lifetime + push delta parity | pending |
| 3 | Cleanup / regrowth (if applicable) | pending |

---

## Pass criteria — push 2

| Check | Pass | Evidence |
|-------|------|----------|
| Issue comment has `### PR summary (lifetime)` before G9 | pending | — |
| `pr_resolution_rollup` on completed publish job `summary_json` | pending | — |
| `github_pull_requests.pr_resolution_rollup` matches job manifest | pending | — |
| `still_open_display` equals block-2 row count | pending | — |
| Dogfood `--psr-gate` green | pending | — |

---

## Pass criteria — push 3

| Check | Pass | Evidence |
|-------|------|----------|
| Check run one-liners (lifetime + this push) | pending | — |
| API `GET publish-job` returns `pr_resolution_rollup` | pending | — |

---

## Results (operator)

| Push | `head_sha` | Notes |
|------|------------|-------|
| 1 | — | pending |

**Script:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --repo raimondskrauklis/revy --pr-number <N> --psr-gate
```

---

## Sign-off

| Check | Status | Evidence |
|-------|--------|----------|
| Staging PASS | pending | Operator: run dogfood on multi-revision PR post-deploy |

**Note:** SOS P2 sign-off may still be open — document here if orphan-filter dependency observed; does not block PSR code ship.

---

## Doc sync (P3)

| Doc | Change |
|-----|--------|
| `README.md` | Program shipped + link this memo |
| `waves/PR_SUMMARY_ROLLUP_EXECUTION.md` | P0–P3 Done + sha |
| `PR_SUMMARY_ROLLUP_GENERAL_PLAN.md` | Execution index → shipped |
