# docs/review-pipeline/waves/REVIEW_PIPELINE_R5_EXECUTION.md

# R5 — Reconciliation + judge (execution)

Phase **R5** of [REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md](../REVIEW_PIPELINE_R5_RECONCILE_JUDGE_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R4 (`review-r4-v1`).

**Goal:** Stable finding identity across revisions; reconcile per-run findings into a workspace-scoped set; run Anthropic judge on configured escalations.

**Authority:** `internal-docs/product/revy/docs/architecture.md` §14, [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md) § Stability.

## Decisions locked for R5

Locked in findings as **R5-Q1–Q3** (execution peer-review 2026-07-26):

| Q# | Resolution |
|----|------------|
| **R5-Q1** | `fingerprint = sha256(workspace_id ‖ pull_request_id ‖ file_path ‖ category ‖ normalize(message)[:500])` — scoped **per PR**, not repo-wide |
| **R5-Q2** | Table `github_finding_groups` (`pull_request_id` FK, fingerprint unique per PR); per-run `github_findings.group_id` FK; group state `active` \| `superseded` \| `resolved` |
| **R5-Q3** | Judge when `severity ∈ {error, critical}` OR (`category = security` AND `severity ≥ warning`); max **10** judge calls per review run |

- **Queues:** `reconcile_tasks` on `reconciliation`; `judge_tasks` on `judge` (routes exist in `celery_app.py`).
- **Trigger:** enqueue reconcile after R4 review run `completed`; judge runs on reconcile output when R5-Q3 matches.
- **Primary model:** Moonshot findings from R4 unchanged; judge uses Anthropic when `ANTHROPIC_API_KEY` set.
- **Judge skip:** when `ANTHROPIC_API_KEY` unset — reconcile completes; judge outcomes omitted (not failed).
- **Judge outcome:** `upheld` \| `dismissed` \| `modified` on `github_finding_judge_outcomes`; links to `group_id` + `review_run_id`. `dismissed` → mark group `resolved` or downgrade per service logic (unit-tested).
- **API:** `GET …/pull-requests/{pr_id}/findings/reconciled` — cursor list for workspace members (`items_view`).
- **R4 hook:** R5.3 adds `reconcile_review_run.delay` from R4 worker on successful completion (not in R4 scope).
- **Out of scope:** GitHub publish (R6); human approval workflow; learning from dismiss feedback (R8+).

---

## R5.1 — Schema migration

**What:** Migration `0015_github_finding_groups`; `GitHubFindingGroupORM`, `GitHubFindingJudgeOutcomeORM`; enums `GitHubFindingGroupState`, `GitHubJudgeOutcome`; FK `github_findings.group_id`; `github_finding_groups.pull_request_id` FK.

**Files:** `alembic/versions/…_github_finding_groups.py`, models, `constants/enums.py`, `models/__init__.py`

**Deliverable:** migration applies; existing R4 finding rows backfill `group_id` in reconcile job (not in migration).

**LOOP pause:** hand-written Alembic revision.

---

## R5.2 — Fingerprint + reconcile service

**What:** `services/github_finding_reconcile.py` — compute fingerprint per R5-Q1; upsert group per PR; link run findings; mark superseded when same fingerprint on new revision with changed message/severity.

**Files:** `services/github_finding_reconcile.py`, `tests/unit/test_github_finding_reconcile.py`

**Deliverable:** unit tests cover new finding, same fingerprint new revision, resolved group unchanged.

---

## R5.3 — Reconcile worker

**What:** `workers/reconcile_tasks.py` — `reconcile_review_run(review_run_id)`; import in `celery_app.py`; enqueue from R4 `review_tasks` on successful completion.

**Files:** `workers/reconcile_tasks.py`, `workers/review_tasks.py` (hook), `tests/unit/test_reconcile_tasks.py`

**Deliverable:** worker tests green; idempotent re-run on same `review_run_id`.

---

## R5.4 — Judge worker + Anthropic escalation

**What:** `services/github_finding_judge.py` — select candidates per R5-Q3; call `anthropic_review.py`; persist outcomes.

**Files:** `services/github_finding_judge.py`, `workers/judge_tasks.py`, `tests/unit/test_github_finding_judge.py`, `tests/unit/test_judge_tasks.py`

**Deliverable:** judge skipped when `ANTHROPIC_API_KEY` unset; reconcile job still `completed`.

---

## R5.5 — Reconciled findings API

**What:** Member route for reconciled set; cursor list; includes latest severity, state, last seen revision.

**Files:** `api/v1/workspaces/installation_review.py` (extend), schemas, `tests/unit/test_github_reconciled_findings_routes.py`

**Deliverable:** phase gate green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_finding_reconcile.py \
  tests/unit/test_reconcile_tasks.py \
  tests/unit/test_github_finding_judge.py \
  tests/unit/test_judge_tasks.py \
  tests/unit/test_github_reconciled_findings_routes.py \
  -q
```

**Deploy:** `alembic upgrade head`; `ANTHROPIC_API_KEY` optional (judge path); worker `-Q` includes `reconciliation,judge`.

**Human gate:** complete R4 review run → reconcile groups stable across second run on new revision.

**Next:** [REVIEW_PIPELINE_R6_EXECUTION.md](./REVIEW_PIPELINE_R6_EXECUTION.md).
