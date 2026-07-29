# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Post-validation:** [FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **Track B push 3 in progress** — FR-DG2 sign-off after probe file deletion.

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | Pre-#64 history only |
| Post-#64 deploy (wave A) | `2026-07-29T17:50:43Z` | #65 wave A metrics |
| Post-#66 deploy (FR-DG2a) | `2026-07-29T19:20:33Z` | **Track B** FR-DG2 sign-off |

**Deploy evidence (#66):** workflow `30483659578` — merge `111e851` — job **Build, Push, and Deploy to Droplet** finished `2026-07-29T19:20:33Z`.

## Track B dogfood PR — [#67](https://github.com/raimondskrauklis/revy/pull/67)

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dg2_probe` + Moonshot defect | **PASS** — `893cf83` (gen=1, pr=1) |
| 2 | Fix defect in-file | **done** — `79fef27` (denom=1; orig group `still_open`; +2 new findings) |
| 3 | Delete probe file — **FR-DG2** | in progress |

**Target group (push 1 cohort):** `019faf58-ad7e-7f6a-b7b4-64e33fa01f38` — `probe_module.py`

## Pass criteria — FR-DG2 (push 3)

| Check | Pass | Evidence |
|-------|------|----------|
| Target probe group `absent_and_addressed` on rev 3 | pending | DB |
| `pr_active_count` stable or ↓ vs push 2 | pending | `summary_json` |
| Stale inline collapsed | pending | `github_inline_threads` |

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | `893cf83` | `019faf57-3bf2-77a8-814d-398603e4c406` | 1 / 1 | probe defect active |
| 2 | `79fef27` | `019faf59-d82d-79db-b638-ce240b8dbadc` | 2 / 3 | denom=1; addressed=0; orig `still_open` |
| 3 | — | — | — | delete file — FR-DG2 (#66 Pass 1) |

## Metrics

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T19:20:33Z --json'
```
