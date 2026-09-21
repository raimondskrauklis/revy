# docs/visual-identity/UIUX_CONSOLE_GENERAL_PLAN.md

# Console UX + mobile/layout — general plan

**Baselines:** [UIUX_CONSOLE_FINDINGS.md](./UIUX_CONSOLE_FINDINGS.md) (C1–m4) + [MOBILE_AND_LAYOUT_FINDINGS.md](./MOBILE_AND_LAYOUT_FINDINGS.md) (M1–M7). **No execution steps.**

**Thesis:** Rebuild the reviewer page as a real operator console — scannable, filterable, verdict-driven — and make the entire app shell responsive from phone to desktop. No new APIs. No diff viewer. No landing changes.

**Locked:** landing stays as-is (thin costume, single CTA). `deriveMergeConclusion` must return `'failure'` on active Critical/Error findings. Settings flatten into main sidebar. Sidebar three-state: expanded / collapsed / mobile sheet.

**Out:** workspace inbox API, diff viewer, github-onboarding HMAC, admin impersonation retarget, Greptile integration.

---

## Cross-cutting (every phase)

- **Visual:** `--app-*` tokens only. No hex in feature UI. `--app-radius-sm/md` consistent. Hairline borders.
- **i18n:** EN + LV via `t()` for every new user-facing string.
- **Tests:** Vitest colocated with every new/changed component and hook.
- **Tokens:** P0 foundations do not restyle pages — they create the sidebar context + responsive shell. Pages consume the new shell.
- **Motion:** 120–200ms snap/opacity. `prefers-reduced-motion` kills all animation.
- **Touch targets:** 44px minimum on mobile interactions.
- **Landing:** not touched. The only landing fix is the `/reviewer` logged-out flash (P3).

---

## P0 — Shell, sidebar & responsive layout

**Goal:** Every page has the same responsive shell: hamburger/sheet on mobile, expand/collapse on desktop, settings in the main sidebar, content at the right width.

**Scope:** In — `SidebarProvider` context (expanded / collapsed / overlaid states); hamburger in `AppHeader`; mobile `<Sheet>` overlay with backdrop, focus trap, body scroll lock; collapse toggle with 56px icon rail + hover tooltips; `Cmd/Ctrl+B` shortcut; collapse persisted in localStorage; settings flattened into an expandable "Settings" accordion group in the main sidebar (remove `SettingsLayout` + `SettingsSidebar`); `max-w-lg` → `max-w-[900px]` on dashboard/settings containers. Out — restyling any feature page; fixing findings, tables, or loading states (P1/P2).

**Deliverables:** Mobile hamburger opens sidebar as sheet; collapse toggles widen/narrow sidebar; settings sub-items in main nav without second sidebar; containers wider and consistent. 44px touch targets on all mobile chrome.

**Depends on:** None.

---

## P1 — Findings UX & merge verdict

**Goal:** A reviewer opens a PR and immediately sees: can I merge? The answer is a single verdict with a reason. Findings are scannable, filterable, and expandable.

**Scope:** In — `deriveMergeConclusion` returns `'failure'` when active Critical or Error findings exist, `'neutral'` when active Warning findings exist but no Critical/Error, `'success'` when zero active findings. Tiering locked: Critical/Error → Blocked, Warning only → Needs review, none → Ready. `MergeReadinessBadge` shows Ready (green, no active) / Blocked (red, Critical/Error active) / Needs review (amber, Warning active, no Critical/Error) / Unavailable (Judge down, fail closed); sticky summary bar between header and table (counts by severity, active vs resolved, next-action line); toolbar above findings table: debounced search, severity/category/state filter dropdowns, result count with "N findings" label, sortable column headers (Severity, File, Date); row click opens a `<Sheet>` detail drawer: full message, file + line range, suggestion/remediation, history, dismiss/snooze with reason dropdown; `ReconciledFinding` type extended with or fetched alongside `ReviewFinding` fields on detail open; loading skeletons (4-row ghost table, no "Not published" flash). **Detail data source locked:** use `useRevisionFindings` (existing hook in `hooks.ts`, already fetches `ReviewFinding` with `start_line`, `end_line`, `suggestion` — zero backend work). Call on detail sheet open, discard on close. No type extension needed. Out — backend API changes; new finding types; diff viewer; PR list or repo list tables (P2).

**Deliverables:** Merge badge says Blocked with reason on active Critical findings; summary bar shows "3 Critical · 7 Warning · 5 Info — 2 dismissed"; toolbar filters and sorts the table; clicking a row opens detail sheet with full message, file line reference, and dismiss/snooze controls; skeletons replace generic "Loading…" text.

**Depends on:** P0 (sidebar shell for sheet/drawer primitives).

---

## P2 — Responsive tables

**Goal:** Every table in the app works on a phone screen — no horizontal scroll, cards instead of rows, key fields visible.

**Scope:** In — all 5 tables switch to card/stacked layout at `< md` breakpoint (hide `overflow-x-auto` below md, show cards). Card field sets locked:

- **Findings table:** Severity + Title + File + State (stacked), tap → detail sheet (full message, actions, metadata per P1).
- **PR list table:** Number + Title + Status badge + Head SHA (7 chars, mono) + Revision count.
- **Repo list table:** Name (link) + Full name (mono).
- **Installations table:** Account login + Status + Action button.
- **Team table:** Member name + Role + Actions (no scroll — Actions always visible inline).

Findings toolbar stacks vertically on mobile (search full-width, filters collapsible). Team table Actions column sticky on desktop. Out — new table components for other features; virtualization; column resizing.

**Deliverables:** At 375px viewport, every table renders as stacked cards with label-value pairs; horizontal scroll never appears; toolbar adapts to single-column on mobile.

**Depends on:** P0 (shell), P1 (findings table already redesigned — P2 adds the responsive layer).

---

## P3 — Polish, empty states & bottom nav

**Goal:** Fix visual inconsistencies, add mobile bottom nav, enrich empty states, clean settings stubs.

**Scope:** In — `DevNoticeWidget` button → `--app-cta-bg` / `--app-cta-fg`; `MobileBottomNav` component (Dashboard, Reviewer, Installations, Settings — always visible on mobile, hidden on desktop, 44px touch targets, active route highlight); `PullRequestListPage` empty state: refresh button + help text + link to installations; `ReviewerHomePage` empty state: same pattern — refresh + help text + link to installations when no repos; settings audit: hide or mark Coming soon for unfinished pages (Appearance is already disabled per VI-Q2 — keep; focus on Security, Billing, Review stubs); contrast audit with automated tooling; terminology tooltips on Judge/Publish/Review badges. Out — onboarding redesign; danger zone changes; marketing pages.

**Deliverables:** CTA button consistent across app; bottom tab bar on mobile; empty repo state has next action; unfinished settings don't masquerade as working; contrast passes AA; key terms have tooltips.

**Depends on:** P0 (shell for bottom nav slot), P1 (findings table already has toolbar).

---

**Open (calibration only):** Contrast numbers from audit (P3). Named `--rv-*` hex already in VI findings parking — verify only, don't remap.

**Next:** `create-execution-plan` on this general plan.
