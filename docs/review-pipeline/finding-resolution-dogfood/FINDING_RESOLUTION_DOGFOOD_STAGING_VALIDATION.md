# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **push 3 in progress** — FR-DG1 PASS on rev 3 (`9d32ea2`); FR-DG2 sign-off after probe removal + Revy.

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | Pre-#64 history only |
| Post-#64 deploy (P1+P2) | `2026-07-29T17:50:43Z` | Dogfood push 2–3; FR-DG1/FR-DG2 metrics |
| Post-push-2c | `2026-07-29T18:44:05Z` | Rev 3 FR-DG1 publish window |

**Deploy evidence:** workflow `30476822659` — merge `f0b12d5` — job **Build, Push, and Deploy to Droplet** finished `2026-07-29T17:50:43Z`.

## Dogfood PRs

| PR | Branch | Status |
|----|--------|--------|
| [#64](https://github.com/raimondskrauklis/revy/pull/64) (merged) | `chore/finding-resolution-staging-dogfood` | wave A code + push 1 |
| [#65](https://github.com/raimondskrauklis/revy/pull/65) (open) | `chore/finding-resolution-staging-dogfood` | push 2a–3 continuation |

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dogfood` probe (#64) | **PASS** — `5bb55ea` |
| 2a | Wire probe | **PASS** — `cdea3cc` (0 findings — VAL6) |
| 2b | Introduce review findings (rev 2) | **PASS** — `b3ccd86` (3 active) |
| 2c | Fix push — **FR-DG1** sign-off (rev 3) | **PASS** — `9d32ea2` |
| 3 | Remove probe — **FR-DG2** | in progress |
| 4 | Optional regrowth | N/A |

## Pass criteria — FR-DG1 (push 2c / rev 3)

| Check | Pass | Evidence |
|-------|------|----------|
| `denominator_active_prior` ≥ 1 | **PASS** | `3` (reconcile `resolution_pass`) |
| `transitions_addressed` ≥ 1 | **PASS** | `2` |
| G9 not `n/a` | **PASS** | resolution block wired from manifest |
| `summary_json.resolution.addressed` ≥ 1 | **PASS** | `2` (post-deploy window aggregate) |

**Window aggregate** (`--since 2026-07-29T17:50:43Z`): `denominator_active_prior_sum=3`, `transitions_addressed_sum=2`, `resolution_addressed_sum=2`, `jobs_with_denominator_active_prior=1`, `jobs_with_resolution_addressed=1`.

## Pass criteria — FR-DG2 (push 3)

| Check | Pass | Evidence |
|-------|------|----------|
| `pr_active_count` shrinks vs push 2c | pending | `summary_json` |
| Stale inline collapsed | pending | GitHub + `github_inline_threads` |
| Group `resolved` + `absent_and_addressed` | pending | DB |

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | `5bb55ea` | `019fae9b-afb0-7229-a827-992382310366` | 0 / 0 | #64 rev 1 |
| 2a | `cdea3cc` | `019faf0d-469b-70ef-8815-5a6dd119a51a` | 0 / 0 | #65 rev 1 — VAL6 |
| 2b | `b3ccd86` | `019faf28-1dc4-7198-9ed0-fb50f298ac9d` | 3 / 3 | #65 rev 2; `denom=0` (no rev1 cohort) |
| 2c | `9d32ea2` | `019faf31-0671-7069-9732-6e057a45e077` | 2 / 3 | FR-DG1 **PASS** — denom=3, addressed=2 |
| 3 | — | — | — | FR-DG2 target |

## Metrics (post-deploy window)

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T17:50:43Z --json'
```

Paste push 3 row when FR-DG2 validated.
