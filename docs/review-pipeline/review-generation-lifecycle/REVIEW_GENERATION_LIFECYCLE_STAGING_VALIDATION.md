# Review generation lifecycle — staging validation

**Program:** [README.md](./README.md) · **Dogfood:** [POST_MAIN_STAGING_VALIDATION.md](../staging-validation/POST_MAIN_STAGING_VALIDATION.md)

**Status:** **RG-15 DB supersede PASS** (PR #93 probes, corrected script). **Queued check UX** pending [#94](https://github.com/raimondskrauklis/revy/pull/94) deploy + push 4.

**Metrics script:** `backend/scripts/generation_lifecycle_staging_metrics.py` (ships in #94)

---

## Deploy boundary

| Deploy | `--since` ISO |
|--------|---------------|
| #89 restart hotfix | `2026-08-10T11:18:54Z` |
| Dogfood window (#92+) | `2026-08-10T14:23:32Z` |
| #94 check UX | _after merge_ |

---

## Dogfood evidence — PR #93 (2026-08-10)

| Check | Result | Evidence |
|-------|--------|----------|
| Full pipeline cycle | **PASS** | 3 completed review runs + index jobs |
| Supersede path (DB) | **PASS** | `superseded_review_runs=2`, `superseded_index_jobs=1` |
| Stuck `processing` | **PASS** | 0 orphans at probe time |
| GitHub queued check UX | **pending** | requires #94 on staging + push 4 |

**`--rg15-gate --require-activity`:** **PASS** (2026-08-10, script from #94 branch).

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| RG-15 supersede (DB evidence) | **PASS** | 2026-08-10 |
| RG-15 queued check UX (GitHub) | **pending** | after #94 deploy |
