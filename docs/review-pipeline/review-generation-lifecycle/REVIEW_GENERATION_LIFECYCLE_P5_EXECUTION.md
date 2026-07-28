# Review generation lifecycle P5 — Judge gate, trace, dogfood, doc sync (execution)

Phase **P5** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-5, RG-6, RG-13, RG-Q10, §3c. **P5 only — program closeout.**

**Goal:** Judge-candidates never publish without outcome; trace shows generation authority; staging dogfood; docs shipped.

## Decisions locked for P5

- **RG-Q10:** Filter at publish eligibility — judge **candidates** (`is_judge_candidate`) require `github_finding_judge_outcomes` row for `(group_id, review_run_id)` OR group `state == resolved` from judge dismiss; **non-candidates** unchanged.
- Apply filter to **inline publish statement** and replace PR-wide `groups` query in `run_publish_job` with **filtered active groups for this review run** (candidates gated; non-candidates unchanged — narrows §3c asymmetry for candidates only).
- Log `judge_candidate_unpublished_missing_outcome` with `group_id`, `review_run_id`.
- **RG-13:** After judge loop, if any candidate lacks outcome row → `judge_status = skipped_unavailable` (not `completed`).
- Trace manifest: `generation_superseded_at` (ISO on supersede), `publish_skipped_not_head` (bool) on publish step artifact.
- Dogfood: two pushes ~8 s apart on staging PR; metric = **open Revy inline thread count at HEAD** (not summary rows).
- PRODUCT_PATTERNS generation row → **shipped**.

## Out of scope for P5

- Frontend pipeline tab
- Block whole publish when judge incomplete
- Hard Celery cancel

---

## P5.1 — Judge publish eligibility filter

**What:** Add `publishable_groups_for_review_run` / `publishable_findings_for_review_run` excluding judge-candidates without outcome. In `run_publish_job` **build** phase, use filtered groups for formatter (check/issue comment) instead of all PR active groups (`github_publish.py` ~688–702 today).

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_finding_judge.py`, `backend/app/services/github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_finding_judge.py -k "judge_candidate or publish" -q
```

---

## P5.2 — Judge status honesty (RG-13)

**What:** In `record_review_run_judge_status` / `_run_judge_llm_loop`: track candidates without persisted outcome; if any missing at end → `run.judge_status = skipped_unavailable` instead of `completed`.

**Files:** `backend/app/services/github_finding_judge.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py -k "skipped_unavailable or missing_outcome" -q
```

---

## P5.3 — Pipeline trace fields

**What:** On supersede (hook from P2, backfill manifest here if missing): write `generation_superseded_at` to pipeline index-step manifest. On publish skip (P1 path): `publish_skipped_not_head: true` (or `publish_skipped_superseded`) on publish step artifact.

**Files:** `backend/app/services/github_pipeline_trace.py`, `backend/app/services/github_generation_lifecycle.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pipeline_trace.py -k "generation_superseded or publish_skipped" -q
```

---

## P5.4 — Dogfood log

**What:** Create `REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md` with template: PR link, two pushes ~8 s apart, open inline thread count at HEAD, Greptile comparison, coalesce on/off note, pass/fail vs findings §13.

**Files:** `docs/review-pipeline/review-generation-lifecycle/REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md`

**Deliverable:** file exists with checklist rows (Human gate: staging run — **non-gate** for commit).

---

## P5.5 — Doc sync

**What:** Update per table:

| Doc | Change |
|-----|--------|
| `review-generation-lifecycle/README.md` | Status Done + sha |
| `REVIEW_GENERATION_LIFECYCLE_EXECUTION.md` | All phases Done (sha) |
| `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` | Snapshot generation row → **shipped** |
| `REVIEW_PIPELINE_RECOVERY_CHECKLIST.md` | Add generation lifecycle track row if active |

**Files:** docs listed above

**Deliverable:**

```bash
grep -l "review-generation-lifecycle" docs/review-pipeline/README.md docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_publish.py tests/unit/test_github_finding_judge.py tests/unit/test_github_pipeline_trace.py tests/unit/test_github_generation_lifecycle.py -q
```

**Human gate:** Staging dogfood per `REVIEW_GENERATION_LIFECYCLE_DOGFOOD.md` — LOOP may stop after commit; deploy verification separate.

**Next:** none — program complete after P5.
