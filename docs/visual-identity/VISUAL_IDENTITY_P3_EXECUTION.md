# docs/visual-identity/VISUAL_IDENTITY_P3_EXECUTION.md

# P3 — Operator home (execution)

Phase **P3** of [`VISUAL_IDENTITY_GENERAL_PLAN.md`](./VISUAL_IDENTITY_GENERAL_PLAN.md). Baseline: [`VISUAL_IDENTITY_FINDINGS.md`](./VISUAL_IDENTITY_FINDINGS.md) VI-Q9. **P3 only.**

**Authority:** findings VI-Q0–Q10.

**Goal:** After sign-in, the member is in the reviewer, not a greeting dashboard.

## Decisions locked for P3

- Default authenticated dest = `/reviewer` in all six files below. **Not** admin `/admin/dashboard`, impersonation-stop, danger-zone, or `BlockAdminWhileImpersonating`.
- Kill `WelcomeWidget` greeting on dashboard.
- `ReviewerSummaryWidget` is status + next action; **no fake queue counts**; render when unavailable as connect (do not `return null`).
- `ReviewerNavItem` **always visible** (empty/connect), not gated on `useReviewerAvailability`.
- Dashboard remains a nav item: status + connect + next action. Do not delete `/dashboard`.
- No inbox API. No client fan-out across repos.

**Dest files (all `/reviewer`):**

| File | Change |
|------|--------|
| `LandingPage.tsx` | logged-in `replace('/reviewer')` |
| `LoginPage.tsx` | default `from` = `/reviewer` |
| `AuthCallbackPage.tsx` | default `navigate('/reviewer')` |
| `CompleteProfilePage.tsx` | already-complete `Navigate` + success dest (pending_approval still `/pending-approval`) |
| `NotFoundPage.tsx` | home `Link to="/reviewer"` |
| `UnauthorizedPage.tsx` | `navigate` + home `Link` → `/reviewer` |

## Out of scope for P3 (later phases)

- Finding-row scan, one-repo hop, QuietSelect on reviewer home → **P4**
- Admin / impersonation / danger-zone `/dashboard` fallbacks
- Workspace PR/findings list endpoint

---

## P3.1 — Six dest retargets

**What:** Change the six dest files (and their tests) from `/dashboard` to `/reviewer`. `LandingPage.test.tsx` must include an **authenticated** case that `replace('/reviewer')` (today the file only covers logged-out). Leave `ImpersonationBanner`, `DangerZonePage`, `AdminLayout`, `BlockAdminWhileImpersonating` alone.

**Files:** `frontend/src/features/marketing/pages/LandingPage.tsx`, `frontend/src/features/marketing/pages/LandingPage.test.tsx`, `frontend/src/features/auth/pages/LoginPage.tsx`, `frontend/src/features/auth/pages/LoginPage.test.tsx`, `frontend/src/features/auth/pages/AuthCallbackPage.tsx`, `frontend/src/features/auth/pages/AuthCallbackPage.test.tsx`, `frontend/src/features/auth/pages/CompleteProfilePage.tsx`, `frontend/src/features/auth/pages/CompleteProfilePage.test.tsx`, `frontend/src/components/errors/NotFoundPage.tsx`, `frontend/src/components/errors/NotFoundPage.test.tsx`, `frontend/src/features/auth/pages/UnauthorizedPage.tsx`, `frontend/src/features/auth/pages/UnauthorizedPage.test.tsx`

**Deliverable:** authenticated landing `replace('/reviewer')`; login default `login('/reviewer')`; callback/complete-profile/unauthorized/404 tests land on `/reviewer` (complete-profile pending_approval unchanged).

```bash
cd frontend && npm test -- LandingPage LoginPage AuthCallbackPage CompleteProfilePage UnauthorizedPage NotFoundPage
```

---

## P3.2 — Kill greeting; dashboard = status + connect

**What:** Remove `WelcomeWidget` from `DashboardPage` (delete the widget + its test if nothing else imports it). Restyle `ReviewerSummaryWidget` as status + connect/open; show when reviewer is unavailable (CTA to `/installations` or `/reviewer`, **no invented counts**). Keep checklist / connect / plan widgets as next action.

**Files:** `frontend/src/features/dashboard/pages/DashboardPage.tsx`, `frontend/src/features/dashboard/pages/DashboardPage.test.tsx`, `frontend/src/features/dashboard/widgets/WelcomeWidget.tsx`, `frontend/src/features/dashboard/widgets/WelcomeWidget.test.tsx`, `frontend/src/features/reviewer/ReviewerSummaryWidget.tsx`, `frontend/src/features/reviewer/ReviewerSummaryWidget.test.tsx` (new), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `DashboardPage` source does not import `WelcomeWidget`; widget still has no numeric queue; tests cover unavailable → connect.

```bash
cd frontend && npm test -- DashboardPage ReviewerSummaryWidget
```

---

## P3.3 — Reviewer nav always visible

**What:** `ReviewerNavItem` always renders the `/reviewer` link (loading/unavailable = same link, not `null`). Empty reviewer home already has no-workspace / empty copy (P4 densifies).

**Files:** `frontend/src/features/reviewer/ReviewerNavItem.tsx`, `frontend/src/features/reviewer/ReviewerNavItem.test.tsx` (new)

**Deliverable:** when `useReviewerAvailability` is false, nav link to `/reviewer` is in the document.

```bash
cd frontend && npm test -- ReviewerNavItem
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- LandingPage LoginPage AuthCallbackPage CompleteProfilePage UnauthorizedPage NotFoundPage DashboardPage ReviewerSummaryWidget ReviewerNavItem
```

**Human gate:** none.

**Deploy:** dest switch ships with P2 chrome. Reviewer tables still pre-P4 scan.

**Next:** [`VISUAL_IDENTITY_P4_EXECUTION.md`](./VISUAL_IDENTITY_P4_EXECUTION.md)
