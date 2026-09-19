# docs/visual-identity/VISUAL_IDENTITY_P2_EXECUTION.md

# P2 — Product chrome (execution)

Phase **P2** of [`VISUAL_IDENTITY_GENERAL_PLAN.md`](./VISUAL_IDENTITY_GENERAL_PLAN.md). Baseline: [`VISUAL_IDENTITY_FINDINGS.md`](./VISUAL_IDENTITY_FINDINGS.md) Track C, VI-Q1 dense. **P2 only.**

**Authority:** findings VI-Q0–Q10.

**Goal:** Shell, settings, admin, and connect chrome are the dense console — not rounded starter-pack cards.

## Decisions locked for P2

- Dense intensity: hairline / inset border, not `ring-1` card elevation. **Consume** `--app-radius-sm` / `--app-radius-md` on shell + Quiet*.
- Sidebar brand = `RevyLogo` wordmark (P0 wedge + `revy`), not `common.appName` text tile.
- Settings + admin readable (Plex Sans body). Do not restyle admin into a toy CRT.
- Impersonation banner stays **unmistakable** (do not quiet it into a hairline chip).
- Installations: kill the four equal `CARD_KEYS` grid; short connect path. **No** HMAC / start-connect rewrite.
- Quiet* stay the shared inputs; token/radius only — no forks.

## Out of scope for P2 (later phases)

- Dashboard greeting, dest retarget, ReviewerNav un-gate → **P3**
- FindingRow / reviewer home hop → **P4**
- github-onboarding HMAC, start-connect JWT, live App paste

---

## P2.1 — Shell + wordmark + radius

**What:** `AppShellLayout` / header use P0 tokens, hairline sidebar (not `ring-1` as elevation), `--app-radius-*` on nav chips. Replace sidebar title with `RevyLogo`. Stack/header chrome matches.

**Files:** `frontend/src/components/layout/AppShellLayout.tsx`, `frontend/src/components/layout/AppShellLayout.test.tsx` (new), `frontend/src/components/layout/AppHeader.tsx`, `frontend/src/components/layout/StackShell.tsx`

**Deliverable:** `AppShellLayout` test asserts sidebar renders `RevyLogo` (wordmark `revy`) and nav class string includes `--app-radius-md`, not `rounded-xl`.

```bash
cd frontend && npm test -- AppShellLayout
```

---

## P2.2 — Settings, admin, impersonation

**What:** Settings surfaces and admin chrome consume overlay + radius. Keep impersonation banner contrast/copy so stop-impersonating cannot be missed. Do not retarget `ImpersonationBanner` / `AdminLayout` / `DangerZonePage` `/dashboard` fallbacks.

**Files:** `frontend/src/features/settings/pages/AppearanceSettingsPage.tsx` (chrome only if needed), `frontend/src/features/admin/layout/AdminLayout.tsx`, `frontend/src/features/admin/components/ImpersonationBanner.tsx`, `frontend/src/features/admin/layout/AdminLayout.test.tsx`, `frontend/src/features/admin/components/ImpersonationBanner.test.tsx`

**Deliverable:** impersonation tests still `navigate('/dashboard')` on stop; admin layout tests still use `/admin/dashboard`.

```bash
cd frontend && npm test -- ImpersonationBanner AdminLayout AppearanceSettingsPage
```

---

## P2.3 — Installations chrome + Quiet*

**What:** Replace four-card grid in `ConnectGitHubPanel` with a short list or single panel; primary CTA first; fallback `<details>` stays. Map Quiet* `rounded-lg` to `--app-radius-md` and inset hairline (`quiet-select`, `quiet-input`, `quiet-chip`, `quiet-date`). Same radius/hairline on `popover.tsx` (`rounded-xl` today) so Quiet dropdowns are not boxed SaaS.

**Files:** `frontend/src/features/installations/components/ConnectGitHubPanel.tsx`, `frontend/src/features/installations/components/ConnectGitHubPanel.test.tsx`, `frontend/src/components/ui/quiet-select.tsx`, `frontend/src/components/ui/quiet-input.tsx`, `frontend/src/components/ui/quiet-chip.tsx`, `frontend/src/components/ui/quiet-date.tsx`, `frontend/src/components/ui/popover.tsx`

**Deliverable:** `CARD_KEYS` four-grid is gone; connect tests still call `onConnect`; Quiet* and `popover.tsx` source use `--app-radius-md` (no `rounded-xl` on popover).

```bash
cd frontend && npm test -- ConnectGitHubPanel
```

---

**Phase gate** (from `frontend/`):

```bash
npm test -- AppShellLayout ImpersonationBanner AdminLayout AppearanceSettingsPage ConnectGitHubPanel
```

**Human gate:** none.

**Deploy:** authenticated chrome. Operator home dest still `/dashboard` until P3.

**Next:** [`VISUAL_IDENTITY_P3_EXECUTION.md`](./VISUAL_IDENTITY_P3_EXECUTION.md)
