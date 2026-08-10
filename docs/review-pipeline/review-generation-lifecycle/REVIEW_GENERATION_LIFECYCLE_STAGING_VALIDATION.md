# Review generation lifecycle — staging validation

**Program:** [README.md](./README.md) · **Dogfood:** [POST_MAIN_STAGING_VALIDATION.md](../staging-validation/POST_MAIN_STAGING_VALIDATION.md) ([#93](https://github.com/raimondskrauklis/revy/pull/93))

**Status:** **full-cycle health PASS** on dogfood PR #93 · **RG-15 supersede overlap pending**.

**Metrics script:** `backend/scripts/generation_lifecycle_staging_metrics.py`

---

## Deploy boundary

| Deploy | `--since` ISO |
|--------|---------------|
| #89 restart hotfix | `2026-08-10T11:18:54Z` |
| Dogfood window (#92+) | `2026-08-10T14:23:32Z` |

---

## Dogfood evidence — PR #93 (2026-08-10)

| Check | Result | Evidence |
|-------|--------|----------|
| Full pipeline cycle | **PASS** | 2 completed review runs + 2 index jobs |
| Publish `head_sha` parity | **PASS** | both publishes match revision HEAD |
| Stuck `processing` | **PASS** | 0 orphan rows |
| Supersede during run | **pending** | 2 sequential revisions; `superseded_jobs=0` |

**`--rg15-gate --require-activity`:** **PASS** (supersede_path INCONCLUSIVE).

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| RG-15 system health (dogfood PR) | **PASS** | 2026-08-10 |
| RG-15 supersede overlap dogfood | **pending** | push during `in_progress` |
