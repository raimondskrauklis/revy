# docs/review-pipeline/staging-validation/POST_MAIN_STAGING_VALIDATION.md
# Post-main staging validation (#89 + #92)

**Purpose:** Dogfood PR on `revy-staging` after [#89](https://github.com/raimondskrauklis/revy/pull/89) (generation lifecycle) and [#92](https://github.com/raimondskrauklis/revy/pull/92) (pipeline observability P0) — **full index → review → publish cycles**, not system-wide idle windows.

**Fixture:** `backend/app/services/post_main_staging_probe.py`  
**Branch:** `chore/post-main-staging-dogfood`

---

## Deploy boundaries (cornerstone)

| Deploy | `--since` ISO | Validates |
|--------|---------------|-----------|
| #89 generation lifecycle | `2026-08-10T11:18:54Z` | RG-15 worker code on staging |
| **#92 pipeline observability P0** | `2026-08-10T14:23:32Z` | migration `0031` + recorder on worker |

**Rule:** Dogfood probes use **`--pr-number`** on the validation PR + **`--since 2026-08-10T14:23:32Z`** (post-#92). System-wide `--since` without a PR is baseline only.

---

## Dogfood PR

| PR | Branch | Status |
|----|--------|--------|
| TBD | `chore/post-main-staging-dogfood` | opening |

---

## Push protocol

| Push | Intent | Status |
|------|--------|--------|
| 1 | Add `post_main_staging_probe` — trigger autostart full cycle | pending |
| 2 | Bump marker while Revy **in_progress** (RG-15 supersede) | pending |

**After each push:** wait Revy idle → run probes (see below).

---

## Probe commands (per push, after Revy idle)

```bash
cd backend
PR=<n>
SINCE=2026-08-10T14:23:32Z

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.pipeline_observability_staging_metrics --since $SINCE --pr-number $PR --require-runs --po-p0-gate --json"

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.generation_lifecycle_staging_metrics --since $SINCE --pr-number $PR --require-activity --rg15-gate --json"

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  "python -m scripts.judge_json_contract_staging_metrics --since $SINCE --json"
```

---

## Results (operator — fill per push)

| Push | `head_sha` | Revy rev | `review_run_id` | PO P0 gate | RG-15 gate | Notes |
|------|------------|----------|-----------------|------------|------------|-------|
| 1 | — | — | — | pending | pending | |

---

## Sign-off

| Track | Verdict | Evidence |
|-------|---------|----------|
| PO P0 behavioral (post-#92 PR) | pending | `--po-p0-gate --require-runs` on dogfood PR |
| RG-15 supersede (push-2) | pending | `--rg15-gate` supersede_path PASS |
| System health (no stuck processing) | pending | `stuck_processing` PASS |

**Related memos:** [pipeline observability](../pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) · [generation lifecycle](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md)
