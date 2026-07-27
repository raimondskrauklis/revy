# GitHub surface P1 — L2 triage comment (execution)

Phase **P1** of [POST_REVIEW_QUALITY_GENERAL_PLAN.md](./POST_REVIEW_QUALITY_GENERAL_PLAN.md). Baseline: [POST_REVIEW_QUALITY_FINDINGS.md](./POST_REVIEW_QUALITY_FINDINGS.md) §4 L2, general plan dogfood rubric. **P1 only.**

**Goal:** Issue comment matches Greptile **triage** class — confidence, files needing attention, G9 prose, findings table; check body stays compact (G3).

**Authority:** `backend/app/services/github_publish_formatter.py` · [GITHUB_SURFACE_EXECUTION.md](./GITHUB_SURFACE_EXECUTION.md)

## Decisions locked for P1

- **L2 pass** = `build_pr_review_comment_fallback` shape is sufficient (PQ-2 v1 bar).
- Moonshot path (`build_pr_review_comment` async) may enhance narrative — failure must fall back (H2).
- `check_summary` ≠ `issue_comment` (G3) — both required.
- No mermaid, merge-verdict automation, or recall/prompt changes.

## Out of scope for P1 (later phases)

- G10 in_progress / ack → **P2**
- Inline warning breadth → **P3**
- PRODUCT_PATTERNS full sweep → **P4**
- Track B empty-findings investigation → dogfood note only

---

## P1.1 — Fallback Greptile-shape regression test

**What:** Add `test_build_pr_review_comment_fallback_greptile_shape` (or extend `test_build_pr_review_comment_fallback_includes_g9_and_metadata`) with **mixed severities** + G9 prose; assert markdown contains `## Revy code review`, confidence line, `### Files needing attention`, `### Findings`, and table header row.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py::test_build_pr_review_comment_fallback_greptile_shape -q
```

---

## P1.2 — G3 split bodies test

**What:** Keep / extend `test_build_publish_format_result_splits_bodies`: `check_summary != issue_comment`; check body has no `<details>` metadata block.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py::test_build_publish_format_result_splits_bodies -q
```

---

## P1.3 — Moonshot failure → fallback

**What:** Add `test_build_pr_review_comment_moonshot_failure_returns_fallback`: patch `reviewer_llm_enabled` false and Moonshot raise → async `build_pr_review_comment` returns same markdown as deterministic fallback (non-empty).

**Files:** `backend/tests/unit/test_github_publish_formatter.py`, `backend/app/services/github_publish_formatter.py` (fix only if gap)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py::test_build_pr_review_comment_moonshot_failure_returns_fallback -q
```

**P1 is not complete until P1.3 test exists and passes.**

---

## P1.4 — Dogfood-driven formatter fixes

**What:** If P0 dogfood row L2 = N: fix only proven gaps (missing sections, JSON leak, check/comment swapped). If L2 = Y: skip code — append dogfood note “L2 pass, P1 tests only”.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_publish.py` (as needed)

**Deliverable:** L2 = Y on next PR push row in [GITHUB_SURFACE_DOGFOOD.md](./GITHUB_SURFACE_DOGFOOD.md).

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish_formatter.py::test_build_pr_review_comment_fallback_greptile_shape \
  tests/unit/test_github_publish_formatter.py::test_build_publish_format_result_splits_bodies \
  tests/unit/test_github_publish_formatter.py::test_build_pr_review_comment_moonshot_failure_returns_fallback \
  tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -q
```

**Human gate:** Dogfood L2 = Y on a real PR push (non-gate for commit if tests pass; required before P2).

**Next:** [GITHUB_SURFACE_P2_EXECUTION.md](./GITHUB_SURFACE_P2_EXECUTION.md)
