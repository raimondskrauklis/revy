# Polish P0 — Schema and enums (execution)

Phase **P0** of [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](../REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_POLISH_FINDINGS.md](../REVIEW_PIPELINE_POLISH_FINDINGS.md) § Track A data, § Track B persisted fields, Q# P1–P7, J1–J5. **P0 only.**

**Goal:** Persist `suggestion` on findings and judge escalation status on review runs.

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) R6-Q3.

## Decisions locked for P0

- Migration revision **`0025`** — hand-written only; `down_revision` = `2026_07_26_2300_0024_workspace_memberships_updated_at`.
- `github_findings.suggestion` — `TEXT NULL`; no backfill.
- `github_review_runs.judge_escalation_candidate_count` — `INTEGER NOT NULL DEFAULT 0`.
- `github_review_runs.judge_status` — `VARCHAR(32) NOT NULL DEFAULT 'not_applicable'`.
- Enum `GitHubReviewJudgeStatus`: `not_applicable` · `completed` · `skipped_disabled` · `skipped_unavailable` (`snake_case` values).
- `GitHubReviewRunResponse` exposes `judge_status` + `judge_escalation_candidate_count`; `GitHubFindingResponse` exposes optional `suggestion` on raw `GET …/findings` only (P4 — **not** on `ReconciledFindingResponse`).

## Out of scope for P0 (later phases)

- LLM prompt / parse / publish suggestion → **P1**
- Setting `judge_status` at reconcile → **P2**
- Reconciled-finding schema → out of wave
- Frontend → **P2**

---

## P0.1 — Judge status enum

**What:** Add `GitHubReviewJudgeStatus` to `app/constants/enums.py` with four values above.

**Files:** `backend/app/constants/enums.py`

**Deliverable:** enum importable; existing tests still pass.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -q
```

---

## P0.2 — Migration `0025`

**What:** Hand-written Alembic revision `0025`: add `github_findings.suggestion`; add `github_review_runs.judge_escalation_candidate_count` and `judge_status` with server defaults.

**Files:** `backend/alembic/versions/2026_07_27_0000_0025_findings_suggestion_review_judge_status.py`

**Deliverable:** `alembic upgrade head` applies on empty DB chain.

```bash
cd backend && pipenv run alembic upgrade head
```

**LOOP pause:** hand-written Alembic revision — stop after commit before P1.

---

## P0.3 — ORM and API schemas

**What:** Map new columns on `GitHubFindingORM`, `GitHubReviewRunORM`; extend `GitHubReviewRunResponse` and `GitHubFindingResponse` with matching fields. On `GitHubReviewRunORM`, set Python `default=` **and** migration `server_default=` for `judge_status` (`not_applicable`) and `judge_escalation_candidate_count` (`0`) — same pattern as `status` on that model (unit tests construct ORM without DB).

**Files:** `backend/app/models/github_finding.py`, `backend/app/models/github_review_run.py`, `backend/app/schemas/github_review.py`

**Deliverable:** response models validate ORM rows with defaults. Route-level `GET …/review-run` judge-field assertions → **P2.2**.

```bash
cd backend && pipenv run pytest tests/unit/test_github_review_routes.py -q
```

---

## P0.4 — Model defaults unit test

**What:** Add tests asserting new review run defaults (`judge_status=not_applicable`, `judge_escalation_candidate_count=0`) and finding `suggestion=None`.

**Files:** `backend/tests/unit/test_github_review.py` (or new `test_review_polish_schema.py`)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run alembic upgrade head && pipenv run pytest \
  tests/unit/test_github_finding_judge.py \
  tests/unit/test_github_review.py \
  tests/unit/test_github_review_routes.py -q
```

**Deploy:** `alembic upgrade head` (`0025`) before P1/P2 code that writes new columns.

**Next:** [REVIEW_PIPELINE_POLISH_P1_EXECUTION.md](./REVIEW_PIPELINE_POLISH_P1_EXECUTION.md)
