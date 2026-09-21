# docs/visual-identity/console-ux-upgrade/CONSOLE_UX_UPGRADE_P1_EXECUTION.md

# P1 — Findings UX & merge verdict (execution)

Phase **P1** of [`UIUX_CONSOLE_GENERAL_PLAN.md`](./UIUX_CONSOLE_GENERAL_PLAN.md). Baseline: [`UIUX_CONSOLE_FINDINGS.md`](./UIUX_CONSOLE_FINDINGS.md) C1–M2. **P1 only. Frontend only.**

**Goal:** A reviewer opens a PR and immediately sees: can I merge? The answer is a single verdict with a reason. Findings are scannable, filterable, and expandable.

## Decisions locked for P1
- `deriveMergeConclusion` tiering: Critical/Error active → `'failure'` (Blocked), Warning active + no Critical/Error → `'neutral'` (Needs review), zero active → `'success'` (Ready).
- `MergeReadinessBadge` already has `'failure'` styling — just needs the code path to be reachable.
- `MergeReadinessBadge` new states: Ready (green, `'success'`), Blocked (red, `'failure'`), Needs review (amber, `'neutral'`), Not published (grey, existing), Unavailable (orange, Judge down → Blocked).
- Summary bar between header and table: sticky, shows severity counts (Critical/Error/Warning/Info), Active vs Dismissed/Resolved counts, next-action line.
- Toolbar: debounced search (300ms), severity/category/state filter dropdowns (multi-select chips), result count, sortable headers (Severity, File, Date).
- Detail sheet: click any finding row → `<Sheet>` from right edge (or bottom on mobile), fetches `ReviewFinding` data via `useRevisionFindings` (existing hook), shows full message, file + line range, suggestion, history, dismiss/snooze with reason dropdown.
- Skeletons: 4-row ghost table (pulsing `--app-chip` bars), replaces "Loading…" text. Pipeline badges show placeholder slot (not "none" claim) until data resolves.

## Out of scope for P1 (later phases)
- Responsive table cards → **P2**
- Toolbar mobile stacking → **P2**
- Bottom tab bar, empty states, token fix → **P3**

---

## P1.1 — Wire merge verdict tiering

**What:** Update `deriveMergeConclusion` in `mergeConclusion.ts`: when `active` findings include any `'critical'` or `'error'` severity, return `'failure'`. When active findings include `'warning'` (but no critical/error), return `'neutral'`. When zero active findings, return `'success'` (unchanged). Update `MergeReadinessBadge` to render Blocked label when `conclusion === 'failure'` and `published` is true. Add i18n key `reviewer.mergeReadiness.failure` in EN + LV. Update `mergeConclusion.test.ts` with new tiering test cases.

**Files:** `frontend/src/features/reviewer/mergeConclusion.ts`, `frontend/src/features/reviewer/mergeConclusion.test.ts`, `frontend/src/features/reviewer/components/MergeReadinessBadge.tsx`, `frontend/src/features/reviewer/components/MergeReadinessBadge.test.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- mergeConclusion MergeReadinessBadge
```

---

## P1.2 — Severity summary bar

**What:** New `FindingsSummaryBar` component rendered between header badges and findings table in `PullRequestDetailPage`. Computes from `reconciledFindings`: count by severity (critical, error, warning, info), count by state (active vs dismissed/resolved). Shows one-line verdict: "3 Critical · 7 Warning · 5 Info — 2 dismissed" with colored severity text. Next-action line: "Blocked — dismiss or resolve 3 Critical findings to unblock" / "Ready to merge" / "Judge unavailable — blocked by default". Stick to top of content area on scroll.

**Files:** `frontend/src/features/reviewer/components/FindingsSummaryBar.tsx` (new), `frontend/src/features/reviewer/components/FindingsSummaryBar.test.tsx` (new), `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx` (insert between header + table), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- FindingsSummaryBar PullRequestDetailPage
```

---

## P1.3 — Findings toolbar (search, filters, sort)

**What:** New `FindingsToolbar` component above findings table in `PullRequestDetailPage`. Debounced search input (300ms) filters findings client-side by title + message + file_path (case-insensitive). Three filter dropdowns: Severity (checkboxes for info/warning/error/critical), Category (security/bug/performance/style/maintainability/other), State (active/superseded/resolved). Active filters render as removable chips. Result count: "12 findings" (updates live). Sortable column headers: click Severity/File/Date header → toggle asc/desc, show arrow indicator, `aria-sort` attribute. Client-side sort + filter on `reconciledFindings` array — no new API calls.

**Files:** `frontend/src/features/reviewer/components/FindingsToolbar.tsx` (new), `frontend/src/features/reviewer/components/FindingsToolbar.test.tsx` (new), `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx` (insert toolbar above table), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- FindingsToolbar PullRequestDetailPage
```

---

## P1.4 — Finding detail sheet

**What:** New `FindingDetailSheet` component: `<Sheet>` from right edge (P0 shell provides the Drawer/Sheet primitive context). On row click in `FindingRow`, opens sheet for that finding. Fetches `ReviewFinding` data via `useRevisionFindings(revisionId)` — shows: full message (no truncation), file path (mono) + line range (if `start_line`/`end_line` exist), suggestion/remediation (if present), severity/category/state badges, dismiss button with reason dropdown (Dismissed by admin / Fixed since last push / False positive / Superseded), snooze option (TBD — placeholder). Dismiss action calls existing `dismissFindingGroup` mutation. Sheet close button + Escape key + backdrop click.

**Files:** `frontend/src/features/reviewer/components/FindingDetailSheet.tsx` (new), `frontend/src/features/reviewer/components/FindingDetailSheet.test.tsx` (new), `frontend/src/features/reviewer/components/FindingRow.tsx` (add row click handler), `frontend/src/features/reviewer/components/FindingRow.test.tsx` (update), `frontend/src/features/reviewer/hooks.ts` (no changes — `useRevisionFindings` already exists), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
cd frontend && npm test -- FindingDetailSheet FindingRow
```

---

## P1.5 — Loading skeletons + deferred badge rendering

**What:** Replace `<p>Loading...</p>` in `PullRequestDetailPage` finding table area with a 4-row skeleton table: each row has pulsing bars (`animate-pulse bg-[color:var(--app-chip)]`) matching the column layout. Pipeline badges (review run status, publish status, MergeReadinessBadge when not yet published) render as grey placeholder slots (empty grey chip, no text claiming "none" or "not published") until their respective queries resolve. PR list page (`PullRequestListPage`) and repo list page (`ReviewerHomePage`) also get skeleton rows (3-row placeholder table).

**Files:** `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx`, `frontend/src/features/reviewer/pages/PullRequestListPage.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.tsx`, `frontend/src/components/ui/TableSkeleton.tsx` (new, shared), `frontend/src/features/reviewer/pages/PullRequestListPage.test.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.test.tsx` (update for skeleton state)

**Deliverable:**
```bash
cd frontend && npm test -- PullRequestDetailPage PullRequestListPage ReviewerHomePage TableSkeleton
```

---

## P1.6 — i18n parity validation

**What:** EN + LV keys already added in each subphase (P1.1–P1.5). This subphase validates parity: every key in `en.json` under `reviewer.mergeReadiness`, `reviewer.summary`, `reviewer.toolbar`, `reviewer.detail` must have a corresponding LV key with non-empty value. No new keys created here — only validation + filling any gaps. Verify JSON validity of both locale files.

**Files:** `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**
```bash
python -m json.tool frontend/src/i18n/locales/en.json > /dev/null && python -m json.tool frontend/src/i18n/locales/lv.json > /dev/null
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- mergeConclusion MergeReadinessBadge FindingsSummaryBar FindingsToolbar FindingDetailSheet FindingRow PullRequestDetailPage PullRequestListPage ReviewerHomePage TableSkeleton
```

**Deploy:** frontend-only.

**Next:** [`CONSOLE_UX_UPGRADE_P2_EXECUTION.md`](./CONSOLE_UX_UPGRADE_P2_EXECUTION.md)
