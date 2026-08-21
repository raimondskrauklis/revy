# Post-main staging validation (#89 + #92)

**Purpose:** Dogfood PR on `revy-staging` after [#89](https://github.com/raimondskrauklis/revy/pull/89) and [#92](https://github.com/raimondskrauklis/revy/pull/92) — **full index → review → publish cycles** on the validation PR, not idle system-wide windows.

**Dogfood PR #93:** closed. **#94** merged + deployed. **Push 4:** [#95](https://github.com/raimondskrauklis/revy/pull/95) (closed). **#96** merged + deployed — MRC P0/P1 validation: [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md). **#98** MRC-P2 merged + deployed (`2026-08-11T05:49:57Z`). **#99** MRC-P3 API exposure merged + deployed (`2026-08-11T07:40:23Z`).

---

## Deploy boundaries (cornerstone)

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| #89 generation lifecycle | `2026-08-10T11:18:54Z` | RG-15 worker code baseline |
| **#92 pipeline observability P0** | `2026-08-10T14:23:32Z` | PO P0 dogfood window — migration `0031` |
| **#94 RG-15 check UX** | `2026-08-10T15:28:53Z` | Queued GitHub check + probe scripts |
| **#96 model-run-capture** | `2026-08-10T19:35:30Z` | **MRC P0/P1 dogfood window** — migration `0032` |
| **#98 MRC-P2** | `2026-08-11T05:49:57Z` | Terminal `models_snapshot` writer |
| **#99 MRC-P3** | `2026-08-11T07:40:23Z` | Pipeline trace API exposure |

**Rule:** PO/RG-15 probes on closed #93/#95 use `--since 2026-08-10T14:23:32Z`. MRC probes use `--since 2026-08-10T19:35:30Z` on the **post-#96 dogfood PR** (not #96 — merged code cannot self-validate).

---

## Push protocol (#93 — closed)

| Push | `head_sha` | Intent | Outcome |
|------|------------|--------|---------|
| 1 | `9f01500` | Introduce probe v1 | completed run |
| 2 | `1a440e5` | Marker v2 | completed run |
| 3a | `7778d1e` | Interrupt test | index job superseded (burst w/ 3b) |
| 3b | `9034ae6` | Interrupt +1min | completed run |
| **4** | `e33cadd` | Post-#94 deploy: queued check probe | **done** — 1 superseded + 1 completed run |

**Interrupt lesson:** `gh pr checks Revy pending` ≠ worker active. Use staging DB `processing` rows. Celery backlog can delay webhooks ~2+ min.

**Real supersede evidence:** `e965292` → `d82c43c` (8s) — rev3 review `superseded`.

---

## Probe results (PR #97 — post-#96 deploy, 2026-08-10)

**Dogfood PR:** [#97](https://github.com/raimondskrauklis/revy/pull/97) · `--since 2026-08-10T19:35:30Z` · `head_sha` `79626fa`

| Gate | Result | Detail |
|------|--------|--------|
| MRC P0 `--mrc-p0-gate` | **PASS** | alembic `0032`; `2/2` embed manifest + step model |
| MRC P1 embed | **PASS** | `2` `index_embed` rows; parity `2/0` |
| MRC P1 judge/publish steps | **PARTIAL** | judge `0/2` (skipped); publish `1/2` (fallback path) |
| MRC P2 `models_snapshot` | **pending** | #98 deployed — re-run on new dogfood PR with `--since 2026-08-11T05:49:57Z` |
| PO P0 `--po-p0-gate` | **PASS** | 2 runs; 4 attempt rows |
| RG-15 `--rg15-gate` | **PASS** | no stuck processing |

```bash
cd backend
PR=97
SINCE=2026-08-10T19:35:30Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json
```

**Related:** [model-run-capture validation](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md)

---

## Probe results (PR #100 — post-#98/#99 deploy, 2026-08-11)

**Dogfood PR:** [#100](https://github.com/raimondskrauklis/revy/pull/100) · `--since 2026-08-11T05:49:57Z` · `head_sha` `c2925da`

| Gate | Result | Detail |
|------|--------|--------|
| MRC P0 `--mrc-gate` | **PASS** | alembic `0032`; `2/2` embed manifest + step model |
| MRC P1 embed | **PASS** | `2` `index_embed` rows; parity `2/0` |
| MRC P1 judge/publish steps | **PARTIAL** | judge `0/1` (skipped); publish `1/1` |
| MRC P2 `models_snapshot` | **PASS** | `with_snapshot=2/2` |
| MRC P3 trace API | **PASS** | snapshot + manifest `embedding_*` in DB |
| PO P0 `--po-p0-gate` | **PASS** | 2 runs; 3 attempt rows |
| RG-15 `--rg15-gate` | **PASS** | 1 superseded review run; no stuck processing |

```bash
cd backend
PR=100
SINCE=2026-08-11T05:49:57Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --mrc-gate --json
```

**Related:** [model-run-capture validation](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md)

---

## Probe results (staging DB — PR #93, script from #94 branch)

**2026-08-10** — local run against staging (no deploy needed for probe SQL fix):

| Gate | Result | Detail |
|------|--------|--------|
| PO P0 `--po-p0-gate` | **PASS** | 5 runs; `trigger_source`/`timing_stats`/`retrieve_ms` 5/5; 5 attempt rows |
| RG-15 `--rg15-gate` | **PASS** | `superseded_index_jobs=1` `superseded_review_runs=2`; 0 stuck `processing` |

```bash
cd backend
PR=93
SINCE=2026-08-10T14:23:32Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE --pr-number $PR --require-activity --rg15-gate --json
```

---

## Sign-off

| Track | Verdict | Evidence |
|-------|---------|----------|
| PO P0 behavioral (post-#92) | **PASS** | PR #93 pushes 1–2 + 3b; probes above |
| RG-15 supersede (DB) | **PASS** | 2 superseded review runs + 1 superseded index job in scope |
| RG-15 queued check UX | **PASS** (initial) | #95 push 4 post-#94 deploy; 2 runs, 1 superseded |
| PO P4 SLO (`--po-gate`) | **INCONCLUSIVE** | `wait_ms` null on success path until P1 |

**Next:** MRC program **complete** — staging sign-off PASS on [#100](https://github.com/raimondskrauklis/revy/pull/100).

**Related:** [model-run-capture validation](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md) · [pipeline observability](../pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) · [generation lifecycle](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md)

---

## Production window (2026-08-21 operator snapshot)

**Database:** `revy-staging` via `PRODUCTION_DATABASE_URL` (same DO cluster as `revy-dev` / `revy-test`). Cluster has **no** `revy` production database — live review traffic is this staging DB.

**Queried:** 2026-08-21T18:43Z · alembic `2026_08_10_1300_0032_github_pipeline_runs_models_snapshot` · tenant `Raimonds Krauklis` · GitHub App `raimondskrauklis`.

**Windows:** `--since 2026-08-07T00:00:00Z` (two-week lookback) and `--since 2026-08-11T07:40:23Z` (post-#99 deploy, fair MRC).

### Fleet

| Metric | All-time | Since 2026-08-07 |
|--------|----------|------------------|
| Review runs | 760 (first 2026-07-27, last 2026-08-20) | 411 |
| Completed / failed / superseded | 661 / 62 / 31 | 351 / 37 / 22 |
| PRs / revisions | 128 / 768 | — |
| Findings / groups | 1759 / 1756 | 893 findings |
| Publish jobs | 659 (619 completed, 38 `skipped_not_head`, 1 failed) | 336 completed in window |
| Code chunks | 252,534 | — |
| Repos | `revy` 62 PRs, `kp-platform` 34, `tender_pro` 32, `v2-kp_platform` 0 | kp-platform 252 runs, revy 159 |

Week of 2026-08-17 is quiet (18 runs vs 200–280 in prior weeks). Last completed run: 2026-08-20T19:34Z (`revy` #102).

### Gate results (system-wide, not dogfood-PR-scoped)

| Gate | Window | Verdict | Evidence |
|------|--------|---------|----------|
| PO P0 `--po-p0-gate` | Aug 7 | **PASS** | alembic `0032`; attempts table; `timing_stats`/`trigger_source`/`retrieve_ms` 215/411; 606 attempt rows |
| PO P4 `--po-gate` | Aug 7 | **PARTIAL** | Gate script PASSes (`review_wait_p95` set) but `wait_ms` is populated on **18/233** review attempts only — those 18 sit at ~840s (timeout path). Success-path wait still mostly null. Taxonomy: 587 success, 17 timeout, 1 rate_limit, 1 provider_error |
| RG-15 `--rg15-gate` | Aug 7 | **FAIL** | supersede path PASS (22 review + 2 index); **1 stuck `processing` run** `019fef5a-…` on `revy` #98 (`c630845`, retrieve, updated 2026-08-11T05:45Z — leftover, not current traffic). 5 `pending` rows from 2026-07-27–30 are older leftovers |
| MRC P0 `--mrc-gate` | post-#99 | **PASS** | embed manifest + step model **147/147**; reuse-null 12/12; false-reuse 0 |
| MRC P1 | post-#99 | **PARTIAL** | embed attempts 177/177 + parity 147/0; `models_snapshot` 155/159; judge step model **59/141**; publish **138/141** |
| RCX `--rcx-gate` | Aug 7 | **FAIL** | inject 124/351 + bytes p50 19014; **diff truncated 15.4%** (54/351, target &lt;5%); **omitted `.md` 54 runs** (target 0). Prompt p50/p95 **168,910 / 522,446** |
| Judge persistence | Aug 7 | **FAIL** vs ≥95% | 141 candidates, 88 with outcome (**62.4%**); 53 `parse_error=Anthropic response invalid`; 0 retries. Candidate runs: 211, outcomes 160, skipped_unavailable 82 |

```bash
cd backend
SINCE_2W=2026-08-07T00:00:00Z
SINCE_MRC=2026-08-11T07:40:23Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.pipeline_observability_staging_metrics \
  --since $SINCE_2W --po-p0-gate --po-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.generation_lifecycle_staging_metrics \
  --since $SINCE_2W --rg15-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.model_run_capture_staging_metrics \
  --since $SINCE_MRC --mrc-gate --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics \
  --since $SINCE_2W --rcx-gate --json
```

### Models in the window

| Signal | Value |
|--------|-------|
| Review / publish | `moonshot` / `kimi-k2.7-code` (389 review runs since Aug 7) |
| Embed through 2026-08-15 | `voyage-code-3.5` (170 index_embed attempts) |
| Embed from 2026-08-16 | **`voyage-code-4`** (34 attempts — live on staging worker) |

### Finding resolution (live, not dogfood-PR protocol)

| State / method | n |
|----------------|---|
| groups `resolved` | 566 |
| `judge_dismissed` + `absent_and_addressed` | 395 |
| `addressed` + `absent_and_addressed` | 65 |
| `judge_dismissed` + `judge_dismissed` | 43 |
| publish `resolution.addressed` sum (Aug 7+) | 265 across 170 jobs |
| `denominator_active_prior` jobs | 247 (sum 627) |

Does **not** close finding-resolution dogfood sign-off (that memo still needs the dedicated PR protocol). Shows Pass 1–2 style closure is happening on `kp-platform` / `revy` traffic.

### Operator notes

1. Stale `processing` on #98 (`019fef5a`) should be marked failed/superseded or the system-wide RG-15 gate will keep failing.
2. Judge RTU parse failures are still the dominant miss — persistence 62.4% vs 95% target; retries still 0.
3. RCX dogfood PASS (2-run, 2026-07-29) does **not** hold on two weeks of real PRs — truncation and omitted `.md` are back.
4. `voyage-code-4` has been the embed model since 2026-08-16 — relevant to [VOYAGE_CODE_4_FINDINGS.md](../../models/voyage-embeddings/VOYAGE_CODE_4_FINDINGS.md).
