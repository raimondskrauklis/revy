# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Post-validation:** [FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **Track B in progress** — FR-DG2 sign-off after [#66](https://github.com/raimondskrauklis/revy/pull/66) deploy.

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | Pre-#64 history only |
| Post-#64 deploy (wave A) | `2026-07-29T17:50:43Z` | #65 wave A metrics |
| Post-#66 deploy (FR-DG2a) | `2026-07-29T19:20:33Z` | **Track B** FR-DG2 sign-off |

**Deploy evidence (#66):** workflow `30483659578` — merge `111e851` — job **Build, Push, and Deploy to Droplet** finished `2026-07-29T19:20:33Z`.

## Wave A (complete — PR #65)

FR-DG1 **PASS** rev 3; FR-DG2 **PARTIAL** rev 4 (RC-1). See #65 staging rows in git history / operator notes.

## Track B dogfood PR (FR-DG2 sign-off)

| PR | Branch | Status |
|----|--------|--------|
| *(open)* | `chore/fr-dg2-staging-dogfood` | push 1 in progress |

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dg2_probe` + Moonshot defect | in progress |
| 2 | Fix defect in-file (line touch) | pending |
| 3 | Delete probe file — **FR-DG2** target | pending |

**Protocol ([VAL8](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val8--dogfood-metrics-interpretation)):** backend-only pushes 1–3; one push per Revy cycle.

## Pass criteria — FR-DG2 (push 3)

| Check | Pass | Evidence |
|-------|------|----------|
| Target probe group `absent_and_addressed` on rev 3 | pending | DB `github_finding_groups` |
| `pr_active_count` stable or ↓ vs push 2 | pending | `summary_json` |
| Stale inline collapsed | pending | `github_inline_threads` + GitHub |

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | — | — | — | introduce probe |
| 2 | — | — | — | fix in-file |
| 3 | — | — | — | delete file — FR-DG2 |

## Metrics

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T19:20:33Z --json'
```
