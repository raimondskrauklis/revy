# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P2_EXECUTION.md

# P2 — This-push metrics (execution)

Phase **P2** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q3, RH-Q5. **P2 only.**

**Goal:** “Closed as fixed” and the rate use last published **group ids**. Empty denominator is **N/A**, never **0%**.

## Decisions locked for P2

- Prior set = groups last seen on the last **published** revision (`get_last_published_prior_revision`), keyed by `group.id` (RH-Q11). After P0, file+category supersede is gone so that path no longer empties the cohort.
- Historical `state=superseded` rows stay out of the cohort (RH-Q2). Do not un-supersede #1.
- When `denominator_active_prior == 0`: `resolution_rate_pct` is `null`; manifest includes `resolution_rate_display: "N/A"`.
- `format_resolution_metrics_block` renders **N/A (no prior cohort)** when denom is 0 or rate is null — including the **display_still_open_prior override** path (`github_publish_formatter.py` today still does `rate = … if denominator else 0.0`). Never `0.0% (0/0 prior active)`.
- Inline map keys are `group.id` from P0.4. `_fingerprints_from_publish_summary` already treats them as group ids; P2 does not reintroduce fingerprint matching.
- First publish on a PR is N/A (no prior review). A second publish after a real prior review must have denom > 0 when prior groups still exist.
- `resolution_pass` remains the reconcile pipeline artifact (comment already reads it). Do not add a second persist path.

## Out of scope for P2 (later phases)

- Lifetime raised/resolved table → **P3**
- GH-Q9 / Option A copy → **P4**
- Dogfood PR → **P5**

---

## P2.1 — Manifest prior set + N/A

**What:** `build_resolution_pass_manifest` keeps group-id identity. `resolution_rate_pct` is `None` when `denominator == 0` (today it is `0.0`). Add `resolution_rate_display` `"N/A"` vs a numeric string.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:** empty denom → rate `None` + display N/A; nonempty denom still a float.

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -k "build_resolution_pass_manifest" -q
```

---

## P2.2 — Formatter N/A

**What:** `format_resolution_metrics_block` uses `resolution_rate_display` / null rate. Line is `**Resolution rate:** N/A (no prior cohort)` when denom is 0. Same N/A on `test_format_resolution_metrics_block_display_still_open_override` when the override drives denom to 0. Nonzero denom keeps `rate% (transition_count/denominator prior active)`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:** `test_format_resolution_metrics_block` empty-denom fixture and `test_format_resolution_metrics_block_display_still_open_override` (when denom hits 0) do not contain `0.0%` or `0/0`.

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "format_resolution_metrics_block" -q
```

---

## P2.3 — Fix-some prior cohort

**What:** Test a prior published set of N group ids, this run H2-closes K of them: `transitions_addressed >= K`, `denominator_active_prior == N` (minus compare-blocked). After P0, retitled leftovers still in the prior set (not superseded). Name the test `test_build_resolution_pass_manifest_fix_some_prior_cohort`.

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -k "build_resolution_pass_manifest or format_resolution_metrics_block" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_publish_formatter.py -q
pipenv run ruff check app/services/github_resolution_metrics.py app/services/github_publish_formatter.py
```

**Deploy:** no migration.

**Next:** [`RESOLUTION_HONESTY_P3_EXECUTION.md`](./RESOLUTION_HONESTY_P3_EXECUTION.md)
