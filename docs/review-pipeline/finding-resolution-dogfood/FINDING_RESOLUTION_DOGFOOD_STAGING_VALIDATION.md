# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Post-validation:** [FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **Track B complete** — FR-DG2 **PARTIAL PASS** ([#67](https://github.com/raimondskrauklis/revy/pull/67) rev 3 `2c14e7d`).

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| Post-#66 deploy (FR-DG2a) | `2026-07-29T19:20:33Z` | Track B metrics |

## Track B — [#67](https://github.com/raimondskrauklis/revy/pull/67)

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce probe + defect | **PASS** — `893cf83` |
| 2 | Fix in-file | **done** — `79fef27` |
| 3 | Delete probe file — FR-DG2 | **PARTIAL PASS** — `2c14e7d` |

## Pass criteria — FR-DG2 (push 3 / rev 3)

| Check | Pass | Evidence |
|-------|------|----------|
| File-deletion `absent_and_addressed` (mechanism) | **PASS** | `019faf5b` closed rev 3 — `absent_and_addressed` |
| Push-1 cohort group `019faf58` closed | **FAIL** | still `active` — aged out of Pass 1 pairing on rev 3 |
| `transitions_addressed` ≥ 1 | **PASS** | `1` (manifest) |
| `pr_active_count` stable vs push 2 | **PASS** | 3 → 3 |
| Inline collapse | **partial** | 4 threads remain; probe cohort mixed |

**Rev 3 manifest:** `denominator_active_prior=2`, `transitions_addressed=1`, `resolution.addressed=1`, `judge_dismissed=1`.

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | `893cf83` | `019faf57-3bf2-77a8-814d-398603e4c406` | 1 / 1 | cohort `019faf58` introduced |
| 2 | `79fef27` | `019faf59-d82d-79db-b638-ce240b8dbadc` | 2 / 3 | orig `still_open`; `019faf5b` introduced |
| 3 | `2c14e7d` | `019faf5e-5b5f-7859-a243-efdd8a4e22c2` | 1 / 3 | `019faf5b` **absent_and_addressed**; `019faf58` orphan |

## Sign-off

| Gap | Result |
|-----|--------|
| **FR-DG2a** | **PASS** — file-deletion Pass 1 + Pass 2 closure on rev-adjacent cohort |
| **FR-DG2** | **PARTIAL PASS** — mechanism proven; push-1 orphan → [VAL10](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md#fr-dg-val10--pass-1-pairing-window-on-delete) |

## Metrics

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T19:20:33Z --json'
```
