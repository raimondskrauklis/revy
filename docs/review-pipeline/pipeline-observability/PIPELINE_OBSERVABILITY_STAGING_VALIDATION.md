# Pipeline observability — staging validation

**Program:** [README.md](./README.md) · **Dogfood:** [POST_MAIN_STAGING_VALIDATION.md](../staging-validation/POST_MAIN_STAGING_VALIDATION.md) ([#93](https://github.com/raimondskrauklis/revy/pull/93))

**Status:** **P0 behavioral PASS** on dogfood PR #93 (post-#92 deploy).

**Metrics script:** `backend/scripts/pipeline_observability_staging_metrics.py`

---

## Deploy boundary

| Deploy | `--since` ISO |
|--------|---------------|
| **#92 P0** | `2026-08-10T14:23:32Z` |

Use with **`--pr-number <dogfood PR>`** — not system-wide idle window.

---

## Dogfood evidence — PR #93 (2026-08-10)

| Check | Result | Evidence |
|-------|--------|----------|
| Alembic `0031` | **PASS** | staging DB |
| `trigger_source` on new runs | **PASS** | 2/2 completed runs |
| `timing_stats.retrieve_ms` checkpoint | **PASS** | 2/2 |
| `failure_stage` set | **PASS** | 2/2 |
| Attempt rows | **PASS** | 2 review-step rows |
| `--po-p0-gate --require-runs` | **PASS** | push 2 probe |

**Review runs:** `019fec1a…` (rev 1, `9f01500`) · `019fec1f…` (rev 2, `1a440e5`)

---

## Sign-off

| Party | Verdict | Date |
|-------|---------|------|
| P0 schema | **PASS** | 2026-08-10 |
| P0 behavioral (dogfood PR) | **PASS** | 2026-08-10 |
| P4 SLO | **pending** | P1 instruments `wait_ms` on success path |
