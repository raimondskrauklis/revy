# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **push 2a in progress** — #64 merged + deployed; FR-DG1 sign-off on push 2b (rev ≥ 2).

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | Pre-#64 history only |
| Post-#64 deploy (P1+P2) | `2026-07-29T17:50:43Z` | Dogfood push 2–3; FR-DG1/FR-DG2 metrics |
| Post-push-2b | *(TBD)* | Optional narrow window after FR-DG1 fix publish |

**Deploy evidence:** workflow `30476822659` — merge `f0b12d5` — job **Build, Push, and Deploy to Droplet** finished `2026-07-29T17:50:43Z`.

## Dogfood PRs

| PR | Branch | Status |
|----|--------|--------|
| [#64](https://github.com/raimondskrauklis/revy/pull/64) (merged) | `chore/finding-resolution-staging-dogfood` | wave A code + push 1 |
| *(open)* | `chore/finding-resolution-staging-dogfood` | push 2a–3 continuation |

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dogfood` probe (#64) | **PASS** — `5bb55ea` |
| 2a | Wire probe — active finding | in progress |
| 2b | Fix push — **FR-DG1** sign-off | pending (after 2a + Revy) |
| 3 | Remove probe — **FR-DG2** | pending (after 2b + Revy) |
| 4 | Optional regrowth | N/A |

## Pass criteria — FR-DG1 (push 2b only)

| Check | Pass | Evidence |
|-------|------|----------|
| `denominator_active_prior` ≥ 1 | pending | reconcile `resolution_pass` |
| `transitions_addressed` ≥ 1 | pending | reconcile `resolution_pass` |
| G9 not `n/a` | pending | issue comment |
| `summary_json.resolution.addressed` ≥ 1 | pending | publish job |

## Pass criteria — FR-DG2 (push 3)

| Check | Pass | Evidence |
|-------|------|----------|
| `pr_active_count` shrinks vs push 2b | pending | `summary_json` |
| Stale inline collapsed | pending | GitHub + `github_inline_threads` |
| Group `resolved` + `absent_and_addressed` | pending | DB |

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | `5bb55ea` | `019fae9b-afb0-7229-a827-992382310366` | 0 / 0 | #64 rev 1; probe unused; judge dismissed 1 FP |
| 2a | — | — | — | pending |
| 2b | — | — | — | FR-DG1 target |
| 3 | — | — | — | FR-DG2 target |

## Metrics (post-deploy window)

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T17:50:43Z --json'
```

Paste snippet in push 2b/3 rows when filled.
