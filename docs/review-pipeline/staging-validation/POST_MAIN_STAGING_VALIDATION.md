# Post-main staging validation (#89 + #92)

**Purpose:** Dogfood PR on `revy-staging` after [#89](https://github.com/raimondskrauklis/revy/pull/89) and [#92](https://github.com/raimondskrauklis/revy/pull/92) — **full index → review → publish cycles** on the validation PR, not idle system-wide windows.

**PR:** [#93](https://github.com/raimondskrauklis/revy/pull/93) · **Branch:** `chore/post-main-staging-dogfood`  
**Fixture:** `backend/app/services/post_main_staging_probe.py`

---

## Deploy boundaries (cornerstone)

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| #89 generation lifecycle | `2026-08-10T11:18:54Z` | RG-15 worker code baseline |
| **#92 pipeline observability P0** | `2026-08-10T14:23:32Z` | **Dogfood window** — migration `0031` + recorder |

**Rule:** Probes use `--pr-number 93 --since 2026-08-10T14:23:32Z`. System-wide `--since` without PR is calibration only.

---

## Push protocol

| Push | `head_sha` | Intent | Status |
|------|------------|--------|--------|
| 1 | `9f01500` | Introduce `post_main_staging_probe` v1 | **done** — Revy `skipping` |
| 2 | `1a440e5` | Bump marker v2 (sequential; supersede needs in-flight overlap) | **done** — Revy `skipping` |

---

## Results (staging DB — PR #93)

| Push | `review_run_id` | Revy rev | PO P0 | RG-15 | Notes |
|------|-----------------|----------|-------|-------|-------|
| 1 | `019fec1a-1eec-7bce-a74d-a079b3584351` | 1 | **PASS** | activity PASS | `trigger_source` + `timing_stats.retrieve_ms` + 1 attempt row |
| 2 | `019fec1f-5552-7150-8b37-16b3bea202ec` | 2 | **PASS** | activity PASS | 2/2 runs complete; publish parity OK |

### Push 2 aggregate (`--po-p0-gate --require-runs`)

| Metric | Value |
|--------|-------|
| Completed review runs | **2/2** |
| `trigger_source` | **2/2** |
| `timing_stats` + `retrieve_ms` | **2/2** |
| `failure_stage` | **2/2** |
| Attempt rows | **2** (review step) |
| Superseded index jobs | **0** (sequential pushes — RG-15 overlap not exercised) |

---

## Probe commands

```bash
cd backend
PR=93
SINCE=2026-08-10T14:23:32Z

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.pipeline_observability_staging_metrics --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json"

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.generation_lifecycle_staging_metrics --since $SINCE --pr-number $PR --require-activity --rg15-gate --json"
```

---

## Sign-off

| Track | Verdict | Evidence |
|-------|---------|----------|
| PO P0 behavioral (post-#92) | **PASS** | PR #93 push 1–2; `timing_stats=2/2 trigger_source=2/2 retrieve_ms=2/2`; 2 attempt rows |
| RG-15 full cycle health | **PASS** | 2 completed runs, 2 index jobs, 0 `processing` orphans |
| RG-15 supersede during run | **pending** | need push while Revy `in_progress` (overlap) |
| PO P4 SLO (`--po-gate`) | **INCONCLUSIVE** | `wait_ms` null on success path until P1 |

**Related:** [pipeline observability](../pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) · [generation lifecycle](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md)
