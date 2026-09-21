# docs/visual-identity/console-ux-upgrade/CONSOLE_UX_UPGRADE_P2_EXECUTION.md

# P2 — Responsive tables (execution)

Phase **P2** of [`UIUX_CONSOLE_GENERAL_PLAN.md`](./UIUX_CONSOLE_GENERAL_PLAN.md). Baseline: [`MOBILE_AND_LAYOUT_FINDINGS.md`](./MOBILE_AND_LAYOUT_FINDINGS.md) M5. **P2 only. Frontend only.**

**Goal:** Every table in the app works on a phone screen — no horizontal scroll, cards instead of rows, key fields visible.

## Decisions locked for P2
- Breakpoint: `< md` (768px) switches from table to card layout. Use `useMediaQuery` or Tailwind `md:hidden`/`md:block` pairs.
- Card layout: `flex flex-col gap-2` wrapper, each row becomes a card with `label: value` pairs in `text-xs`/`text-sm`. Consistent `rounded-[var(--app-radius-sm)]` + `shadow-[inset_0_0_0_1px_var(--app-ring)]` border.
- No horizontal scroll on mobile — `overflow-x-auto` only on `md:` breakpoint.
- Card field sets locked per general plan (see below).
- Findings toolbar stacks vertically on mobile (search full-width, filters wrap below or in collapsible section).

## Out of scope for P2 (later phases)
- New table components for other features
- Virtualization, column resizing
- Desktop table redesign (already done in P1 for findings)
- Bottom tab bar, empty states, token fix → **P3**

---

## P2.1 — Findings table mobile cards

**What:** At `< md`, hide `<table>` (`hidden md:table`), show card list instead. Each card: Severity shape + label, Title (bold), File (mono), State badge. Tap card → opens `FindingDetailSheet` (same click handler as P1.4 desktop row). Toolbar on mobile: search input full-width at top, filter dropdowns in a collapsible "Filters" section (chevron toggle), result count right-aligned. Keep `overflow-x-auto` only on `md:overflow-x-auto` for desktop fallback.

**Files:** `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx`, `frontend/src/features/reviewer/components/FindingsToolbar.tsx` (mobile adaptation), `frontend/src/features/reviewer/pages/PullRequestDetailPage.test.tsx` (new mobile card tests — update existing)

**Deliverable:**
```bash
cd frontend && npm test -- PullRequestDetailPage FindingsToolbar
```

---

## P2.2 — PR list table mobile cards

**What:** At `< md`, hide `<table>`, show card list. Each card: `#123` number (link to PR detail, bold), Title, Status badge (PullRequestStateBadge), Head SHA (first 7 chars, mono), Revision count. `PullRequestListPage` already has `overflow-x-auto` — split to `md:overflow-x-auto` only.

**Files:** `frontend/src/features/reviewer/pages/PullRequestListPage.tsx`, `frontend/src/features/reviewer/pages/PullRequestListPage.test.tsx` (extend)

**Deliverable:**
```bash
cd frontend && npm test -- PullRequestListPage
```

---

## P2.3 — Repo list table mobile cards

**What:** At `< md`, hide `<table>`, show card list. Each card: Name (link to PR list, bold), Full name (mono). `ReviewerHomePage` already handles loading/error/empty — add card variant to the data branch.

**Files:** `frontend/src/features/reviewer/pages/ReviewerHomePage.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.test.tsx` (extend)

**Deliverable:**
```bash
cd frontend && npm test -- ReviewerHomePage
```

---

## P2.4 — Installations table mobile cards

**What:** At `< md`, hide `<table>`, show card list. Each card: Account login (bold), Status badge, Action button (Configure / Manage). `InstallationsTable` already handles data — add card variant.

**Files:** `frontend/src/features/installations/components/InstallationsTable.tsx`, `frontend/src/features/installations/components/InstallationsTable.test.tsx` (extend)

**Deliverable:**
```bash
cd frontend && npm test -- InstallationsTable
```

---

## P2.5 — Team table mobile cards + sticky Actions desktop

**What:** At `< md`, hide `<table>`, show card list. Each card: Member name + Role + Actions buttons (inline, no scroll). On desktop, Actions column receives `sticky right-0 bg-[color:var(--app-surface)]` with a left border to separate from scrollable columns. `MembersTable` already handles role change + remove — add card variant + sticky column.

**Files:** `frontend/src/features/settings/components/MembersTable.tsx`, `frontend/src/features/settings/components/MembersTable.test.tsx` (extend)

**Deliverable:**
```bash
cd frontend && npm test -- MembersTable
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- PullRequestDetailPage FindingsToolbar PullRequestListPage ReviewerHomePage InstallationsTable MembersTable
```

**Deploy:** frontend-only.

**Next:** [`CONSOLE_UX_UPGRADE_P3_EXECUTION.md`](./CONSOLE_UX_UPGRADE_P3_EXECUTION.md)
