# Free Plan Credits — Findings

**Status:** baseline-ready · **Date:** 2026-09-21 · **DB:** revy-staging (verified 2026-09-21)

## Production DB snapshot (verified 2026-09-21 08:55 UTC+3)

| Workspace | Plan | Completed Runs | Failed Runs | Installations |
|-----------|------|----------------|-------------|---------------|
| `raimonds-krauklis-3d0151ab` | pro | 939 | 101 | `raimondskrauklis` |
| `gaz-66-67927c40` | pro | 3 | 0 | `rtudatadev-dotcom` |
| `data-dev-df8f59b6` | NULL (= free) | 0 | 0 | none |
| `data-dev-25b56474` | NULL (= free) | 0 | 0 | none |

**Key observations:**
- 101 of 1046 total runs (9.7%) are `failed` — confirms model crashes, truncated responses happen regularly. These must NOT consume credits.
- 2 active free-plan workspaces with zero runs — safe to apply the 25-run cap retroactively.
- 2 pro workspaces — would bypass the cap (NULL limit = unlimited).
- Latest migration: `2026_09_19_2200_0035_finding_group_claim_slot`.
- No `completed_review_runs` or `review_run_limit` columns exist yet.

## Build principles

- **Real data only** — count actual completed review runs; no fuzzy estimates, no projected credits.  
- **No misleading** — if a run fails (model crash, truncated response), it does NOT consume credit.  
- **Production-grade** — schema designed for future Pro bypass, reset cycles, and admin overrides; not a throwaway.  
- **Reuse, don't fork** — reuse existing `github_review_runs` data and `ForbiddenError` patterns.

## Terminology

| Term | Meaning |
|------|---------|
| **Credit** | One successful review run (`status = 'completed'`) |
| **Credit limit** | Max credits before soft-gating; free plan = 25 |
| **Soft gate** | Review trigger rejected → `error_code: "credit_limit_reached"`; user sees it, can wait for reset or upgrade |
| **Credit counter** | Column on `workspaces` tracking total lifetime completed runs |

## What exists vs genuinely new

### Present (verified)

| Item | Location | Notes |
|------|----------|-------|
| Plan field | `workspaces.plan` (varchar, nullable) | `"free"` | `"pro"`; defaults `"free"` via `effective_plan()` — `backend/app/services/billing.py:30-33` |
| Plan gate system | `backend/app/core/plan_gates.py` | Only gate: `installations.create → pro`. `require_plan_feature()` + `workspace_has_feature()` |
| Review run statuses | `backend/app/constants/enums.py:184-191` | `pending`, `processing`, `completed`, `failed`, `superseded` |
| Review trigger | `POST .../revisions/{id}/review` → `create_review_run()` | `backend/app/api/v1/workspaces/installation_review.py:55-131` |
| Autostart pipeline | `backend/app/services/review_pipeline.py` | `prepare_review_after_index()` calls `create_review_run()` — verified line 277 |
| Frontend dashboard | `PlanSummaryWidget.tsx` | Already says "Free tier — up to 25 review runs" — **i18n is already written** (`en.json:79`, `lv.json:79`) |
| Model switching disabled | `ReviewSettingsPage.tsx:188,201` | `disabled` hardcoded — nothing to change |
| Me endpoint | `backend/app/api/v1/me.py:69-76` | Returns `workspace_plan` — frontend reads it via `useExtensions()` hook (`platform/extensions/hooks.ts:19`) |
| Billing status API | `backend/app/api/v1/workspaces/billing.py` | Returns `plan` + `stripe_enabled` |
| Review run counter | **None** | No credit tracking anywhere — SaaS docs explicitly rejected it for v1 (`docs/saas-base/SAAS_BASE_W4_STRIPE_GENERAL_PLAN.md:17`) |
| Per-IP rate limiter | `backend/app/core/rate_limit.py` | `120 req/60s` API-wide — not per-workspace, not credit-aware |

### Genuinely new

1. **Credit counter on `workspaces`** — `completed_review_runs` (INT, default 0)  
2. **Credit limit on `workspaces`** — `review_run_limit` (INT, nullable; NULL = unlimited, 25 = free)  
3. **Credit check in `create_review_run()`** — before creating a run, check `completed_review_runs < review_run_limit` for free plan  
4. **Credit increment** — when a review run transitions to `completed`, atomically increment the counter  
5. **Frontend display** — show `{used}/{limit}` credit usage in PlanSummaryWidget  
6. **Frontend gate** — disable "Run Review" buttons when at limit; show error explanation  
7. **i18n** — new keys for limit-reached messaging (dashboard, reviewer page)

## Catalog

### Track 1: Schema & backend logic

#### 1.1 DB migration

Add two columns to `workspaces`:

```sql
ALTER TABLE workspaces
  ADD COLUMN completed_review_runs INTEGER NOT NULL DEFAULT 0,
  ADD COLUMN review_run_limit INTEGER NULL;
```

- `review_run_limit` NULL → unlimited (Pro); 25 → free cap.  
- `completed_review_runs` starts at 0; incremented atomically on each completed run.  
- `completed_review_runs` never decremented (no refunds — if user retries, it's a new run).

**Migration file:** `backend/alembic/versions/2026_09_21_0900_0036_workspace_credit_limits.py`

#### 1.2 Plan model update

Update `backend/app/models/workspaces.py`:

```python
completed_review_runs: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
review_run_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
```

#### 1.3 Set default limit for existing workspaces

Data migration in Alembic `upgrade()`:

```sql
-- Free/NULL plan: 25-run cap
UPDATE workspaces SET review_run_limit = 25 WHERE plan IS NULL OR plan = 'free';

-- Pro plan: unlimited
UPDATE workspaces SET review_run_limit = NULL WHERE plan = 'pro';
```

**Verified against staging:** 2 NULL-plan workspaces with 0 runs, 2 pro workspaces. No existing credit counters needed — `completed_review_runs = 0` is the column default. Safe retroactive application.

Also set `review_run_limit = NULL` for pro workspaces — they already exist with 939+ completed runs, must be unlimited.

#### 1.4 Credit check at review creation

In `backend/app/services/github_review.py:create_review_run()`, **before** the existing checks (LLM config, index status, in-progress check), add:

```python
workspace = await session.get(WorkspaceORM, workspace_id)
if workspace and workspace.review_run_limit is not None:
    if workspace.completed_review_runs >= workspace.review_run_limit:
        raise ForbiddenError(
            message="Credit limit reached. Upgrade to Pro for unlimited reviews.",
            error_code="credit_limit_reached",
            details={
                "completed_runs": workspace.completed_review_runs,
                "run_limit": workspace.review_run_limit,
            },
        )
```

**Note:** The workspace is already loaded in `create_review_run` indirectly via `ensure_revision_access()` — but we need it explicitly for the credit check. The existing `ensure_revision_access` already validates workspace access; add workspace fetch right after it.

#### 1.5 Credit increment on completion

In `backend/app/services/github_review.py:run_review_run()`, after the `update(GitHubReviewRunORM).values(status=GitHubReviewRunStatus.completed)` succeeds (line ~1278), atomically increment:

```python
from app.models.workspaces import WorkspaceORM

await session.execute(
    update(WorkspaceORM)
    .where(
        WorkspaceORM.id == run.workspace_id,
        WorkspaceORM.review_run_limit.isnot(None),
        WorkspaceORM.completed_review_runs < WorkspaceORM.review_run_limit,
    )
    .values(completed_review_runs=WorkspaceORM.completed_review_runs + 1)
)
```

- Only increments if `review_run_limit` is set (free plan) — Pro workspaces (NULL limit) are skipped.  
- `completed_review_runs < WorkspaceORM.review_run_limit` guards against races — won't exceed limit even under concurrency.  
- Failed runs (`status = 'failed'` or `'superseded'`) never trigger increment — only `completed`.

#### 1.6 Autostart pipeline should propagate credit errors

In `backend/app/services/review_pipeline.py:prepare_review_after_index()`, the `create_review_run()` call (line 277) may now raise `ForbiddenError` with `credit_limit_reached`. Currently this is caught by the generic `ConflictError` handler (line 286) — update to also catch `ForbiddenError` and return `ReviewAfterIndexOutcome(fail_pipeline_check=True, pipeline_check_summary="credit_limit_reached")`.

#### 1.7 Future-proof: new workspace defaults + Stripe downgrade

In `backend/app/services/onboarding.py` (where workspaces are created after registration), set `review_run_limit = 25` for new workspaces.

In `backend/app/services/billing.py:apply_subscription_event()`, when `customer.subscription.deleted` fires and `_update_workspace_plan()` sets plan to `"free"`, also set `review_run_limit = 25`. Do this **after** `_update_workspace_plan()` returns (not inside it — that function is shared with upgrade path).

#### 1.8 Stripe webhook: upgrade path

In `backend/app/services/billing.py:apply_subscription_event()`, when checkout completes or subscription updates and `_plan_from_subscription()` returns `"pro"`, set `review_run_limit = NULL`. This is the upgrade path — existing free credits become irrelevant. No need to reset `completed_review_runs`.

### Track 2: Frontend

#### 2.1 PlanSummaryWidget — show credit usage

Current: shows only "Free tier — up to 25 review runs" (static).

Change to show `{completed}/{limit}`:

```
{completed}/{limit} reviews used
```

Extend the `/me` endpoint (not billing — billing is admin-gated) to return `completed_review_runs` and `review_run_limit`. The `MeUser` type already carries `workspace_plan`; add credit fields alongside it. Every user can see their own workspace credits.

**Why not billing endpoint:** `/workspaces/{id}/billing` requires `canManageBilling` (`admin:users`). Regular workspace members (viewers, contributors) wouldn't see their own credit counter on the dashboard widget. The `me` endpoint is self-scoped — no additional authorization needed.

Schema addition in `MeUser` (backend + frontend):
```python
completed_review_runs: int = 0
review_run_limit: int | None = None  # None = unlimited
```

#### 2.2 ReviewTriggerBar — disable at limit

Current: button is disabled only when `reviewInFlight || triggerMutation.isPending`.

Add: also disable when credits exhausted. Can be derived from `PlanSummaryWidget` data (same billing endpoint) or from the API error on trigger attempt.

Recommended: **pre-check via `me` endpoint credit data** — if at limit, show button as disabled with tooltip "Credit limit reached — upgrade to Pro." The `PlanSummaryWidget` and `ReviewTriggerBar` share the same data source (user context from `me`).

#### 2.3 InstallationsPage — remove plan gate UI

Current: shows `plan_upgrade_required` error from OAuth callback. After removing the backend gate, this error should never appear for install. However, keep the error handling (future Pro-only features might reuse it). The i18n text already exists — just leave it.

#### 2.4 i18n keys needed

| Key | EN | LV |
|-----|----|----|
| `dashboard.planSummary.usage` | `{completed}/{limit} reviews used` | `{completed}/{limit} pārskati izmantoti` |
| `dashboard.planSummary.limitReached` | `Credit limit reached. Upgrade to Pro for unlimited reviews.` | `Kredītu limits sasniegts. Jauniniet uz Pro neierobežotiem pārskatiem.` |
| `reviewer.reviewRun.creditLimitReached` | `Credit limit reached — upgrade to Pro to run more reviews.` | `Kredītu limits sasniegts — jauniniet uz Pro, lai veiktu vairāk pārskatu.` |
| `errors.credit_limit_reached` | `Credit limit reached. Upgrade to Pro for unlimited reviews.` | `Kredītu limits sasniegts. Jauniniet uz Pro neierobežotiem pārskatiem.` |

### Track 3: Remove installation gate

#### 3.1 Drop `installations.create` from `PLAN_FEATURES`

`backend/app/core/plan_gates.py:21` — remove the entry:

```python
PLAN_FEATURES: dict[str, str] = {}  # Empty; pro-only features added later
```

#### 3.2 Remove `require_plan_feature` from three installation endpoints

`backend/app/api/v1/workspaces/installations.py`:
- Line 64: `POST /{workspace_id}/installations` — remove `_: Annotated[None, Depends(require_plan_feature("installations.create"))] = None,`
- Line 91: `POST /{workspace_id}/installations/connect` — remove same
- Line 122: `POST /{workspace_id}/installations/{installation_id}/verify` — remove same

#### 3.3 Remove `workspace_has_feature` from OAuth callback

`backend/app/services/github_installations.py:142-148` — remove the entire guard block in `bind_github_installation()`. This is the callback path for the GitHub OAuth flow — duplicate of the endpoint guard.

**Total: 5 locations** — `PLAN_FEATURES` dict + 3 endpoint guards + 1 service-layer guard.

## Data scope & exclusions

### What we count
- Only review runs where `status = 'completed'` — the run produced findings (even if 0 findings, it consumed LLM compute).  
- Counted only when the atomic `UPDATE` succeeds in `run_review_run()`.

### What we DON'T count
- `failed` runs — model crash, truncated response, timeout, parse error. User sees these, they don't consume credit.  
- `superseded` runs — newer revision arrived before this one completed.  
- Runs that never started (`pending` → time out).  

### What we DON'T build (defer)
- **Credit resets** — monthly, weekly, or manual reset. Deferred until Pro launch or abuse patterns emerge.  
- **Admin credit overrides** — no UI for changing `review_run_limit` per workspace.  
- **Per-user credits** — credit is workspace-scoped, not per member.  
- **Credit purchase** — Stripe integration for buying additional runs. Pro plan (unlimited) is the upgrade path.  
- **Warning before limit** — no "you have 2 remaining" banners. Just the counter and the hard block at 25.  

## Edge cases

- **Race condition on completion increment:** Two simultaneous completions, counter at 24 → both pass pre-check (24 < 25). First one completes → `UPDATE WHERE completed_review_runs < review_run_limit` increments to 25. Second one also passes (25 < 25 → false, no rows updated). Second run's counter stays at 25. User gets exactly 25 credits. **Accepted:** fair soft cap, no reservation system needed.
- **Concurrent triggers:** Two users trigger at 23/25 → both pass the pre-check. Both runs are created. Race is on completion increment, not creation. Resolution is the same as above — `WHERE` clause handles it. Worst case: 26th run is in-flight but can't increment. OK.
- **Pro → Free downgrade:** Stripe webhook fires `customer.subscription.deleted` → plan becomes `"free"`, `review_run_limit` set to 25. If user has already exceeded 25 completed runs while on Pro, any new trigger immediately hits the cap. Intentional — downgrade consequences are immediate.
- **Free → Pro upgrade:** `_update_workspace_plan()` sets plan to `"pro"`, `review_run_limit = NULL`. Existing `completed_review_runs` counter is preserved (history) but no longer checked.
- **Autostart at limit:** Pipeline calls `create_review_run()` which raises `ForbiddenError(credit_limit_reached)` → catches as `fail_pipeline_check=True`. PR check shows "credit limit reached". User must upgrade to continue auto-review.
- **Zero-finding runs:** Still count. LLM was called, compute consumed. The run produced 0 findings but that doesn't mean it was "free" — embeddings, indexing, and LLM inference all ran.
- **Workspace deletion:** `CASCADE` handles removal. No orphan cleanup needed.
- **Failed runs don't count:** 101 of 1046 production runs (9.7%) are failed. These correctly don't trigger the increment — the `UPDATE` only fires after `status = completed` transition succeeds. Truncated responses, model crashes, timeouts are excluded.  

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Where to store credit counter? | **Resolved** | Column on `workspaces` — clean, single join, extensible |
| Q2 | What triggers credit consumption? | **Resolved** | `status = 'completed'` only — verified transition in `run_review_run()` |
| Q3 | How to expose to frontend? | **Resolved** | Extend `me` endpoint (not billing — billing is admin-gated). Every user sees own workspace credits. |
| Q4 | Autostart vs manual trigger gating? | **Resolved** | Same `create_review_run()` check covers both |
| Q5 | Backfill existing workspaces? | **Resolved** | Data migration: set `review_run_limit = 25` for all free, NULL for pro |
| Q6 | Pro downgrade → credit re-enable? | **Resolved** | Reset `review_run_limit = 25`; if already over, immediate block |
| Q7 | Should credit limit block the install flow? | **Resolved** | No — only blocks review trigger. Installation is always allowed |

## References

- Plan gate system: `backend/app/core/plan_gates.py:1-58`  
- Billing service: `backend/app/services/billing.py:30-33`, `200-230`, `257-290`  
- Review run creation: `backend/app/services/github_review.py:606-690`  
- Review completion: `backend/app/services/github_review.py:1035-1335` (specifically 1278-1287)  
- Autostart pipeline: `backend/app/services/review_pipeline.py:210-316`  
- Installation API: `backend/app/api/v1/workspaces/installations.py:64,91,122`  
- Installation service: `backend/app/services/github_installations.py:142-148`  
- Workspace model: `backend/app/models/workspaces.py:12-28`  
- Frontend dashboard: `frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx:1-24`  
- Frontend review trigger: `frontend/src/features/reviewer/components/ReviewTriggerBar.tsx:1-97`  
- Billing settings page: `frontend/src/features/settings/pages/BillingSettingsPage.tsx:1-57`  
- Me endpoint: `backend/app/api/v1/me.py:69-76`  
- i18n (existing): `frontend/src/i18n/locales/en.json:77-80`, `lv.json:77-80`