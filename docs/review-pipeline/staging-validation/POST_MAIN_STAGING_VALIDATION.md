# Post-main staging validation (#89 + #92)

**Purpose:** Dogfood PR on `revy-staging` after [#89](https://github.com/raimondskrauklis/revy/pull/89) and [#92](https://github.com/raimondskrauklis/revy/pull/92) — **full index → review → publish cycles** on the validation PR, not idle system-wide windows.

**Dogfood PR #93:** closed. **#94** merged + deployed. **Push 4:** [#95](https://github.com/raimondskrauklis/revy/pull/95) (closed). **#96** merged + deployed — MRC validation: [MODEL_RUN_CAPTURE_STAGING_VALIDATION.md](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md).

---

## Deploy boundaries (cornerstone)

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| #89 generation lifecycle | `2026-08-10T11:18:54Z` | RG-15 worker code baseline |
| **#92 pipeline observability P0** | `2026-08-10T14:23:32Z` | PO P0 dogfood window — migration `0031` |
| **#94 RG-15 check UX** | `2026-08-10T15:28:53Z` | Queued GitHub check + probe scripts |
| **#96 model-run-capture** | `2026-08-10T19:35:30Z` | **MRC dogfood window** — migration `0032` + P0/P1 |

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

**Next:** open MRC dogfood PR (`chore/mrc-staging-dogfood`) — push 6 probe + full pipeline gate. Optional push 5 overlap supersede on closed #95 track.

**Related:** [model-run-capture validation](../models/model-run-capture/MODEL_RUN_CAPTURE_STAGING_VALIDATION.md) · [pipeline observability](../pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) · [generation lifecycle](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md)
