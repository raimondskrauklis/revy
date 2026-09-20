# docs/visual-identity/MOBILE_AND_LAYOUT_FINDINGS.md

# Mobile & layout — findings

**Date:** 2026-09-20 (code-audited 2026-09-20)
**Status:** baseline — full pass planned; no execution yet
**Purpose:** Full mobile responsiveness, sidebar expand/collapse, settings navigation restructure, and content container sizing audit. **No execution steps.**
**Evidence:** code audit of `AppShellLayout.tsx`, `AppHeader.tsx`, `SettingsLayout.tsx`, `SettingsSidebar.tsx`, reviewer table pages, `DevNoticeWidget.tsx`, `DashboardPage.tsx`.

**Related:** `UIUX_CONSOLE_FINDINGS.md` (reviewer UX) — shared recommendations cross-referenced. M5 (tables) overlaps with console M1 (findings table) and M4 (Team table).

---

## M1 — No mobile sidebar / hamburger — code-audited

**Finding:** The sidebar is completely invisible below `md` breakpoint with no alternative navigation.

**Code evidence:**
- `AppShellLayout.tsx:44` — `<aside className="hidden md:flex w-56 shrink-0 flex-col …">` — `hidden md:flex` means the sidebar disappears entirely below 768px.
- `AppHeader.tsx:7–10` — `<header className="… md:hidden">` shows workspace switcher + user menu on mobile. **No hamburger/menu toggle button.** The mobile header has zero navigation access — only workspace switching and user menu.
- No `SidebarProvider`, `useSidebar`, `SidebarTrigger`, or collapse state exists anywhere in the codebase (grep confirmed zero matches).
- No sheet/drawer component for mobile overlay navigation.

**kp-platform pattern (for reference):** `WorkspaceLayout.tsx:201–207` has a `<Menu>` hamburger button with `onClick={toggleSidebar}` that opens a `<Sheet>` slide-over on mobile, backed by `SidebarProvider` + `useSidebar()` context.

**External reference:** [Dashboard Layout with Collapsible Sidebar](https://uipotion.com/potions/layouts/dashboard) — three-state pattern: desktop expanded (240–280px), desktop collapsed (64–80px icon rail), mobile hidden/off-canvas overlay. [Sidebar Navigation](https://uipotion.com/potions/components/sidebar-navigation) — mobile overlay with backdrop, focus trap, route-close, body scroll lock. [HQ Design](https://docs.yourhq.ai/design/patterns/layout) — identical three-state pattern with Cmd/Ctrl+B toggle.

**Impact:** App is completely unnavigable on phones — only the current route is accessible, no way to switch pages. This is the highest-severity mobile issue.

**Recommendation:**
- Add hamburger button to `AppHeader` for mobile (left side, before workspace switcher).
- Implement `SidebarProvider` context with `expanded` / `collapsed` / `hidden` states.
- Mobile: sidebar renders as a `<Sheet>` overlay from the left edge, with backdrop, close on route change, close on Escape, focus trap, body scroll lock.
- Desktop (≥1024px): sidebar visible as current `w-56`. Desktop (768–1023px): optional collapsed state.
- `Cmd/Ctrl+B` keyboard shortcut toggles sidebar at all breakpoints.
- Persist collapse state in localStorage.

**Files:** `AppShellLayout.tsx`, `AppHeader.tsx`, new `SidebarProvider` context + hook, new `MobileSidebarSheet` component, `AppSidebar.tsx` extraction (sidebar content separate from layout), i18n keys

---

## M2 — Sidebar lacks expand / collapse — code-audited

**Finding:** Sidebar has a fixed `w-56` width with no collapse toggle. On narrow laptop screens (1280–1440px) this wastes 224px.

**Code evidence:**
- `AppShellLayout.tsx:44` — `w-56 shrink-0` — fixed width, no state variable, no toggle button.
- No `SidebarProvider`, `useSidebar`, `SidebarTrigger`, or collapse state in the entire codebase.

**kp-platform pattern (for reference):** `StandardSidebar.tsx:234–278` uses shadcn `Sidebar` component with `collapsible="icon"`. Collapsed = icon rail (`w-14`). `<SidebarTrigger>` hover button at the left edge toggles. State persisted in cookie. MicroTooltips on collapsed icons.

**External reference:** Collapsed width recommendation: 48–80px. Collapse toggle: icon button at sidebar bottom or after nav items, 40×40px, chevron icon rotating on state. Toggle animation: 200–300ms ease-in-out. Persist in localStorage/session.

**Impact:** Wastes 224px of horizontal space on laptops that could be reclaimed for reading findings, settings forms, or PR lists.

**Recommendation:**
- Add collapse toggle button at the bottom of the sidebar (above workspace switcher/user menu).
- Collapsed state: icon-only rail at 56–64px width with hover tooltips for item labels.
- Icon: chevron pointing left (expand) / right (collapse) — rotates on state.
- Persist in localStorage. `Cmd/Ctrl+B` shortcut.
- Collapsed mode auto-activates on 768–1023px breakpoint.
- Animate width transition 200ms ease-in-out, respect `prefers-reduced-motion`.

**Files:** `AppShellLayout.tsx`, `AppSidebar.tsx` (extracted), `SidebarProvider`, i18n keys

---

## M3 — Settings has double-level side navigation — code-audited

**Finding:** Settings pages render a secondary sidebar alongside the main sidebar — two separate nav rails competing for attention.

**Code evidence:**
- `SettingsLayout.tsx:7–9` — wraps `<SettingsSidebar />` on the left + `<Outlet />` on the right inside a `flex-col md:flex-row` container.
- `SettingsSidebar.tsx:52–84` — `<nav className="w-full shrink-0 md:w-52">` renders two groups (Personal: Profile, Security, Appearance; Workspace: Workspace, Review, Team, Integrations, Billing, Danger) with `NavLink`s.
- On desktop: main sidebar (w-56) → content area with settings sidebar (md:w-52) + form. **364px of horizontal space consumed by nav before any content.**
- On mobile: both sidebar (hidden) and settings sidebar stack vertically — but M1 means sidebar is already gone, so mobile settings is just a vertical list + form.

**kp-platform pattern:** No settings sub-navigation. Individual settings routes appear as flat sidebar items in the main nav under appropriate labels. Settings are one route per purpose.

**Impact:** Two nav panels create visual noise and extra clicks. Users must mentally map "which settings group has this page." After M1+M2 (sidebar collapse), the double-nav problem gets worse because collapsed main sidebar + expanded settings sidebar = confusing visual hierarchy.

**Recommendation:**
- Flatten settings navigation into the main sidebar under a collapsible "Settings" group (accordion/expandable section in the main nav).
- When expanded, show all settings sub-items as indented children: Profile, Security, Appearance, Workspace, Review, Team, Integrations, Billing, Danger.
- Personal + Workspace groups as subsection labels within the expandable list.
- Remove `SettingsSidebar` component and `SettingsLayout` wrapper entirely — settings routes render directly in the main content area.
- Active route matching works the same way (path prefix).
- This complements M2 — when main sidebar is collapsed, settings items are accessible via icon tooltips + expand on click.

**Files:** `SettingsLayout.tsx` (delete), `SettingsSidebar.tsx` (delete), `AppShellLayout.tsx` (add settings group), `AppSidebar.tsx`, route config, i18n keys

---

## M4 — Dashboard and settings containers are too narrow

**Finding:** Content containers use `mx-auto max-w-lg` (~512px), leaving >50% empty whitespace on desktop.

**Code evidence:**
- `DashboardPage.tsx:17` — `<div className="mx-auto max-w-lg space-y-6">` — 512px max on a ~1224px available content area.
- `SettingsLayout.tsx:9` — `<div className="mx-auto max-w-lg min-w-0 flex-1">` — same 512px cap.
- Reviewer pages (PR list, PR detail) do NOT cap width — they use full available space. This creates visual inconsistency across the app.

**kp-platform pattern:** No `max-w` on page containers — content fills available width with responsive padding, no max-width cap. Wide pages use `page-container-wide`.

**Impact:** Dashboard and settings feel artificially narrow. Settings pages like Review Settings (model dropdowns, code blocks) and Team Settings (member table) are cramped at 512px. Inconsistency with full-width reviewer tables undermines the console feel.

**Recommendation:**
- Remove `max-w-lg` from `DashboardPage` and settings content area.
- Use `max-w-3xl` (~768px) or `max-w-4xl` (~896px) as a generous limit if constrained reading width is desired; otherwise full available width with responsive padding.
- Consider `max-w-[900px]` as a reasonable cap — wide enough for tables and settings forms, narrow enough to not feel sprawling.
- Ensure all pages use the same container width for consistency.

**Files:** `DashboardPage.tsx`, `SettingsLayout.tsx` (may be deleted per M3), `DashboardPage.test.tsx`

---

## M5 — Reviewer / installations tables lack mobile adaptation

**Finding:** All reviewer tables use `overflow-x-auto` with no mobile card/stacked layout. Tables simply horizontally scroll on narrow screens.

**Code evidence:**
- `PullRequestListPage.tsx:50` — `<div className="overflow-x-auto …">` — PR list table scrolls horizontally.
- `PullRequestDetailPage.tsx:164` — `<div className="overflow-x-auto …">` — findings table scrolls horizontally.
- `ReviewerHomePage.tsx:100` — `<div className="overflow-x-auto …">` — repositories table scrolls horizontally.
- `InstallationsTable.tsx:23` — same pattern.
- No `md:` breakpoints or mobile-first card layouts on any table.

**External reference:** [Data table UI design reference guide for 2026](https://www.setproduct.com/blog/data-table-ui-design) — tables should collapse to card/stacked layout on narrow screens, show key fields as label-value pairs, and hide secondary columns. [Prowler findings table PR #9699](https://github.com/prowler-cloud/prowler/pull/9699) — redesigned findings table with rounded rows, updated badges, collapsible filters, expandable search, finding title opens detail sheet. [How to Design Data Tables](https://137foundry.com/articles/ux-patterns-data-tables-web-applications) — column-level filters, saved filter state, clear-all action.

**Impact:** Functional but poor UX on mobile — horizontal scroll with full table headers is hard to parse on narrow screens. This directly affects the reviewer and installations flows, which are the core product surfaces.

**Recommendation:**
- At `< md` breakpoint, switch tables to card/stacked layout: each row becomes a card with label-value pairs for visible columns.
- For findings table (M1 in UIUX_CONSOLE_FINDINGS): mobile card shows Severity + Title + File + State as stacked fields, with a tap to open detail sheet for full message, actions, and metadata.
- For repo/PR list tables: card layout shows name (link), full name, and status badge.
- Keep `overflow-x-auto` as fallback only.
- This complements the M1 toolbar/filters redesign — toolbar should also stack vertically on mobile, with search full-width and filters as a collapsible section.

**Files:** `PullRequestListPage.tsx`, `PullRequestDetailPage.tsx`, `ReviewerHomePage.tsx`, `InstallationsTable.tsx`, new `MobileFindingsCard`, new `MobileRepoCard` components

---

## M6 — DevNoticeWidget "Leave feedback" button uses wrong color token — code-audited

**Finding:** The feedback button uses `bg-[color:var(--app-primary)]` instead of `--app-cta-bg` / `--app-cta-fg`.

**Code evidence:**
- `DevNoticeWidget.tsx:19` — `bg-[color:var(--app-primary)]` with `text-[color:var(--app-on-accent)]`.
- 17 other button instances across the app use `bg-[color:var(--app-cta-bg)]` / `text-[color:var(--app-cta-fg)]`.
- Per `app-color-tokens.mdc` rule: CTA buttons use `--app-cta-bg` / `--app-cta-fg` pair.

**Impact:** Visual inconsistency — the feedback button looks different from all other app buttons.

**Recommendation:** Replace with `bg-[color:var(--app-cta-bg)] text-[color:var(--app-cta-fg)]`.

**Files:** `DevNoticeWidget.tsx:19`

---

## M7 — No bottom tab bar on mobile

**Finding:** No bottom navigation on mobile — after M1 is fixed (hamburger/sheet), users still need to open the sheet for every navigation action.

**kp-platform pattern:** `WorkspaceLayout.tsx` renders `<BottomNav>` with icons for key routes.

**External reference:** Bottom tab bars are a standard mobile pattern for primary navigation with 3–5 key destinations.

**Impact:** After M1 (hamburger/sheet), mobile users must open a sheet for every navigation action. A bottom tab bar would give one-tap access to the 3–4 most frequent pages.

**Recommendation:**
- Add bottom tab bar on mobile (below main content, always visible).
- Icons for: Dashboard, Reviewer (primary), Installations, Settings.
- Active state matches current route (highlight + filled icon variant).
- Hide on desktop (≥ md breakpoint). 44px minimum touch target height per tab.

**Files:** new `MobileBottomNav` component, `AppShellLayout.tsx`, i18n keys

---

## Summary table

| ID | Area | Severity | Description |
|----|------|----------|-------------|
| M1 | Mobile nav | **Critical** | No sidebar/hamburger on mobile — app is unnavigable below `md` |
| M2 | Sidebar | High | No expand/collapse toggle — wastes 224px on narrow desktops/laptops |
| M3 | Settings nav | High | Double-level side navigation (main sidebar + settings sidebar) — confusing |
| M4 | Layout | Medium | `max-w-lg` (512px) too narrow on dashboard and settings |
| M5 | Tables | Medium | No mobile card/stacked layout for reviewer/installations tables |
| M6 | DevNotice | Low | Feedback button uses `--app-primary` instead of `--app-cta-bg` |
| M7 | Mobile nav | Medium | No bottom tab bar for quick mobile navigation |

## Dependencies

- M1 blocks M7 — can't add bottom nav until hamburger/sheet nav exists.
- M2 depends on implementing `SidebarProvider` + collapse state (shared with M1).
- M3 depends on M2 — when settings links move to main sidebar, the collapse helps manage sidebar length.
- M5 (table mobile adaptation) is shared with console M1 (findings table) and M4 (Team table) — plan together.
- M6 is independent — can be fixed in any order.

---

## Cross-reference — console UX

Console findings in `UIUX_CONSOLE_FINDINGS.md` cover reviewer interaction issues that overlap:

| Layout finding | Console related |
|----|-----|
| M5 (table mobile layout) | Console M1 (findings table dense) — shared toolbar + layout redesign |
| M5 (table mobile layout) | Console M4 (Team table Actions off-screen) — same pattern |
| M1 (mobile nav) | Affects all console flows — reviewer, settings, installations |

## Out of scope

- Native mobile app, push notifications, touch gestures beyond click/press
- Mobile-specific auth flows (Biometrics, Passkeys), offline support

---

*Code-audited 2026-09-20. External references from web research appended.*
