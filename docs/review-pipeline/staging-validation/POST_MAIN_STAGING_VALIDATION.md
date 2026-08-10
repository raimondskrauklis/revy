# Post-main staging validation (#89 + #92)

**Purpose:** Dogfood PR on `revy-staging` after [#89](https://github.com/raimondskrauklis/revy/pull/89) and [#92](https://github.com/raimondskrauklis/revy/pull/92) — **full index → review → publish cycles** on the validation PR, not idle system-wide windows.

**Dogfood PR #93:** closed — evidence captured below. **Ship PR:** [#94](https://github.com/raimondskrauklis/revy/pull/94) (queued check UX + probe scripts) → **deploy required** before push 4.

---

## Deploy boundaries (cornerstone)

| Deploy | `--since` ISO | Role |
|--------|---------------|------|
| #89 generation lifecycle | `2026-08-10T11:18:54Z` | RG-15 worker code baseline |
| **#92 pipeline observability P0** | `2026-08-10T14:23:32Z` | **Dogfood window** — migration `0031` + recorder |
| **#94 RG-15 check UX** | _pending merge + deploy_ | Queued GitHub check + probe script fix |

**Rule:** Probes use `--pr-number 93 --since 2026-08-10T14:23:32Z`. Run scripts from `main` after #94 merge.

---

## Push protocol (#93 — closed)

| Push | `head_sha` | Intent | Outcome |
|------|------------|--------|---------|
| 1 | `9f01500` | Introduce probe v1 | completed run |
| 2 | `1a440e5` | Marker v2 | completed run |
| 3a | `7778d1e` | Interrupt test | index job superseded (burst w/ 3b) |
| 3b | `9034ae6` | Interrupt +1min | completed run |
| **4** | _TBD_ | Post-#94 deploy: queued check + overlap supersede | **after deploy** |

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
| RG-15 queued check UX | **pending deploy #94** | needs push 4 after staging deploy |
| PO P4 SLO (`--po-gate`) | **INCONCLUSIVE** | `wait_ms` null on success path until P1 |

**Next:** merge [#94](https://github.com/raimondskrauklis/revy/pull/94) → staging deploy → new dogfood PR push 4.

**Related:** [pipeline observability](../pipeline-observability/PIPELINE_OBSERVABILITY_STAGING_VALIDATION.md) · [generation lifecycle](../review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md)
