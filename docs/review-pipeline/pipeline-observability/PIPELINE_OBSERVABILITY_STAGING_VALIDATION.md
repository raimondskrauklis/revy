# Pipeline observability — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [PIPELINE_OBSERVABILITY_FINDINGS.md](./PIPELINE_OBSERVABILITY_FINDINGS.md)

**Status:** **P0 schema PASS** · **P0 behavioral pending** (no post-#92 review runs on staging yet).

**Metrics script:** `backend/scripts/pipeline_observability_staging_metrics.py` — [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

---

## Deploy boundaries

| Boundary | `--since` ISO | Deploy job | Notes |
|----------|---------------|------------|-------|
| Generation lifecycle #89 | `2026-08-10T11:18:54Z` | [Actions #31382638736](https://github.com/raimondskrauklis/revy/actions/runs/31382638736) | RG-15 restart path on worker |
| **Pipeline observability P0 #92** | `2026-08-10T14:23:32Z` | [Actions #31397517476](https://github.com/raimondskrauklis/revy/actions/runs/31397517476) | migration `0031` + recorder on worker |

**Rule:** P0 sign-off uses **`--since` #92** for behavioral rows. Schema checks are valid immediately after #92 deploy.

```bash
cd backend

# P0 schema gate (post-#92 deploy)
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.pipeline_observability_staging_metrics --since 2026-08-10T14:23:32Z --po-p0-gate --json'

# P4 SLO gate (when attempt rows exist)
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.pipeline_observability_staging_metrics --since 2026-08-10T14:23:32Z --po-gate --json'
```

---

## System probe — 2026-08-10 (operator)

**Database:** `revy-staging` · **alembic:** `2026_08_10_1200_0031_pipeline_observability`

### Post-#92 window (`--since 2026-08-10T14:23:32Z`)

| Check | Status | Evidence |
|-------|--------|----------|
| Alembic `0031` | **PASS** | `alembic_0031` gate |
| `github_llm_call_attempts` table | **PASS** | `attempts_table` gate |
| Review runs in window | **0** | no staging traffic post-deploy |
| `trigger_source` / `timing_stats` populated | **pending** | needs ≥1 review run post-#92 |
| Attempt rows | **pending** | P0 timeout path only; P1 adds success tokens |

**`--po-p0-gate`:** **PASS** (schema checks; column/attempt checks `INCONCLUSIVE` — no runs in window).

### Post-#89 window (`--since 2026-08-10T11:18:54Z`) — context only

| Metric | Value | Notes |
|--------|-------|-------|
| Review runs | 6 completed | pre-#92 code — no observability columns |
| `with_trigger_source` | 0/6 | expected — runs predate P0 deploy |
| `with_timing_stats` | 0/6 | expected — runs predate P0 deploy |
| Attempt rows | 0 | expected — recorder not on worker yet |

---

## Pass criteria — P0 schema (post-#92 deploy)

| Check | Required | Result | Evidence |
|-------|----------|--------|----------|
| Alembic at `0031` | yes | **PASS** | probe 2026-08-10 |
| Attempts table exists | yes | **PASS** | probe 2026-08-10 |
| No orphan `processing` review runs (system) | yes | **PASS** | [generation lifecycle probe](./REVIEW_GENERATION_LIFECYCLE_STAGING_VALIDATION.md) |

---

## Pass criteria — P0 behavioral (post-#92 review run)

| Check | Required | Result | Evidence |
|-------|----------|--------|----------|
| `trigger_source` set on new run | yes | **pending** | trigger autostart/index job |
| `timing_stats.retrieve_ms` after checkpoint | yes | **pending** | PO-V3 partial |
| Timeout attempt row on induced HTTP timeout | yes | **pending** | PO-V3 — optional dogfood |
| `failure_class` on permanent fail path | yes | **pending** | worker `_mark_failed` |

**Next operator action:** trigger any staging PR review **after** `2026-08-10T14:23:32Z`, re-run `--po-p0-gate --since 2026-08-10T14:23:32Z`.

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| P0 schema (migration + table) | **PASS** | 2026-08-10 |
| P0 behavioral (checkpoint + attempts) | **pending** | — |
| P4 SLO (`--po-gate`) | **pending** | needs attempt rows |

**Blocked on:** ≥1 completed review run on staging after P0 deploy (#92).
