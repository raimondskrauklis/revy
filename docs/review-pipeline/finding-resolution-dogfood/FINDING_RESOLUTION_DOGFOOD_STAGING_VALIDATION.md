# Finding resolution dogfood — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [FINDING_RESOLUTION_DOGFOOD_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_FINDINGS.md) · **Operator locks:** [FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md](./FINDING_RESOLUTION_DOGFOOD_VALIDATION_FINDINGS.md)

**Status:** **dogfood complete** — FR-DG1 **PASS** (rev 3); FR-DG2 **PARTIAL** (rev 4 — absent_and_addressed on rev 3 docs only; push 3 did not shrink `pr_active`).

## Deploy boundaries

| Boundary | `--since` ISO | Used for |
|----------|---------------|----------|
| PSA baseline (reference) | `2026-07-29T11:38:12Z` | Pre-#64 history only |
| Post-#64 deploy (P1+P2) | `2026-07-29T17:50:43Z` | Dogfood push 2–3; FR-DG1/FR-DG2 metrics |
| Post-push-2c | `2026-07-29T18:44:05Z` | Rev 3 FR-DG1 publish window |
| Post-push-3 | `2026-07-29T18:49:59Z` | Rev 4 FR-DG2 publish window |

**Deploy evidence:** workflow `30476822659` — merge `f0b12d5` — job **Build, Push, and Deploy to Droplet** finished `2026-07-29T17:50:43Z`.

## Dogfood PRs

| PR | Branch | Status |
|----|--------|--------|
| [#64](https://github.com/raimondskrauklis/revy/pull/64) (merged) | `chore/finding-resolution-staging-dogfood` | wave A code + push 1 |
| [#65](https://github.com/raimondskrauklis/revy/pull/65) (open) | `chore/finding-resolution-staging-dogfood` | push 2a–3 complete |

## Dogfood pushes

| Push | Intent | Status |
|------|--------|--------|
| 1 | Introduce `fr_dogfood` probe (#64) | **PASS** — `5bb55ea` |
| 2a | Wire probe | **PASS** — `cdea3cc` (0 findings — VAL6) |
| 2b | Introduce review findings (rev 2) | **PASS** — `b3ccd86` (3 active) |
| 2c | Fix push — **FR-DG1** sign-off (rev 3) | **PASS** — `9d32ea2` |
| 3 | Remove probe — **FR-DG2** (rev 4) | **PARTIAL** — `66d64e5` |
| 4 | Optional regrowth | N/A |

## Pass criteria — FR-DG1 (push 2c / rev 3)

| Check | Pass | Evidence |
|-------|------|----------|
| `denominator_active_prior` ≥ 1 | **PASS** | `3` (reconcile `resolution_pass`) |
| `transitions_addressed` ≥ 1 | **PASS** | `2` |
| G9 not `n/a` | **PASS** | resolution block wired from manifest |
| `summary_json.resolution.addressed` ≥ 1 | **PASS** | `2` |

**Rev 3 row:** `019faf31-0671-7069-9732-6e057a45e077` — `gen=2`, `pr=3`, `resolution.addressed=2`.

## Pass criteria — FR-DG2 (push 3 / rev 4)

| Check | Pass | Evidence |
|-------|------|----------|
| `pr_active_count` shrinks vs push 2c | **FAIL** | `3` → `7` (rev 3 → rev 4) |
| Stale inline collapsed | **FAIL** | inline map `5` → `8` entries; prior threads retained |
| Group `resolved` + `absent_and_addressed` on rev 4 | **FAIL** | `0` closures on rev 4 |
| Pass 2 mechanism (any rev) | **PASS** | `2` groups `absent_and_addressed` on rev 3 (doc fixes) |

**Rev 4 row:** `019faf36-7090-794c-ad6e-bdd77d5f20d2` — `gen=5`, `pr=7`, `resolution.addressed=0`, `denominator_active_prior=1`, `transitions_addressed=0`.

**FR-DG2 gap notes (rev 4):**

- Original `probe_module.py` group (`019faf29-9c6e`) stayed **active** after file deletion — no `resolution_status=addressed` on 2c for that fingerprint, so Pass 2 did not close it.
- Push 3 surfaced **5 new generation findings** about probe removal / memo state (meta dogfood noise), inflating `pr_active_count`.
- Two doc groups from rev 2 closed **`absent_and_addressed` on rev 3** (2c fix) — proves Pass 2 path when Pass 1 stamps addressed; not rev 4 probe removal.

## Results (operator)

| Push | `head_sha` | `review_run_id` | `gen` / `pr` | Notes |
|------|------------|-----------------|--------------|-------|
| 1 | `5bb55ea` | `019fae9b-afb0-7229-a827-992382310366` | 0 / 0 | #64 rev 1 |
| 2a | `cdea3cc` | `019faf0d-469b-70ef-8815-5a6dd119a51a` | 0 / 0 | #65 rev 1 — VAL6 |
| 2b | `b3ccd86` | `019faf28-1dc4-7198-9ed0-fb50f298ac9d` | 3 / 3 | #65 rev 2; `denom=0` (no rev1 cohort) |
| 2c | `9d32ea2` | `019faf31-0671-7069-9732-6e057a45e077` | 2 / 3 | FR-DG1 **PASS** — denom=3, addressed=2 |
| 3 | `66d64e5` | `019faf36-7090-794c-ad6e-bdd77d5f20d2` | 5 / 7 | FR-DG2 **PARTIAL** — no rev4 closures; pr↑ |

## Metrics (post-deploy window)

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T17:50:43Z --json'
```

**Window aggregate (after rev 4):** `completed_jobs=4`, `denominator_active_prior_sum=4`, `transitions_addressed_sum=2`, `resolution_addressed_sum=2`, `pr_active_count_p50=3`.

## Sign-off summary

| Gap | Staging result |
|-----|----------------|
| **FR-DG1** | **PASS** — manifest + G9 + `summary_json.resolution` on rev 3 |
| **FR-DG2** | **PARTIAL** — `absent_and_addressed` proven on rev 3 doc cohort; probe removal on rev 4 did not shrink block 2 or close stale probe group |

**Follow-up:** FR-DG2 probe-removal path — [post-validation findings](./FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) Track A (code) + Track B (repro). Merge #65 for FR-DG1; **not** FR-DG2 sign-off.
