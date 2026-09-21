# docs/visual-identity/console-ux-upgrade/CONSOLE_UX_UPGRADE_P3_EXECUTION.md

# P3 — Polish, empty states & bottom nav (execution)

Phase **P3** of [`UIUX_CONSOLE_GENERAL_PLAN.md`](./UIUX_CONSOLE_GENERAL_PLAN.md). Baseline: [`UIUX_CONSOLE_FINDINGS.md`](./UIUX_CONSOLE_FINDINGS.md) M3–m4 + [`MOBILE_AND_LAYOUT_FINDINGS.md`](./MOBILE_AND_LAYOUT_FINDINGS.md) M6–M7. **P3 only. Frontend only. Final phase — includes doc-sync.**

**Goal:** Fix visual inconsistencies, add mobile bottom nav, enrich empty states, clean settings stubs.

## Decisions locked for P3
- `DevNoticeWidget` button: `bg-[color:var(--app-primary)]` → `bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)]`. Single-line fix.
- `MobileBottomNav`: 4 tabs (Dashboard, Reviewer, Installations, Settings), `md:hidden`, fixed at bottom, 56px height, 44px touch targets, active route highlight via `useLocation`.
- Empty states: `PullRequestListPage` + `ReviewerHomePage` — both get a refresh button + "How PRs appear here" help text + link to installations. i18n keys shared.
- Settings audit: Security page → "Coming soon — security settings will be available in a future update" with feedback link. Billing → "Coming soon — billing management will be available in a future update." Review → keep existing UI but mark model selectors as "Coming soon" if disabled. Appearance already disabled per VI-Q2 — keep.
- Contrast audit: run axe-core or Lighthouse on key screens, document any AA failures in findings parking. No remap — `--rv-*` hex are calibrated.
- Terminology tooltips: `title` attributes on Judge/Publish/Review badges with short definitions from i18n keys (`reviewer.glossary.judge`, etc.).

## Out of scope for P3 (final phase)
- Onboarding redesign, danger zone changes, marketing pages
- Email templates, GitHub check-run HTML
- Backend changes

---

## P3.1 — DevNoticeWidget button token fix

**What:** Replace `bg-[color:var(--app-primary)] text-[color:var(--app-on-accent)]` with `bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)]` on the "Leave feedback" button in `DevNoticeWidget.tsx:19`. Match all other CTA buttons in the app.

**Files:** `frontend/src/features/dashboard/widgets/DevNoticeWidget.tsx`

**Deliverable:**
```bash
cd frontend && npm run build  # verify no className errors
```

---

## P3.2 — Mobile bottom tab bar

**What:** New `MobileBottomNav` component: `md:hidden`, `fixed bottom-0 left-0 right-0`, `h-14`, `bg-[color:var(--app-surface)]`, `border-t border-[color:var(--app-ring)]`. 4 tabs in a row: Dashboard (`LayoutDashboard` icon), Reviewer (`GitPullRequest`), Installations (`Plug`), Settings (`Settings`). Each tab: `flex flex-col items-center justify-center`, 44×44px min touch area, `text-xs` label. Active route: highlighted icon color + bold label, `bg-[color:var(--app-chip-active)]` pill behind active icon. Renders in `AppShellLayout` below main content area (inside the `<main>` flex column, after `<Outlet />`). Uses `useLocation` for active detection.

**Files:** `frontend/src/components/layout/MobileBottomNav.tsx` (new), `frontend/src/components/layout/MobileBottomNav.test.tsx` (new), `frontend/src/components/layout/AppShellLayout.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- MobileBottomNav AppShellLayout
```

---

## P3.3 — Empty state enrichment (PR list + repo list)

**What:** `PullRequestListPage` empty state: replace plain text with a structured empty panel: "No pull requests ingested yet" heading, "PRs appear here after a review is triggered from the repository" help text, "Refresh" button (refetches via query client `invalidateQueries`), "Manage installations" link to `/installations`. `ReviewerHomePage` empty state: same pattern — "No repositories connected" heading, help text, refresh button, installations link. Shared i18n keys for help text.

**Files:** `frontend/src/features/reviewer/pages/PullRequestListPage.tsx`, `frontend/src/features/reviewer/pages/PullRequestListPage.test.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.test.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- PullRequestListPage ReviewerHomePage
```

---

## P3.4 — Settings stub cleanup

**What:** Audit `SecuritySettingsPage`, `BillingSettingsPage`, `ReviewSettingsPage`. Security: if no real functionality, replace page content with "Coming soon — security settings will be available in a future update." + feedback link. Billing: same pattern. Review: keep existing model selector UI but disable with "Coming soon" label if models aren't configured. Appearance: already shows disabled state per VI-Q2 — verify it still says "console only." Do NOT remove routes or nav items — just honest content.

**Files:** `frontend/src/features/settings/pages/SecuritySettingsPage.tsx`, `frontend/src/features/settings/pages/BillingSettingsPage.tsx`, `frontend/src/features/settings/pages/ReviewSettingsPage.tsx`, `frontend/src/features/settings/pages/AppearanceSettingsPage.tsx` (verify only), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- SecuritySettingsPage BillingSettingsPage ReviewSettingsPage AppearanceSettingsPage
```

---

## P3.5 — Terminology tooltips + `/reviewer` flash fix

**What:** Add `title` attributes to `JudgeSkippedBadge`, `MergeReadinessBadge`, and pipeline status text in `PullRequestDetailPage` with short glossary definitions from i18n (`reviewer.glossary.judge`: "The Judge evaluates findings and decides merge readiness", etc.). Fix `/reviewer` logged-out flash: in router or `ProtectedRoute`, redirect to `/` before render if not authenticated — no brief `/reviewer` mount.

**Files:** `frontend/src/features/reviewer/components/JudgeSkippedBadge.tsx`, `frontend/src/features/reviewer/components/MergeReadinessBadge.tsx`, `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx`, `frontend/src/lib/routerInstance.tsx` (or ProtectedRoute wrapper), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- JudgeSkippedBadge MergeReadinessBadge PullRequestDetailPage
```

---

## P3.5v — Visual verification (non-gate)

**What:** Manual visual checks before doc-sync marks everything shipped. Run contrast audit on at least 3 key screens (PR detail page, settings page, dashboard) — use axe-core or Lighthouse Accessibility audit. Document results: any AA failures, their tokens (e.g. `--app-text-muted` on `--app-surface`), and whether they're pre-existing or new. Verify `/reviewer` logged-out flash is fixed: navigate to `/reviewer` while logged out — must redirect to `/` without flashing the reviewer UI. Verify mobile sidebar: open sheet at 375px viewport, confirm nav is scrollable, close via backdrop/Escape/route change.

**Files:** none (manual verification only — document findings in comments if pre-existing issues found)

**Deliverable:** contrast audit results documented in `console-ux-upgrade/` as a short note. `/reviewer` flash confirmed fixed.

```bash
# Run Lighthouse accessibility audit on PR detail page (replace URL)
npx lighthouse https://localhost:5173/reviewer/repositories/.../pull-requests/... --only-categories=accessibility --output=json
```

---

## P3.6 — Doc-sync + changelog

**What:** Final phase closeout. Doc changes:

| Doc | Change |
|-----|--------|
| `docs/visual-identity/console-ux-upgrade/README.md` | Phase statuses Done + shas |
| `docs/visual-identity/README.md` | Update next program status to shipped |
| `docs/visual-identity/console-ux-upgrade/UIUX_CONSOLE_FINDINGS.md` | Status → shipped |
| `docs/visual-identity/console-ux-upgrade/MOBILE_AND_LAYOUT_FINDINGS.md` | Status → shipped |
| `frontend/src/data/changelog.json` | New entry: "**Console UX + mobile/layout** — merge verdict, findings search/filter/detail, responsive sidebar, mobile support." |

**Files:** docs listed above, `frontend/src/data/changelog.json`

**Deliverable:**
```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- MobileBottomNav AppShellLayout PullRequestListPage ReviewerHomePage SecuritySettingsPage BillingSettingsPage ReviewSettingsPage AppearanceSettingsPage JudgeSkippedBadge MergeReadinessBadge PullRequestDetailPage
```

**Phase gate** (from repo root):

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

**Deploy:** frontend-only.

**Next:** none — final phase.
