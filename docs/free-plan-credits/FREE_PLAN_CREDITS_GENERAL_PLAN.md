# Free Plan Credits — General Plan

**Based on:** `docs/free-plan-credits/FREE_PLAN_CREDITS_FINDINGS.md` (baseline-ready, all decisions locked)

## Cross-cutting

Every phase ships: **i18n (EN+LV)**, **backend unit tests (`tests/unit/`)**, **frontend unit tests (`*.test.tsx`)**. Lineage is transparent — credit consumption is a direct consequence of `status = completed`, traceable in `github_review_runs`.

---

## Phase 0: Schema + open the gate

**Goal:** Allow any workspace to install GitHub; add credit columns; backfill existing workspaces.

**Scope in:** `workspaces` migration (2 new columns), model update, backfill SQL, workspace creation default, remove `installations.create` plan gate from 5 locations:
1. `plan_gates.py` — drop `"installations.create": "pro"` from `PLAN_FEATURES`
2. `installations.py:64` — remove `require_plan_feature("installations.create")` from `post_workspace_installation`
3. `installations.py:91` — remove from `post_workspace_installation_connect`
4. `installations.py:122` — remove from `post_workspace_installation_verify`
5. `github_installations.py:142-148` — remove `workspace_has_feature` check from `bind_github_installation`  
**Scope out:** Credit check logic, credit increment, frontend.

**Deliverables:** Migration `0036_workspace_credit_limits` (DDL + backfill SQL), updated `WorkspaceORM`, `review_run_limit = 25` set on new workspace creation (`onboarding.py`), all 5 guard locations removed, `plan_upgrade_required` error code stays (harmless dead code, reusable for future gates).

**Depends on:** nothing.

---

## Phase 1: Credit check + increment

**Goal:** Soft-gate review triggers at 25 completed runs for free plan; atomically increment counter.

**Scope in:** Check in `create_review_run()`, atomic increment in `run_review_run()` after completion, `ForbiddenError` catch in autostart pipeline (`review_pipeline.py` — currently only catches `ConflictError` + `ServiceUnavailableError`), Stripe downgrade path in `apply_subscription_event()`.  
**Scope out:** Frontend, any reset/refund/UPSERT logic.

**Deliverables:** Single-point credit gate (manual + auto via `create_review_run`), atomic increment guarded by `WHERE completed_review_runs < review_run_limit`, autostart pipeline catches `ForbiddenError` → `fail_pipeline_check=True` with `pipeline_check_summary="credit_limit_reached"`, Stripe webhook `customer.subscription.deleted` sets `review_run_limit = 25` (in `apply_subscription_event`, not `_update_workspace_plan`), new workspace already gets default from P0.

**Depends on:** Phase 0.

---

## Phase 2: Frontend — counter display + trigger gate

**Goal:** Show `{used}/{limit}` in dashboard; disable review buttons at limit.

**Scope in:** Extend `me` endpoint schema to include `completed_review_runs` + `review_run_limit`, update `PlanSummaryWidget` to show counter, update `ReviewTriggerBar` to disable at limit with tooltip, new i18n keys.  
**Scope out:** Warning banners, admin credit override UI, per-user counters, billing endpoint changes.

**Deliverables:** Backend `/me` returns credit fields (no auth change — user is self), `MeUser` type updated, `PlanSummaryWidget` shows dynamic `{completed}/{limit}` instead of static text, `ReviewTriggerBar` disables at limit with tooltip, i18n keys for usage + limit-reached messages.

**Depends on:** Phase 1.

---

**Open item:** None — all decisions locked in findings.  
**Next step:** `create-execution-plan` from `docs/free-plan-credits/`.