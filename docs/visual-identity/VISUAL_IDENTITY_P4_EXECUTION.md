# docs/visual-identity/VISUAL_IDENTITY_P4_EXECUTION.md

# P4 — Reviewer UX (execution)

Phase **P4** of [`VISUAL_IDENTITY_GENERAL_PLAN.md`](./VISUAL_IDENTITY_GENERAL_PLAN.md). Baseline: [`VISUAL_IDENTITY_FINDINGS.md`](./VISUAL_IDENTITY_FINDINGS.md) Track R, VI-Q9. **P4 only.** Final phase — includes doc-sync.

**Authority:** findings VI-Q0–Q10.

**Goal:** Repos → PRs → findings are scannable operator tables.

## Decisions locked for P4

- Severity = **text + shape + hue** (info / warning / error / critical). Green phosphor = **merge success**, not info (info uses `--app-info` from P0).
- Finding message truncated; title stays. Path = Plex Mono; message body = Plex Sans.
- **One-repo hop:** auto-`Navigate` to `/reviewer/repositories/:id/pull-requests` only when **`installations.length <= 1` and `repositories.length === 1` after load** (nothing to pick). Do not hop while loading. Zero repos = empty. **`installations.length > 1`:** never auto-Navigate (QuietSelect stays reachable); one repo = one-row table. Multiple repos = denser table. Not a workspace PR list.
- **No bounce:** `ReviewerLayout` hides `backToRepositories` when that hop condition holds (`Link to="/reviewer"` would re-trigger Navigate). When multiple repos (or multiple installs), keep the back link to `/reviewer`. Home and layout **must** use the same predicate via `useReviewerRepoHop` (shared hook) — do not fetch twice with divergent filters.
- Installation picker = `QuietSelect` when `installations.length > 1` (already hidden at 0–1).
- Empty / loading / error copy on reviewer home **and** PR list. Error already toasts; keep a visible inline error as well.
- No in-app diff viewer. No new list API. No scanlines/glow.

## Out of scope for P4

- Diff viewer, GitHub.com clone, workspace inbox endpoint
- github-onboarding HMAC / live App paste
- Optional `post-finish-gap-pass` is a **separate** session if invoked

---

## P4.1 — Finding row scan

**What:** `FindingRow` severity cell: translated label + distinct shape (not color-only) + `--app-info` / warning / danger tokens. Truncate `message`. `file_path` stays `font-mono`; title/message `font-sans`. Merge badges on PR surfaces stay success/danger (do not retarget merge green onto info findings).

**Files:** `frontend/src/features/reviewer/components/FindingRow.tsx`, `frontend/src/features/reviewer/components/FindingRow.test.tsx`, `frontend/src/features/reviewer/components/MergeReadinessBadge.tsx` (only if merge hue would collide — keep success/danger)

**Deliverable:** tests assert all four severity labels render; long message is truncated in the DOM; merge badge tests still pass.

```bash
cd frontend && npm test -- FindingRow MergeReadinessBadge
```

---

## P4.2 — QuietSelect + one-repo hop

**What:** Reviewer home: `QuietSelect` for installation when `length > 1`. Auto-`Navigate` **only** when `useReviewerRepoHop().shouldHop`. `ReviewerLayout` hides `backToRepositories` when that same hook returns `shouldHop` (do not retarget to a workspace PR list; do not duplicate install/repo fetches with a different filter). Multiple repos: denser table (hairline, `--app-radius-sm`, drop extra action column if the row itself links).

**Files:** `frontend/src/features/reviewer/useReviewerRepoHop.ts` (new), `frontend/src/features/reviewer/useReviewerRepoHop.test.ts` (new), `frontend/src/features/reviewer/pages/ReviewerHomePage.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.test.tsx` (new), `frontend/src/features/reviewer/ReviewerLayout.tsx`, `frontend/src/features/reviewer/ReviewerLayout.test.tsx` (new)

**Deliverable:** one-install + one-repo fixture navigates to that repo’s PR list and nested layout has **no** back-to-repositories link; two-repo fixture renders a table, does not navigate, and nested layout **has** back to `/reviewer`; two-install + one-repo fixture does **not** navigate (QuietSelect visible). Home and layout both import `useReviewerRepoHop`. No native `<select>` in the DOM.

```bash
cd frontend && npm test -- useReviewerRepoHop ReviewerHomePage ReviewerLayout
```

---

## P4.3 — List empty / loading / error

**What:** Reviewer home and `PullRequestListPage` show empty, loading, and inline error (in addition to toast). Denser PR table (hairline, path/sha mono). Detail page: no scanlines; findings inherit P4.1.

**Files:** `frontend/src/features/reviewer/pages/PullRequestListPage.tsx`, `frontend/src/features/reviewer/pages/PullRequestListPage.test.tsx` (new), `frontend/src/features/reviewer/pages/PullRequestDetailPage.tsx`, `frontend/src/features/reviewer/pages/ReviewerHomePage.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** list pages have empty + loading keys; error path renders visible text, not toast-only.

```bash
cd frontend && npm test -- ReviewerHomePage PullRequestListPage FindingRow
```

---

## P4.4 — Doc-sync + changelog

**What:** README LOOP statuses Done + sha. Grep **only** the six dest files + landing copy for stale `/dashboard` as default member home — **do not** replace impersonation / danger-zone / admin `/dashboard` fallbacks (P3 out). Also grep indigo / “Ship with confidence” / `--app-info` aliases primary in this folder + overlay. Record named `--rv-*` hex in findings parking (calibration closed). User-facing changelog for the console identity.

| Doc | Change |
|-----|--------|
| `docs/visual-identity/README.md` | Phase statuses + shas |
| `docs/visual-identity/VISUAL_IDENTITY_FINDINGS.md` | Parking: hex named; status shipped |
| `docs/visual-identity/VISUAL_IDENTITY_GENERAL_PLAN.md` | Open calibration closed |
| `docs/starter-pack/SCAFFOLD_FINDINGS.md` | Q4 pointer if it still describes indigo overlay as current product paint |
| `frontend/src/data/changelog.json` | Operator console + reviewer home |

**Files:** docs listed above, `frontend/src/data/changelog.json`

**Deliverable:**

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- FindingRow MergeReadinessBadge useReviewerRepoHop ReviewerHomePage ReviewerLayout PullRequestListPage
```

**Phase gate** (from repo root):

```bash
python -m json.tool frontend/src/data/changelog.json > /dev/null
```

**Human gate:** none.

**Deploy:** frontend-only. Ship P4 with P0–P3 in the same PR if LOOP batched; otherwise last commit on the program PR.

**Next:** none.
