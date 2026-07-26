# docs/models/waves/MODEL_POLICY_M3_EXECUTION.md

# M3 — Review settings UI (execution)

Phase **M3** of [`MODEL_POLICY_GENERAL_PLAN.md`](../MODEL_POLICY_GENERAL_PLAN.md). **M3 only — final phase.**

**Goal:** Workspace admins configure models and autostart at `/settings/review`.

**Depends on:** M2 PASS.

## Decisions locked for M3

- Route **`/settings/review`** — flat settings sibling (SETTINGS_IA); admin `admin:users`.
- Sidebar: `settings.nav.review` under Workspace group.
- Sections: **Automation** (`review_autostart_enabled` moved from Workspace General); **Models** — four dropdowns (standard / deep / critical / judge).
- Dropdowns: “Platform default” (PATCH `null`) + catalog options; all four roles shown even when platform Bedrock uses one reviewer model id — workspace may still override per role.
- Non-blocking warning when effective reviewer + judge share provider (MP-D7); EN+LV.
- No embedding, jury, BYOK.

## Out of scope for M3

- Custom rules (`workspace_review_policy` text) → R8+
- Plan-tier caps → Q9

---

## M3.1 — API client + types

**What:** `fetchModelCatalog`, `fetchModelPolicy`, `patchModelPolicy`; types for overrides + effective models.

**Files:** `frontend/src/features/settings/api.ts`, `frontend/src/features/settings/types.ts`, `frontend/src/features/settings/hooks.ts`

**Deliverable:** `cd frontend && npm run lint` — clean on touched files.

---

## M3.2 — ReviewSettingsPage

**What:** Autostart toggle + four `QuietSelect` dropdowns; load/save via M2 API.

**Files:** `frontend/src/features/settings/pages/ReviewSettingsPage.tsx`, `frontend/src/features/settings/pages/ReviewSettingsPage.test.tsx`

**Deliverable:** `cd frontend && npm test -- ReviewSettingsPage -q` — green.

---

## M3.3 — Router + sidebar + i18n

**What:** `/settings/review` in router; sidebar link; `settings.review.*` + `settings.nav.review` EN+LV.

**Files:** `frontend/src/lib/routerInstance.tsx`, `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`, `frontend/src/features/settings/layout/SettingsSidebar.test.tsx`

**Deliverable:** `cd frontend && npm test -- SettingsSidebar ReviewSettingsPage -q` — green.

---

## M3.4 — Workspace General cleanup

**What:** Remove `review_autostart_enabled` from `WorkspaceSettingsPage` (moved to Review settings only).

**Files:** `frontend/src/features/settings/pages/WorkspaceSettingsPage.tsx`, `frontend/src/features/settings/pages/WorkspaceSettingsPage.test.tsx`

**Deliverable:** `cd frontend && npm test -- WorkspaceSettingsPage ReviewSettingsPage -q` — green.

---

## M3.5 — Doc sync

| Doc | Change |
|-----|--------|
| `docs/models/README.md` | Program shipped |
| `docs/models/waves/README.md` | M0–M3 Done + sha |
| `docs/models/MODEL_POLICY_FINDINGS.md` | Shipped summary |
| `docs/saas-base/SETTINGS_IA.md` | Add `/settings/review` row |
| `docs/utils/GITHUB_APP_TARGET_CONFIG.md` | Workspace policy API + UI |
| `docs/saas-base/OPS.md` | Model policy operator note |

**Deliverable:** No stale `/settings/workspace/review` or env-only-only claims in `docs/models/`.

---

**Phase gate** (from `frontend/`):

```bash
npm run lint
npm test -- ReviewSettingsPage SettingsSidebar WorkspaceSettingsPage --run
npm run build
```

**Phase gate** (from `backend/`):

```bash
cd backend && pipenv run pytest tests/unit/test_workspace_model_policy_routes.py tests/unit/test_model_policy.py -q
```

**Human gate (non-gate):** Staging — change workspace judge model → run review → verify `github_review_runs.model_id` and `github_finding_judge_outcomes.judge_model_id` match effective policy.

**Deploy:** FE + BE together; `alembic upgrade head` through `0023`.

**Next:** none — optional `post-finish-gap-pass` on `docs/models/`.
