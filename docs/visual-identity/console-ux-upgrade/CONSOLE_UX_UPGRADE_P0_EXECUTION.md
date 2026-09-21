# docs/visual-identity/console-ux-upgrade/CONSOLE_UX_UPGRADE_P0_EXECUTION.md

# P0 — Shell, sidebar & responsive layout (execution)

Phase **P0** of [`UIUX_CONSOLE_GENERAL_PLAN.md`](./UIUX_CONSOLE_GENERAL_PLAN.md). Baseline: [`MOBILE_AND_LAYOUT_FINDINGS.md`](./MOBILE_AND_LAYOUT_FINDINGS.md) M1–M4. **P0 only. Frontend only.**

**Goal:** Every page has the same responsive shell: hamburger/sheet on mobile, expand/collapse on desktop, settings in the main sidebar, content at the right width.

## Decisions locked for P0
- Three-state sidebar: expanded (w-56), collapsed (w-14 icon rail), overlaid (mobile `<Sheet>` from left).
- `SidebarProvider` context with `useSidebar()` hook — `state`, `toggle`, `expand`, `collapse`, `openMobile`, `closeMobile`.
- Collapse persisted in `localStorage` key `app-sidebar-collapsed`.
- `Cmd/Ctrl+B` keyboard shortcut registered on `keydown` in provider, killed on unmount.
- Settings flattened: expandable "Settings" accordion group in main sidebar nav, indented sub-items, remove `SettingsLayout` + `SettingsSidebar`.
- Container: `max-w-lg` → `max-w-[900px]` on `DashboardPage` and settings `<Outlet>` wrapper.
- Mobile sheet: 260px wide, backdrop (`bg-black/40`), closes on route change (useEffect on location), Escape key, backdrop click. Body scroll lock via `document.body.style.overflow`. Focus trapped.
- Animated transitions 200ms ease-in-out, killed by `prefers-reduced-motion`.
- 44px minimum touch targets on all mobile chrome.

## Out of scope for P0 (later phases)
- Findings table, merge verdict, toolbar, detail panel → **P1**
- Responsive table cards → **P2**
- Bottom tab bar, empty states, token fix, settings stubs → **P3**

---

## P0.1 — SidebarProvider context + hook

**What:** Create `frontend/src/components/layout/SidebarProvider.tsx` with `useSidebar()` context hook. State machine: `expanded` | `collapsed` | `overlaid`. Init priority: (1) localStorage `app-sidebar-collapsed` — if `"true"`, init as `collapsed`; (2) `window.matchMedia('(max-width: 1023px)').matches` — if true, init as `overlaid` (mobile), else init as `expanded` (desktop); (3) localStorage takes precedence over matchMedia — a user who collapsed on desktop stays collapsed on reload. Provider wraps `AppShellLayout` children. Keyboard shortcut: `Ctrl/Cmd + B` toggles between expanded/collapsed on desktop, opens/closes mobile sheet.

**Files:** `frontend/src/components/layout/SidebarProvider.tsx` (new), `frontend/src/components/layout/SidebarProvider.test.tsx` (new)

**Deliverable:**
```bash
cd frontend && npm test -- SidebarProvider
```

---

## P0.2 — Extract AppSidebar component

**What:** Extract sidebar content from `AppShellLayout.tsx:44–96` into new `AppSidebar.tsx`. Moves: wordmark link, nav links (Dashboard, Reviewer, Installations, Settings — Settings becomes expandable accordion in P0.5), extension nav items, workspace switcher, user menu. Receives `collapsed: boolean` prop. Collapsed mode: icon-only items with `title` attribute tooltips. Add collapse toggle button (chevron icon, 40×40px, bottom of nav, above workspace switcher).

**Files:** `frontend/src/components/layout/AppSidebar.tsx` (new), `frontend/src/components/layout/AppSidebar.test.tsx` (new), `frontend/src/components/layout/AppShellLayout.tsx` (refactor to use `AppSidebar` + `SidebarProvider`)

**Deliverable:**
```bash
cd frontend && npm test -- AppSidebar AppShellLayout
```

---

## P0.3 — Mobile hamburger + sheet overlay

**What:** Add hamburger button (`Menu` icon from `lucide-react`) to `AppHeader.tsx` at the left side (before workspace switcher). On click, calls `sidebar.openMobile()`. Create `MobileSidebarSheet` component: fixed overlay from left edge, 260px wide, backdrop with blur, renders `AppSidebar` in expanded mode. Closes on: route change (`useEffect` on `location.pathname`), Escape key, backdrop click. Body scroll lock on open, unlock on close. Use native `inert` attribute on main content when sheet is open (no focus trap library needed).

**Files:** `frontend/src/components/layout/AppHeader.tsx` (modified — add hamburger button), `frontend/src/components/layout/MobileSidebarSheet.tsx` (new), `frontend/src/components/layout/MobileSidebarSheet.test.tsx` (new), `frontend/src/components/layout/AppHeader.test.tsx` (new)

**Deliverable:**
```bash
cd frontend && npm test -- AppHeader MobileSidebarSheet
```

---

## P0.4 — Collapse toggle + icon rail

**What:** In `AppSidebar`, when `collapsed` prop is true: sidebar width transitions from `w-56` to `w-14`. Nav items render as icon-only with `title` attribute for native tooltip. Wordmark shrinks to wedge SVG only. Collapse toggle button at bottom of nav (above workspace switcher/user menu), rotates chevron on state change. Persist collapse state to localStorage on toggle. `Cmd/Ctrl+B` already wired in P0.1.

**Files:** `frontend/src/components/layout/AppSidebar.tsx` (extend from P0.2), `frontend/src/components/layout/AppSidebar.test.tsx` (extend)

**Deliverable:**
```bash
cd frontend && npm test -- AppSidebar
```

---

## P0.5 — Flatten settings into main sidebar

**What:** Add expandable "Settings" accordion group to `AppSidebar` nav. Replace the single "Settings" link with a disclosure button (chevron icon rotates on expand/collapse). When expanded, renders indented sub-items: Personal group label → Profile, Security, Appearance; Workspace group label → Workspace, Review, Team, Integrations, Billing, Danger. Use existing `PERSONAL_LINKS` / `WORKSPACE_LINKS` arrays from `SettingsSidebar.tsx` (import, don't duplicate). Active state: `isNavActive` on path prefix (already works). Remove `SettingsLayout.tsx` and `SettingsSidebar.tsx` — settings routes render directly via `Outlet`. Update route config: remove `SettingsLayout` wrapper, each settings route renders as direct child of `AppShellLayout`.

**Files:** `frontend/src/components/layout/AppSidebar.tsx` (extend), `frontend/src/components/layout/AppSidebar.test.tsx` (extend), `frontend/src/lib/routerInstance.tsx` (remove SettingsLayout wrapper), `frontend/src/features/settings/layout/SettingsLayout.tsx` (delete), `frontend/src/features/settings/layout/SettingsSidebar.tsx` (delete), `frontend/src/features/settings/layout/SettingsLayout.test.tsx` (delete), `frontend/src/features/settings/layout/SettingsSidebar.test.tsx` (delete)

**Deliverable:**
```bash
cd frontend && npm test -- AppSidebar
```

---

## P0.6 — Content container widths

**What:** Replace `max-w-lg` with `max-w-[900px]` in `DashboardPage.tsx:17`. For settings pages (now direct children of `AppShellLayout` without `SettingsLayout`), apply `max-w-[900px] mx-auto` in the `<Outlet />` wrapper or a shared settings page wrapper component. All pages now share consistent max width.

**Files:** `frontend/src/features/dashboard/pages/DashboardPage.tsx`, `frontend/src/features/dashboard/pages/DashboardPage.test.tsx`, `frontend/src/components/layout/AppShellLayout.tsx` (Outlet wrapper container)

**Deliverable:**
```bash
cd frontend && npm test -- DashboardPage AppShellLayout
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- SidebarProvider AppSidebar AppShellLayout AppHeader MobileSidebarSheet DashboardPage
```

**Deploy:** frontend-only.

**Next:** [`CONSOLE_UX_UPGRADE_P1_EXECUTION.md`](./CONSOLE_UX_UPGRADE_P1_EXECUTION.md)
