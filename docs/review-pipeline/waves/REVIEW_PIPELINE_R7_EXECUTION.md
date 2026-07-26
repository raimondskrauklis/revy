# R7 — Reviewer UI (execution)

Phase **R7** of [REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md](../REVIEW_PIPELINE_R7_REVIEWER_UI_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** R4 API (`review-r4-v1`); publish status from R6 when available.

**Goal:** Workspace members browse PRs and findings in-app; merge readiness badge; EN+LV.

**Authority:** [SETTINGS_IA.md](../../saas-base/SETTINGS_IA.md), `frontend/src/platform/extensions/`, R4/R5 API contracts.

## Decisions locked for R7

- **Feature path:** `frontend/src/features/reviewer/`.
- **Routes (v1):** flat shell routes (workspace from `X-Workspace-Id` / store — same as `/installations`): `/reviewer` → installation/repo picker; `/reviewer/repositories/:repoId/pull-requests` → PR list; `/reviewer/repositories/:repoId/pull-requests/:prId` → findings + review run status.
- **Permissions:** `items_view` for read surfaces; reuse workspace header `X-Workspace-Id`.
- **Data:** TanStack Query hooks wrapping R4 list/findings APIs; reconciled list when R5 API exists.
- **Merge readiness badge (R6-Q2):** map latest publish check `conclusion` → badge (`success` / `neutral` / `failure`); hidden when no publish yet.
- **Nav honesty:** register reviewer nav via extension registry only when R4 findings API returns 200 for workspace (same pattern as installations widget).
- **i18n:** all strings via `t()` — EN + LV.
- **Out of scope:** inline diff viewer; dismiss/ack flows (defer to R7.6 or R8); OAuth install (Q10).

---

## R7.1 — Feature scaffold + routing

**What:** `features/reviewer/` layout; register routes in `frontend/src/lib/routerInstance.tsx` (same pattern as `/installations`); lazy load; `--app-*` tokens only.

**Files:** `features/reviewer/routes.tsx`, `ReviewerLayout.tsx`, route registration

**Deliverable:** `npm run lint` + empty route renders.

---

## R7.2 — PR list per repository

**What:** Hook `usePullRequests(repoId)`; table with number, title, head SHA, revision count; link to detail.

**Files:** `api/reviewer.ts`, `PullRequestListPage.tsx`, MSW handlers, Vitest

**Deliverable:** list loads from R2 API; empty state i18n.

---

## R7.3 — Findings list + detail

**What:** PR detail page — latest review run status, findings table (severity, category, file, message); link out to GitHub PR `html_url`.

**Files:** `PullRequestDetailPage.tsx`, `FindingRow.tsx`, tests

**Deliverable:** reads R4 `GET …/findings`; error toast via `mapApiError()`.

---

## R7.4 — Merge readiness + publish status

**What:** Badge component from publish/check conclusion; show “not published” when R6 job absent.

**Files:** `MergeReadinessBadge.tsx`, i18n keys, tests

**Deliverable:** badge states match R6-Q2 mapping.

---

## R7.5 — Nav extension + dashboard widget

**What:** extend `registerRevyExtensions()` in `platform/extensions/registerRevy.ts` — reviewer nav slot + optional dashboard widget; nav hidden until R4 API probe succeeds.

**Files:** `platform/extensions/registerRevy.ts`, `features/reviewer/ReviewerNavWidget.tsx` (or equivalent), i18n

**Deliverable:** nav hidden until R4 API probe succeeds; widget optional behind feature flag.

---

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test && npm run build
```

**Deploy:** no migration; ships with frontend deploy.

**Human gate:** EN+LV switch; browse PR → findings; badge matches GitHub check after R6.

**Next:** R8 automation / workspace review policy — see [REVIEW_PIPELINE_PRODUCT_PATTERNS.md](../REVIEW_PIPELINE_PRODUCT_PATTERNS.md).
