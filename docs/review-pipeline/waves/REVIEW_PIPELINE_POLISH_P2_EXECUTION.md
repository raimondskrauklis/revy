# Polish P2 — Judge skipped badge (execution)

Phase **P2** of [REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md](../REVIEW_PIPELINE_POLISH_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_POLISH_FINDINGS.md](../REVIEW_PIPELINE_POLISH_FINDINGS.md) § Track B, Q# J1–J5. **Depends on P0.** **P2 only — final polish phase.**

**Goal:** Persist judge escalation status per review run and show a **Judge skipped** badge on `/reviewer` PR detail when appropriate.

**Authority:** [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md).

## Decisions locked for P2

- Set `judge_escalation_candidate_count` and `judge_status` via **`record_review_run_judge_status(session, review_run_id)`** — count candidates **before** any early-return; run judge when enabled; persist on review run — never at API read time.
- **Refactor required:** today `run_judge_for_review_run` returns before loading candidates when disabled — replace with flow inside `record_review_run_judge_status` (callable from `reconcile_tasks` and future `judge_tasks`).
- Candidate count = findings on run where `is_judge_candidate` true and group not `resolved` (same set judge would consider).
- Status rules (findings § Track B + J5): `not_applicable` when count=0; `skipped_disabled` when count>0 and `!settings.judge_llm_enabled()`; `skipped_unavailable` when count>0, judge enabled, `resolve_model(judge)` fails before any LLM call; `completed` when judge path entered (including all per-call LLM failures — **no badge**).
- UI shows badge only when `reviewRun.status === 'completed'` and `judge_status ∈ {skipped_disabled, skipped_unavailable}`.
- Badge copy: `reviewer.judge.skipped` (disabled) and `reviewer.judge.skippedUnavailable` (unavailable) — EN + LV.
- Chip styling: warning/muted `--app-*` tokens; mirror `MergeReadinessBadge` pattern.

## Out of scope for P2

- Judge all LLM calls fail but model resolved → `completed`, no badge (J5) → parking lot for distinct status
- Settings page judge credential hint → parking lot
- Re-trigger judge action → R9+
- Suggestion UI in findings table → parking lot
- Publish–UI parity test → separate PR

---

## P2.1 — Persist judge status on review run

**What:** Add `record_review_run_judge_status(session, review_run_id)` — load candidates; set `judge_escalation_candidate_count` early; set `skipped_*` before return; set `completed` **after** the LLM loop (not before first call); invoke judge when not skipped. Refactor or wrap `run_judge_for_review_run` so disabled/unavailable paths still persist counts. In `reconcile_review_run_task`, replace `run_judge_for_review_run` with `record_review_run_judge_status` after `reconcile_review_run` and before commit. Update `test_reconcile_tasks.py` to patch `record_review_run_judge_status` (not `run_judge_for_review_run`).

**Files:** `backend/app/services/github_finding_judge.py`, `backend/app/workers/reconcile_tasks.py`, `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:** tests for `skipped_disabled`, `skipped_unavailable`, `not_applicable`, `completed` (including all-call-fail → completed, no badge).

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_reconcile_tasks.py -q
```

---

## P2.2 — API parity test

**What:** Assert `GET …/review-run` returns `judge_status` and `judge_escalation_candidate_count` on completed runs (mock/fixture).

**Files:** `backend/tests/unit/test_github_review_routes.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review_routes.py -q
```

---

## P2.3 — Frontend types and badge component

**What:** Add `GitHubReviewJudgeStatus` union on `ReviewRun` in `types.ts`; add `JudgeSkippedBadge.tsx` (`judgeStatus` prop → `skipped` vs `skippedUnavailable` copy) + test; render on `PullRequestDetailPage` header when `reviewRun.status === 'completed'` and `judge_status ∈ {skipped_disabled, skipped_unavailable}`.

**Files:** `frontend/src/features/reviewer/types.ts`, `frontend/src/features/reviewer/components/JudgeSkippedBadge.tsx`, `frontend/src/features/reviewer/components/JudgeSkippedBadge.test.tsx`, `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx`

**Deliverable:**

```bash
cd frontend && npm test -- src/features/reviewer/components/JudgeSkippedBadge.test.tsx
```

---

## P2.4 — i18n EN + LV

**What:** Add `reviewer.judge.skipped` and `reviewer.judge.skippedUnavailable` to `en.json` and `lv.json` with matching keys.

**Files:** `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**

```bash
cd frontend && npm test -- src/features/reviewer/
```

---

## P2.5 — Doc sync

**What:** Update program docs to reflect shipped polish wave.

| Doc | Change |
|-----|--------|
| [waves/README.md](./README.md) | Polish P0–P2 rows → Done + sha |
| [REVIEW_PIPELINE_POLISH_FINDINGS.md](../REVIEW_PIPELINE_POLISH_FINDINGS.md) | Status → shipped; lock P5=2000 |
| [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) | Suggested fix → **shipped**; judge visibility → **shipped** |
| [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md) | R6-Q3 note: suggestion blocks shipped |
| [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) | Judge skipped UI row → **shipped** |
| [README.md](../README.md) | Optional one-line under Next if polish merged before R9 |

**Deliverable:** grep confirms no stale **defer** on R6-Q3 suggestion row in product patterns.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_finding_judge.py \
  tests/unit/test_reconcile_tasks.py \
  tests/unit/test_github_review_routes.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- src/features/reviewer/ && npm run build
```

**Deploy:** requires P0 migration `0025`; no worker queue changes.

**Tag on `main` (optional):** `review-polish-v1`

**Next:** [review-quality program](../review-quality/README.md) — merged PR #50; RQ9 hardening active.
