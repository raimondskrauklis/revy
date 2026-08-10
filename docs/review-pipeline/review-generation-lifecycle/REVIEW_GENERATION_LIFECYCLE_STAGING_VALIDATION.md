# Review generation lifecycle — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) (RG-15)

**Status:** **system health PASS** · **RG-15 supersede dogfood pending**.

**Metrics script:** `backend/scripts/generation_lifecycle_staging_metrics.py` — [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

---

## Deploy boundary

| Boundary | `--since` ISO | Deploy job |
|----------|---------------|------------|
| Restart hotfix #89 | `2026-08-10T11:18:54Z` | [Actions #31382638736](https://github.com/raimondskrauklis/revy/actions/runs/31382638736) |

```bash
cd backend

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.generation_lifecycle_staging_metrics --since 2026-08-10T11:18:54Z --rg15-gate --json'
```

---

## System probe — 2026-08-10 (operator)

**Database:** `revy-staging` · **window:** post-#89 deploy

| Metric | Value |
|--------|-------|
| Review runs | 6 completed, 0 failed, 0 `processing` |
| Index jobs | 6 completed, 0 `superseded`, 0 `processing` |
| Synchronize events | *(not queried — no `github_events` table on staging)* |

### RG-15 gate (`--rg15-gate`)

| Check | Status | Evidence |
|-------|--------|----------|
| Pipeline activity | **PASS** | `runs=6 index_jobs=6` |
| Supersede path exercised | **INCONCLUSIVE** | `superseded_jobs=0` — need push-during-run dogfood |
| No stuck `processing` rows | **PASS** | `processing_runs=0 processing_jobs=0` |

**`--rg15-gate`:** **PASS** (no `FAIL`; supersede `INCONCLUSIVE`).

---

## Pass criteria — RG-15 behavioral (dogfood)

| Check | Required | Result | Evidence |
|-------|----------|--------|----------|
| Push during Revy run → new run enqueued without worker restart | yes | **pending** | [P2 § P2.7](./REVIEW_GENERATION_LIFECYCLE_P2_EXECUTION.md#p27--post-ship-restart-hotfix-pr-89) |
| `@revy review` while pipeline active → supersede + restart | yes | **pending** | operator dogfood |
| `superseded` index job row after rapid push | yes | **pending** | DB: `index_jobs.superseded_jobs > 0` |
| Resolution before pipeline enqueue (G9) | yes | **pending** | reconcile manifest / worker logs |

**Note:** System-wide probe confirms **no regressions** (no orphan processing). Supersede **behavior** requires intentional dogfood — not inferred from idle staging traffic.

---

## Related system probes (same deploy window)

| Script | Purpose |
|--------|---------|
| `judge_json_contract_staging_metrics.py` | Judge + RCX health |
| `pipeline_observability_staging_metrics.py` | P0 schema post-#92 |

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| RG-15 system health (no stuck processing) | **PASS** | 2026-08-10 |
| RG-15 supersede / restart dogfood | **pending** | — |

**Next operator action:** push during active Revy run on any staging PR; re-run `--rg15-gate` and confirm `superseded_jobs > 0` or new review run without worker restart.
