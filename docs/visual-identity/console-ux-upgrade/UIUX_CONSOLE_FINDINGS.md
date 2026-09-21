# Revy UI/UX critical review — findings

**Date:** 2026-09-20 (code-audited 2026-09-20)
**Status:** baseline — full pass planned; no execution yet
**Purpose:** Full console UX audit: merge-readiness, findings interaction, settings, marketing surface, terminology, loading states. **No execution steps.**
**Evidence:** live app walkthrough + code audit of `frontend/src/features/reviewer/`, `frontend/src/features/settings/`, `frontend/src/components/layout/`, `frontend/src/features/marketing/`.

**Related:** `MOBILE_AND_LAYOUT_FINDINGS.md` (mobile/sidebar/settings-nav) — cross-references marked inline. Shared recommendations are duplicated in both docs so neither is orphaned.

---

## Executive summary

Revy positions itself as a GitHub-connected code-review console: connect GitHub, review findings, merge when readiness is clear. The authenticated console has a coherent information architecture (Dashboard → Reviewer → Installations → Settings) and a sensible drill-down from repository → pull request → findings.

The core product promise is not delivered in the UI. Marketing language around "lamps go green" / merge readiness is not reflected on the PR findings screen. That screen can show **Review: Completed**, **Publish: Completed**, and **Judge unavailable** while many **Active** Critical and Warning findings remain visible. A reviewer cannot answer the primary question: *is this safe to merge, and why?*

That gap is the highest-severity UX failure in this review.

---

## Product journey (as the UI presents it)

1. Land on a minimal public homepage → authenticate (Keycloak).
2. Dashboard onboarding (installations, reviewer, invite teammate, plan).
3. Connect / manage GitHub installations.
4. Open Reviewer → pick a repository → open a pull request.
5. Inspect findings; optionally run Deep / Critical review; publish / reconcile.
6. *(Intended but not clearly surfaced)* Decide merge readiness.

The last step is the product's reason to exist and is the weakest part of the experience.

---

## Critical findings

### C1. No explicit merge-readiness verdict — code-audited

**Where:** `PullRequestDetailPage.tsx:108–158` (header badges row) + `mergeConclusion.ts:4–10`

**Code evidence:**
- `deriveMergeConclusion` (mergeConclusion.ts:4–10) returns `'success'` only when zero active findings, otherwise `'neutral'`. The `'failure'` type is **declared but unreachable** — there is no severity threshold. A PR with 25 active Critical findings still gets `'neutral'`.
  ```
  4: export function deriveMergeConclusion(findings): MergeConclusion {
  5:   const active = findings.filter((item) => item.state === 'active');
  6:   if (active.length === 0) return 'success';
 10:   return 'neutral';
 11: }
  ```
- `MergeReadinessBadge.tsx:11–15` has full styling for `'failure'` (`--app-danger-subtle` / `--app-danger`) but that code path is dead.
- `PullRequestDetailPage.tsx:121–125` renders `MergeReadinessBadge` with `mergeConclusion` + `published` + `prOpen`. When `published` is false, it shows "Not published to GitHub" regardless of findings.
- `PullRequestDetailPage.tsx:126–141` shows Review Run status text ("Review: Completed · Standard") and Publish status ("Publish: Completed") as the **primary status signals** — these say "Completed" while active findings remain.

**Observation:** Header shows pipeline completion + "Judge unavailable" badge while Critical findings stay Active. No single primary verdict, no green/red lamp, no explanation.

**Why it matters:** Users will infer readiness from "Completed" language while Critical findings remain Active. For a merge-gate product, ambiguous success signals are unsafe. The `'failure'` dead code means severity was never wired to merge verdict.

**Recommendation:**
- Wire `'failure'` return in `deriveMergeConclusion` when active Critical or Error findings exist.
- Primary verdict control above the fold: **Ready** (green, 0 active findings) | **Blocked** (red, Critical/Error active) | **Needs review** (amber, Warning active, no Critical/Error) | **Unavailable** (Judge down, fail closed).
- One-line reason: "2 Critical · 3 Warning active", "Judge unavailable — blocked by default", "0 active — ready to merge".
- When Judge is unavailable, fail closed: show Blocked, not Neutral.

**Files:** `mergeConclusion.ts`, `MergeReadinessBadge.tsx`, `PullRequestDetailPage.tsx`, i18n keys

---

### C2. "Complete" pipeline vs open findings — no severity summary

**Where:** `PullRequestDetailPage.tsx:160–191` (findings table + loading/empty) — no summary bar exists above the table.

**Code evidence:**
- `PullRequestDetailPage.tsx:59–61` fetches `reconciledFindings` but never computes severity counts or displays them.
- `PullRequestDetailPage.tsx:130–148` shows Review Run + Publish status lines as the primary status — these can say "Completed" while `reconciledFindings` has active items.
- No count badge, severity summary, or next-action text anywhere in the component.

**Why it matters:** Completion language competes with unresolved risk. Attention goes to the table instead of a decision.

**Recommendation:**
- Sticky summary bar between header and table: counts by severity (info / warning / error / critical), Active vs Dismissed/Resolved counts, and a single next action.
- Do not present pipeline steps as primary status when findings remain unresolved. Pipeline status should be secondary metadata, not the headline.

**Files:** `PullRequestDetailPage.tsx`, new `FindingsSummaryBar` component, i18n keys

---

## Major findings

### M1. Findings table is dense and action-poor — code-audited

**Where:** `PullRequestDetailPage.tsx:160–191` (table markup) + `FindingRow.tsx:30–91`

**Code evidence:**
- 7 fixed-width percentage columns: Severity (12%), Category (10%), State (12%), Title (20%), File (16%), Message (22%), Actions (8%).
- `FindingRow.tsx:73–76` truncates message with `max-w-0 truncate` — the most useful content is hidden; only a hover `title` attribute shows it.
- `FindingRow.tsx:78–89` — the only action is Dismiss (admin-only). No expand, no dismiss-with-reason, no snooze, no details.
- `ReconciledFinding` (types.ts:120–135) has no `start_line`, `end_line`, or `suggestion` — those exist on `ReviewFinding` (types.ts:108–117) but are never fetched or shown.
- `useRevisionFindings` exists in hooks.ts but is **never called** from any component.
- Zero search, filter, sort controls anywhere in reviewer features.
- Infinite scroll (sentinel div at table bottom) but no result count.

**Why it matters:** In a review product, the finding is the unit of work. A scan-hostile table with only a Dismiss button blocks triage.

**Recommendation:**
- Toolbar above table: debounced search, severity/category/state filters, result count.
- Sortable columns (severity first, then file, then date).
- Row click → detail drawer/sheet: full message, file path + line range, suggestion/remediation, history, dismiss/snooze with reason dropdown.
- Fetch `ReviewFinding` data when detail panel opens (on-demand, not preloaded).
- Default visible columns: Severity, Title, File, State — rest in detail panel.
- Column resizing optional; minimum: collapse Category into detail, let Title fill available width.

**Files:** `FindingRow.tsx`, `PullRequestDetailPage.tsx`, `types.ts`, `hooks.ts`, new `FindingsToolbar`, new `FindingDetailSheet`, new `useFindingDetail` hook, i18n keys

---

### M2. Weak and contradictory loading states — code-audited

**Where:** `PullRequestDetailPage.tsx:160–161` (loading) + `PullRequestListPage.tsx` + `ReviewerHomePage.tsx`

**Code evidence:**
- `PullRequestDetailPage.tsx:160–161`: `<p>Loading...</p>` — generic text, no skeleton. The "Not published to GitHub" badge (line 121) shows `!published` immediately, then flips to ready/neutral once publish data loads.
- `PullRequestListPage.tsx`: same generic "Loading..." pattern.
- `ReviewerHomePage.tsx:99`: same pattern for repositories list.
- No skeleton components, no reserved status slots, no deferred badge rendering.

**Why it matters:** Flash of contradictory state trains users to distrust headers. "Not published" then "Ready" is confusing.

**Recommendation:**
- Skeleton placeholders for table rows during initial load.
- Defer pipeline badges (review run, publish) until data resolves — show a placeholder/grey slot, not a definitive "none" claim.
- Distinguish initial load from refresh (background refetch should not flash skeletons).
- Skeletons for PR list, repo list, findings table.

**Files:** `PullRequestDetailPage.tsx`, `PullRequestListPage.tsx`, `ReviewerHomePage.tsx`, new `TableSkeleton` component

---

### M3. Settings pages overpromise unfinished work

**Where:** Settings — Security, Appearance, Billing, Review (disabled model selectors), related stubs

**Observation:** Pages look like full product surfaces but communicate "later," "unavailable," or "not configured."

**Why it matters:** Undermines trust and clutters IA with dead ends.

**Recommendation:**
- Audit each settings page — mark clearly as "Coming soon" if not implemented.
- Hide entirely unfinished pages behind a feature flag or gate by permission.
- Prefer fewer honest settings over many placeholder screens.
- Single feedback CTA on Coming-soon pages.

**Files:** `frontend/src/features/settings/pages/` (all pages), i18n keys

---

### M4. Team table hides Actions behind horizontal scroll

**Where:** Settings → Team page

**Observation:** At typical desktop width, Actions start off-screen; horizontal scroll required.

**Why it matters:** Primary actions that require discovery scrolling are often missed.

**Recommendation:** Sticky rightmost Actions column; collapse secondary columns on narrower widths.

**Files:** Team settings page component

---

### M5. Empty repository state has no next step

**Where:** Repository with no ingested PRs — `PullRequestListPage.tsx`

**Observation:** Clear empty copy ("No pull requests ingested…") but no refresh button, webhook/ingestion help, or path back to install/config.

**Code evidence:** `PullRequestListPage.tsx` shows empty text only — no action buttons, no links, no help text.

**Recommendation:** Add refresh button, short "how PRs appear here" help text, and link to Installations / docs.

**Files:** `PullRequestListPage.tsx`, i18n keys

---

### M6. Dead linked pages return 404 — landing itself is clean

**Where:** `https://revy.createit.digital/` and linked paths

**What works:** The landing page itself is intentionally minimal — thin costume per VI-Q3: prompt-line eyebrow ("Builder console" + block cursor), single heading ("Catch corners cut before they bite"), three-line value prop ("Connect GitHub. Review findings. Merge when the lamps go green."), one CTA ("Enter console"). No feature cards, no testimonials, no slop. This direction is **locked** — do not add hero-page slop (3-card grids, trust bars, pricing tables, "Ship with confidence" copy). No dead links exist in the current landing code — `routerInstance.tsx` has no `/about`, `/features`, `/pricing`, or `/docs` routes. The earlier walkthrough 404s were from manually-typed paths, not linked from the UI.

**What's broken:** `/reviewer` when logged out briefly loads then redirects home — flash of auth page. "Enter console" does not disclose that auth is required (the CTA label is fine — just the logged-out flash is a UX glitch).

**Recommendation:**
- Fix the `/reviewer` logged-out flash — redirect before render, not after.
- No landing changes needed. No dead links to remove (none exist in code).

**Files:** `LandingPage.tsx` (no changes needed), router config (remove dead routes or redirect), auth gate for `/reviewer` flash

---

## Minor findings

### m1. Terminology drift

"Reviewer," "Code review," "Review," "Judge," and "Publish" appear without definitions. New users cannot map words to system stages.

**Recommendation:** Short glossary tooltips on key badge labels, or a "How Revy works" collapsible panel at first visit. Align all copy to one canonical vocabulary.

### m2. Onboarding progress is opaque

Dashboard shows "3 of 4 complete" but mainly surfaces the remaining "Invite a teammate" item without explaining completion criteria.

**Recommendation:** Show what counts toward each step and what's needed to complete.

### m3. Contrast on secondary text

Muted green/secondary typography on the dark theme looks borderline in places. Prefer stronger contrast for body and metadata.

**Code note:** Overlay `--rv-*` hex values in VISUAL_IDENTITY_FINDINGS.md parking lot — body `#C5E0B8` on canvas `#07140C` should pass WCAG AA. Verify with automated tooling.

**Recommendation:** Audit contrast via axe-core or similar; bump any pair below AA threshold.

### m4. Danger zone prominence

Destructive controls are correctly grouped; ensure confirmations are strong (not re-tested in this pass).

---

## What works well

- Consistent left navigation with clear active state.
- Dashboard cards give direct routes to Installations and Reviewer.
- Repository → PR → findings drill-down is understandable.
- Severity / status badges are recognizable (P4 added shapes + colors — `FindingRow.tsx:14–18`).
- Settings split into Personal vs Workspace is sensible.
- Empty and branded 404 states are concise and recoverable.
- Danger zone is isolated from day-to-day settings.

---

## Priority recommendations

| Priority | Action |
| ---: | --- |
| P0 | One merge-readiness verdict on every PR; fail closed when Judge is unavailable; wire `'failure'` return in `deriveMergeConclusion` |
| P0 | Findings summary bar (severity counts + next action) above the table |
| P1 | Finding detail drawer + filters/sort/search toolbar; stop truncating the only useful message |
| P1 | Honest loading states (skeletons); no contradictory interim status |
| P2 | Hide or clearly mark unfinished settings |
| P2 | Fix Team Actions visibility; enrich empty PR state and repo list empty state with refresh + help |
| P3 | Fix `/reviewer` logged-out flash; glossary for Review/Judge/Publish |
| P3 | Contrast audit for secondary text |
| P3 | Onboarding progress transparency |

---

## Cross-reference — mobile/layout

Mobile/layout findings in `MOBILE_AND_LAYOUT_FINDINGS.md` cover sidebar, navigation, and responsive table issues that directly affect reviewer UX:

| Console finding | Mobile/layout related |
|----|-----|
| M1 (dense table) | M5 — tables lack mobile card/stacked layout |
| M4 (Team Actions scroll) | M5 — same pattern, different table |
| M1 (no search/filter) | — desktop also needs this; same toolbar |

These should be planned together because the toolbar + table redesign must work on both desktop and mobile.

---

## Screens reviewed (authenticated)

| Area | Notes |
| --- | --- |
| Dashboard | Onboarding, installations, reviewer CTA, plan |
| Reviewer | Connected repositories |
| PR list | Open PR present; empty repo empty-state |
| PR findings | 25 findings visible in session; Judge unavailable; Deep/Critical actions |
| Installations | Active GitHub installation; install CTA → external GitHub login (not completed) |
| Settings | Profile, Security, Appearance, Workspace, Review, Team, Integrations, Billing, Danger |
| 404 | Branded not-found with Go home |
| Account menu | Profile/settings, sign out |

---

## Out of scope / not verified

- End-to-end GitHub App install and org/repo selection
- Dismiss / Deep review / Critical review / Publish side effects
- Merge behavior and any real green/red gate enforcement
- Confirmation modals on Danger zone actions

---

## Suggested next design work

1. **PR findings interaction redesign** — summary bar, filters, detail panel, dismiss with reason.
2. **Merge lamp / verdict brief** — states, fail-closed rules, copy when Judge is down.
3. **GitHub install return path** — progress, return-state, failure recovery in-product.

---

*Prepared as a UI/UX critical review of the live Revy console and public surface. Code-audited 2026-09-20.*