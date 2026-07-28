# Finding resolution P0 — Closure model & schema (execution)

Phase **P0** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). Baseline: [FINDING_RESOLUTION_FINDINGS.md](../FINDING_RESOLUTION_FINDINGS.md). **P0 only.**

**Goal:** Shared closure contract — `ResolutionMethod`, group closure columns, compare helper, pure closure rules — without changing runtime closure behavior yet.

## Decisions locked for P0

- Migration `2026_07_28_1200_0028_finding_resolution_closure.py` — hand-written only.
- `github_finding_groups`: `resolution_method` VARCHAR nullable; `resolved_at_revision_id` UUID FK nullable; `closure_blocked_reason` TEXT nullable.
- `github_finding_judge_outcomes`: `judge_purpose` VARCHAR NOT NULL, server default `discovery`; values from **`JudgePurpose` enum** (`discovery`, `verification`) — no string constants.
- `ResolutionMethod` enum: `absent_and_addressed`, `judge_dismissed`, `verification_dismissed`, `human_dismissed`.
- `fetch_compare_patches(session, pull_request, base_sha, head_sha)` in `github_compare_patches.py`; refactor existing callers to use it without behavior change in P0.
- `github_finding_closure.py` — pure functions: `should_close_absent_and_addressed`, `apply_resolution_method_on_judge_dismiss`, etc. — no worker wiring in P0.
- Fix R5-Q1 doc drift: fingerprint uses **title** not message in `REVIEW_PIPELINE_FINDINGS.md`.

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — `docs/review-pipeline/finding-resolution/**`, `scope: ["backend/**"]`
- **Bugbot:** `.cursor/BUGBOT.md` — links to finding-resolution findings + execution index

## Out of scope for P0

- Pass 1/2 closure wiring → **P1**
- Verification judge → **P2**
- Metrics display → **P3**

---

## P0.1 — Program PR review context

**What:** Add Greptile + Bugbot entries for `finding-resolution/` program docs.

**Files:** `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
python -m json.tool .greptile/files.json > /dev/null
```

---

## P0.2 — Migration `0028` + enums

**What:** Add `ResolutionMethod` and `JudgePurpose` enums in `enums.py`; ORM columns; Alembic `0028`.

**Files:** `backend/app/constants/enums.py`, `backend/app/models/github_finding_group.py`, `backend/app/models/github_finding_judge_outcome.py`, `backend/alembic/versions/2026_07_28_1200_0028_finding_resolution_closure.py`, `backend/tests/unit/test_review_quality_models.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/constants/enums.py app/models/github_finding_group.py app/models/github_finding_judge_outcome.py alembic/versions/2026_07_28_1200_0028_finding_resolution_closure.py
cd backend && pipenv run pytest tests/unit/test_review_quality_models.py -q
```

**LOOP pause:** apply `0028` on staging before P1 deploy.

---

## P0.3 — Shared compare helper

**What:** `fetch_compare_patches(session, pull_request, base_sha, head_sha) -> dict[str, str]`; refactor `github_resolution_metrics._fetch_compare_patches` and `fetch_compare_patches_by_file` internals to call shared helper (same behavior for existing paths).

**Files:** `backend/app/services/github_compare_patches.py`, `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -q
```

---

## P0.4 — Closure rules module

**What:** `backend/app/services/github_finding_closure.py` — pure functions for FR-Q2/FR-Q3/FR-Q13 decision table; unit tests with fixtures (no DB).

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q
```

---

## P0.5 — Doc sync R5-Q1 fingerprint

**What:** Update `REVIEW_PIPELINE_FINDINGS.md` R5-Q1 row to D10 title-based fingerprint (align with `compute_fingerprint`).

**Files:** `docs/review-pipeline/REVIEW_PIPELINE_FINDINGS.md`

**Deliverable:** R5-Q1 resolution text matches `github_finding_reconcile.py`.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_resolution_metrics.py tests/unit/test_review_quality_models.py -q
pipenv run ruff check app/services/github_compare_patches.py app/services/github_finding_closure.py app/models/github_finding_group.py
```

**Next:** [FINDING_RESOLUTION_P1_EXECUTION.md](./FINDING_RESOLUTION_P1_EXECUTION.md)
