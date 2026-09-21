# docs/free-plan-credits/FREE_PLAN_CREDITS_P2_EXECUTION.md

# P2 — Frontend counter display + trigger gate (execution)

Phase **P2** of [`FREE_PLAN_CREDITS_GENERAL_PLAN.md`](./FREE_PLAN_CREDITS_GENERAL_PLAN.md). Baseline: [`FREE_PLAN_CREDITS_FINDINGS.md`](./FREE_PLAN_CREDITS_FINDINGS.md) §Track 2. **P2 only.**

**Goal:** Show `{completed}/{limit}` credit counter in dashboard; disable "Run Review" buttons at limit; i18n keys for usage and limit-reached messages.

## Decisions locked for P2
- Credit fields exposed via `/me` endpoint (not billing — billing is admin-gated)
- `MeResponse` gets `completed_review_runs: int = 0`, `review_run_limit: int | None = None`
- `MeUser` (frontend) gets matching fields
- `PlanSummaryWidget` swaps static text for dynamic `{completed}/{limit}`
- `ReviewTriggerBar` disables when `completed >= limit` (free only — pro has null limit, never blocks)
- Keep `plan_upgrade_required` error handling in `InstallationsPage` (dead code, harmless)
- i18n: EN + LV for `dashboard.planSummary.usage`, `dashboard.planSummary.limitReached`, `reviewer.reviewRun.creditLimitReached`, `errors.credit_limit_reached`

## PR review context (SSOT stays from P0 commit, scope widens to frontend)

**SSOT:** `.revy/review-context.json` — same program, `scope` adds `frontend/`. **Bugbot:** `.cursor/BUGBOT.md` stays. **Agent mirror:** `.agent/review-context.json` stays.

## Out of scope for P2 (deferred)
- Warning banners before limit ("you have 2 remaining")
- Admin credit override UI
- Per-user credits
- BillingSettingsPage changes (billing remains admin-gated, no credit display there)

---

## P2.0 — Update PR review context (scope widen to frontend)

**What:** Update `.revy/review-context.json` — `scope` adds `frontend/` to existing backend scope from P1. No new Bugbot context needed (stays from P0). Mirror to `.agent/review-context.json`.

**Files:** `.revy/review-context.json`, `.agent/review-context.json`

**Deliverable:** `pipenv run pytest tests/unit/test_engineering_context_manifest.py`

---

## P2.1 — README status

**What:** Update README.md — set P1 row to `Done (<sha>)`.

**Files:** `docs/free-plan-credits/README.md`

**Deliverable:** README P1 row reflects shipped commit.

---

## P2.2 — Backend: extend `/me` endpoint with credit fields

**What:** In `_build_current_me()`, after fetching `WorkspaceORM` and setting `workspace_plan`, add `completed_review_runs` and `review_run_limit` to the `model_copy(update={...})` block. Both come from the already-fetched workspace object — no new query.

**Files:**
- `backend/app/api/v1/me.py` — `_build_current_me()` function (line 71-77 `model_copy` block)
- `backend/app/schemas/me.py` — `MeResponse` model (add `completed_review_runs: int` and `review_run_limit: int | None`)

**Deliverable:** `pipenv run pytest tests/unit/test_me_credit_fields.py` — `/me` returns `completed_review_runs` (0 for new workspace) and `review_run_limit` (25 for free, None for pro).

---

## P2.3 — Frontend: extend MeUser type

**What:** Add `completed_review_runs: number` and `review_run_limit: number | null` to `MeUser` interface.

**Files:** `frontend/src/lib/me.ts` — `MeUser` interface (line 30-43)

**Deliverable:** TypeScript compiles; `npm run build` succeeds.

---

## P2.4 — Frontend: PlanSummaryWidget dynamic counter

**What:** Replace static `t('dashboard.planSummary.free')` with dynamic counter using credit fields from `useAuth().user`. Show `{completed}/{limit}` when free, "Unlimited" when pro (null limit). Add i18n keys `dashboard.planSummary.usage` and `dashboard.planSummary.limitReached`.

**Files:**
- `frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx`
- `frontend/src/i18n/locales/en.json` — add `dashboard.planSummary.usage`, `dashboard.planSummary.limitReached`
- `frontend/src/i18n/locales/lv.json` — add same keys in Latvian

**Deliverable:** `npm test -- PlanSummaryWidget`

---

## P2.5 — Frontend: ReviewTriggerBar credit gate

**What:** Disable "Run Deep Review" and "Run Critical Review" buttons when `completed >= limit` (free plan). Add tooltip: "Credit limit reached — upgrade to Pro." Derive from `useAuth().user` (same source as widget). Add i18n key `reviewer.reviewRun.creditLimitReached`.

**Files:**
- `frontend/src/features/reviewer/components/ReviewTriggerBar.tsx`
- `frontend/src/i18n/locales/en.json` — add `reviewer.reviewRun.creditLimitReached`
- `frontend/src/i18n/locales/lv.json` — add same

**Deliverable:** `npm test -- ReviewTriggerBar`

---

## P2.6 — Frontend: error toast i18n for `credit_limit_reached`

**What:** Add `errors.credit_limit_reached` key to EN + LV locale files. The `ForbiddenError(error_code="credit_limit_reached")` from backend will map to this toast via `showDomainErrorToast(mapApiError(error))`.

**Files:**
- `frontend/src/i18n/locales/en.json` — `errors.credit_limit_reached`
- `frontend/src/i18n/locales/lv.json` — same

**Deliverable:** `npm test -- InstallationsPage` — confirms `SETUP_ERROR_KEYS` still includes `plan_upgrade_required` (untouched), no regressions.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_me_credit_fields.py
```

**Phase gate** (from `frontend/`):

```bash
npm run build && npm test -- PlanSummaryWidget ReviewTriggerBar InstallationsPage
```

**Deploy:** Ship with P0+P1 in one PR (full stack). Frontend reads from me endpoint — no coupling to billing/Stripe.

**Next:** none — final phase. Run `post-finish-gap-pass` + doc-sync.

## P2.7 — Doc sync (final phase)

**What:** Update all affected docs; finalize README status.

**Files:** `docs/free-plan-credits/README.md` — all rows Done

| Doc | Change |
|:---|:---|
| `docs/free-plan-credits/README.md` | P0, P1, P2 → Done with shas |
| `docs/free-plan-credits/FREE_PLAN_CREDITS_FINDINGS.md` | No change (baseline doc) |
| `docs/free-plan-credits/FREE_PLAN_CREDITS_GENERAL_PLAN.md` | No change (baseline doc) |

**Deliverable:** README reflects all phases shipped.

**Human gate:** Verify credit counter on staging dashboard; trigger review at limit → confirm blocked; upgrade workspace to pro → confirm unlimited.