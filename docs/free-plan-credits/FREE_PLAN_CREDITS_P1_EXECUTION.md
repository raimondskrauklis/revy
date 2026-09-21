# docs/free-plan-credits/FREE_PLAN_CREDITS_P1_EXECUTION.md

# P1 — Credit check + increment (execution)

Phase **P1** of [`FREE_PLAN_CREDITS_GENERAL_PLAN.md`](./FREE_PLAN_CREDITS_GENERAL_PLAN.md). Baseline: [`FREE_PLAN_CREDITS_FINDINGS.md`](./FREE_PLAN_CREDITS_FINDINGS.md) §1.4–1.8. **P1 only.**

**Goal:** Soft-gate review triggers at 25 completed runs for free plan; atomically increment counter on completion; handle credit errors in autostart pipeline; wire Stripe webhook credit mutations.

## Decisions locked for P1
- Credit check: in `create_review_run()`, after `ensure_revision_access()`, before existing LLM/index/in-progress checks
- Credit gate: `workspace.review_run_limit is not None AND workspace.completed_review_runs >= workspace.review_run_limit` → `ForbiddenError(error_code="credit_limit_reached")`
- Credit increment: atomic `UPDATE workspaces SET completed_review_runs = completed_review_runs + 1 WHERE id = ? AND review_run_limit IS NOT NULL AND completed_review_runs < review_run_limit`
- Increment hook: after `update(GitHubReviewRunORM).values(status='completed')` succeeds in `run_review_run()` (line ~1278)
- Autostart: `prepare_review_after_index()` catches `ForbiddenError` → `fail_pipeline_check=True, pipeline_check_summary="credit_limit_reached"`
- Stripe downgrade: `apply_subscription_event()` for `customer.subscription.deleted` sets `review_run_limit = 25` after `_update_workspace_plan()` returns
- Stripe upgrade: `apply_subscription_event()` for `checkout.session.completed` sets `review_run_limit = NULL` after `_update_workspace_plan()` returns
- New workspace defaults already handled in P0

## PR review context (SSOT stays from P0 commit)

**SSOT:** `.revy/review-context.json` — same as P0 but `scope` narrows to backend files touched in P1. **Bugbot:** `.cursor/BUGBOT.md` stays as P0 set. **Agent mirror:** `.agent/review-context.json` stays.

## Out of scope for P1 (later phases)
- Me endpoint credit fields → **P2**
- Frontend counter display → **P2**
- Frontend trigger bar disable → **P2**
- i18n keys → **P2**

---

## P1.0 — Update PR review context (scope narrow to backend)

**What:** Narrow `.revy/review-context.json` `scope` to backend files touched in P1. No new Bugbot context needed (stays from P0). Mirror to `.agent/review-context.json`.

**Files:** `.revy/review-context.json`, `.agent/review-context.json`

**Deliverable:** `pipenv run pytest tests/unit/test_engineering_context_manifest.py`

---

## P1.1 — README status

**What:** Update README.md — set P0 row to `Done (<sha>)`.

**Files:** `docs/free-plan-credits/README.md`

**Deliverable:** README P0 row reflects shipped commit.

---

## P1.2 — Credit check in `create_review_run()`

**What:** Fetch `WorkspaceORM` after `ensure_revision_access()`; if `review_run_limit is not None` and `completed_review_runs >= review_run_limit`, raise `ForbiddenError` with `error_code="credit_limit_reached"` and `details={"completed_runs", "run_limit"}`.

**Files:** `backend/app/services/github_review.py` — `create_review_run()` function (after line 635, before line 639)

**Deliverable:** `pipenv run pytest tests/unit/test_credit_check_create_review.py`

---

## P1.3 — Atomic credit increment on completion

**What:** In `run_review_run()`, after the `update(GitHubReviewRunORM).values(status='completed')` block succeeds, execute atomic increment on `WorkspaceORM`. Only increments for free-plan workspaces (`review_run_limit IS NOT NULL`). Guarded by `completed_review_runs < review_run_limit` to prevent exceeding cap.

**Files:** `backend/app/services/github_review.py` — `run_review_run()` function (after line 1287, after `completed.rowcount` check succeeds)

**Deliverable:** `pipenv run pytest tests/unit/test_credit_increment.py` — verifies: free workspace increments, pro workspace skipped, failed run skipped, superseded run skipped, race guard holds, counter at 25 stops further increments.

---

## P1.4 — Catch `ForbiddenError` in autostart pipeline

**What:** In `prepare_review_after_index()`, add `from app.core.exceptions import ForbiddenError` to imports; add `except ForbiddenError as exc:` block before the existing `except ConflictError`. On `credit_limit_reached`, return `ReviewAfterIndexOutcome(fail_pipeline_check=True, pipeline_check_summary="credit_limit_reached")`.

**Files:** `backend/app/services/review_pipeline.py` — lines 20 (import), 285 (new except block)

**Deliverable:** `pipenv run pytest tests/unit/test_autostart_credit_blocked.py` — autostart pipeline returns `fail_pipeline_check=True` when credit limit reached.

---

## P1.5 — Stripe webhook credit mutations

**What:** In `apply_subscription_event()`:
- `checkout.session.completed` block (line ~283): after `_update_workspace_plan()` returns, set `workspace.review_run_limit = None` (upgrade to Pro = unlimited)
- `customer.subscription.deleted` block (line ~292): after `_update_workspace_plan()` returns, set `workspace.review_run_limit = 25` (downgrade to free = capped)

**Files:** `backend/app/services/billing.py` — `apply_subscription_event()` function

**Deliverable:** `pipenv run pytest tests/unit/test_stripe_credit_mutations.py` — upgrade sets limit to NULL, downgrade sets limit to 25.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_credit_check_create_review.py tests/unit/test_credit_increment.py tests/unit/test_autostart_credit_blocked.py tests/unit/test_stripe_credit_mutations.py
```

**Deploy:** Dependent on P0 (needs columns). Ship with P0 if not already shipped; can ship standalone after P0.

**Next:** [`FREE_PLAN_CREDITS_P2_EXECUTION.md`](./FREE_PLAN_CREDITS_P2_EXECUTION.md)