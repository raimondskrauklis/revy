# docs/saas-base/waves/SAAS_BASE_W1_EXECUTION.md

# W1 — Personal settings (execution)

Wave **W1** of [`SAAS_BASE_W1_PERSONAL_SETTINGS_GENERAL_PLAN.md`](../SAAS_BASE_W1_PERSONAL_SETTINGS_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) Q13, [`SETTINGS_IA.md`](../SETTINGS_IA.md). **Depends on W0.** **W1 only.**

**Goal:** Profile, security (Keycloak link), and appearance — first personal settings sidebar links.

**Authority:** `internal-docs/starter-pack/docs/backend/ME_ENDPOINT.md`, `frontend/foundations/THEME.md`, `frontend/patterns/state.md`.

## Decisions locked for W1

- `PATCH /api/v1/me` on router `""` (same prefix as `GET /me`) — body `MeUpdate`: optional `full_name`, `locale`, `timezone`; **unset fields unchanged** (partial PATCH); **email read-only** (never in body).
- `GET /me` returns `locale` + `timezone` after migration (via `build_me_response`).
- **Who may PATCH:** `active` users only — `ForbiddenError` for `suspended`, `rejected`, `pending_*` (onboarding uses `POST /users/complete-profile` for name).
- **Locale validation:** `en` \| `lv` only (match `i18n` `supportedLngs` + `locale.ts` maps).
- **Timezone validation:** IANA via `zoneinfo.ZoneInfo`; reject unknown IDs (`ValidationError`, field `timezone`).
- **i18n sync:** on `refetchUser()` and after profile save — `i18n.changeLanguage(normalizeLanguage(me.locale ?? 'en'))`; profile locale change **immediately** switches UI language.
- No DB column for theme — `localStorage` key `app-theme` (`light`|`dark`|`system`) per THEME.md; shared `applyTheme()` in `lib/theme.ts` used by FOUC script + `themeStore`.
- FOUC: **verify/enhance** existing inline script in `frontend/index.html` (already present) — must handle `light` / `dark` / `system` consistently with `applyTheme()`.
- Security page: Keycloak account console — `VITE_KEYCLOAK_ACCOUNT_URL` **if set**, else derive `{VITE_KEYCLOAK_URL}/realms/{VITE_KEYCLOAK_REALM}/account`; helper in `lib/keycloak.ts`; document password/MFA/session revoke live in KC only.
- `/settings` index **redirects** to `/settings/profile` (replaces W0 neutral shell).
- Sidebar: enable **Personal** group links only (profile, security, appearance); Workspace group labels only until W2.
- User menu profile link → `/settings/profile` (update `UserMenu.tsx` from W0).
- `QuietComponentsDemo` — removed in W0; **verify** not on any production route in W1.
- Personal API keys, notifications → **deferred program**.
- EN+LV; unit tests only.

## Out of scope for W1 (later waves)

- Workspace settings UI → **W2**
- Billing → **W4**
- Danger zone → **W6**
- Avatar upload → **reject** for W1

---

## W1.1 — User profile columns migration

**What:** Hand-written Alembic adding `users.locale` (`String(16)`, nullable, `server_default='en'`) and `users.timezone` (`String(64)`, nullable, `server_default='UTC'`); update `UserORM` with matching Python defaults.

**Files:** `backend/alembic/versions/YYYY_MM_DD_HHMM_NNNN_user_locale_timezone.py`, `backend/app/models/users.py`, `backend/tests/unit/test_users_model.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_users_model.py -q` — green (assert columns + defaults on `UserORM`).

**LOOP pause:** `alembic upgrade head` on dev DB before W1.2+.

---

## W1.2 — `PATCH /api/v1/me` + `GET /me` parity

**What:** Add `MeUpdate` + extend `MeResponse` in `schemas/me.py`. Service `update_me(session, user_id, payload)` — merge optional fields; validate locale/timezone; idempotent when body matches current values. Wire `PATCH ""` on `me.py` router. Update `build_me_response()` to include `locale`, `timezone`. Keep `POST /users/complete-profile` / `complete_user_profile` **name-only** for onboarding (locale/timezone default from migration; editable on profile page after active).

**Files:** `backend/app/services/users.py`, `backend/app/api/v1/me.py`, `backend/app/schemas/me.py`, `backend/tests/unit/test_users_service.py`, `backend/tests/unit/test_users_complete_profile.py`, `frontend/src/lib/me.ts` (`MeUser` + `locale` / `timezone` fields)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_users_service.py tests/unit/test_users_complete_profile.py -q` — green.

---

## W1.3 — Profile settings page + i18n sync

**What:** `/settings/profile` — `QuietInput` name; `QuietSelect` locale (`en`, `lv`); `QuietSelect` timezone from curated list in `frontend/src/lib/timezones.ts` (~20 common IANA zones incl. `UTC`, `Europe/Riga`, `Europe/London`, `America/New_York` — full list validated server-side on save). Email read-only/disabled. Save → `patchMe()` in `settings/api.ts` → `notify.success()` on success; `handleFormError()` / `showDomainErrorToast()` on errors; `refetchUser()` after save. **AuthContext:** on `refetchUser`, sync `i18n.changeLanguage(normalizeLanguage(me.locale ?? 'en'))`.

**Router:** add `profile` child under `SettingsLayout` (see W1.6 tree).

**Files:** `frontend/src/features/settings/pages/ProfileSettingsPage.tsx`, `frontend/src/features/settings/api.ts` (`patchMe`), `frontend/src/lib/timezones.ts`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `cd frontend && npm test -- --run ProfileSettingsPage` — green.

---

## W1.4 — Security settings page

**What:** `/settings/security` — explanatory copy (EN+LV) that credentials/MFA/sessions are managed in Keycloak; external link button to account console (`target="_blank"`, `rel="noopener noreferrer"`); **no** in-app password forms. `getKeycloakAccountUrl()` in `lib/keycloak.ts` — env override, else derive from realm URL.

**Files:** `frontend/src/features/settings/pages/SecuritySettingsPage.tsx`, `frontend/src/lib/keycloak.ts`, `frontend/.env.example` (`# VITE_KEYCLOAK_ACCOUNT_URL=` optional override), `frontend/src/lib/env.ts` (if needed for optional env)

**Deliverable:** `cd frontend && npm test -- --run SecuritySettingsPage` — green.

---

## W1.5 — Theme module + appearance page

**What:** `frontend/src/lib/theme.ts` — export `applyTheme(mode: 'light'|'dark'|'system')` (toggle `html.dark`, persist `app-theme`). `stores/themeStore.ts` (Zustand) wraps `applyTheme()`. `/settings/appearance` — `QuietSelect` or radio for light/dark/system. **Verify** `frontend/index.html` FOUC script delegates to same logic as `applyTheme()` (extract shared function or inline-equivalent). Export store from `stores/index.ts`.

**Files:** `frontend/src/lib/theme.ts`, `frontend/src/stores/themeStore.ts`, `frontend/src/stores/index.ts`, `frontend/src/features/settings/pages/AppearanceSettingsPage.tsx`, `frontend/index.html`, `frontend/src/stores/themeStore.test.ts`

**Deliverable:** `cd frontend && npm test -- --run themeStore AppearanceSettingsPage` — green.

---

## W1.6 — Settings sidebar, redirect, user menu

**What:** `SettingsSidebar` — enable Personal group `NavLink`s: profile, security, appearance (`settings.nav.profile`, `settings.nav.security`, `settings.nav.appearance`). Workspace group: labels only, no links. `/settings` index → `<Navigate to="/settings/profile" replace />`. Update `UserMenu` profile href → `/settings/profile`.

**Router tree:**

```text
/settings → AppShellLayout → SettingsLayout
  index     → Navigate /settings/profile
  profile   → ProfileSettingsPage
  security  → SecuritySettingsPage
  appearance → AppearanceSettingsPage
```

**Files:** `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/components/layout/UserMenu.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `cd frontend && npm run build` — green; manual: Personal links visible, Workspace group has no links, user menu → profile.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_users_model.py tests/unit/test_users_service.py tests/unit/test_users_complete_profile.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run ProfileSettingsPage SecuritySettingsPage AppearanceSettingsPage themeStore CompleteProfilePage settings && npm run build
```

**Deploy:** `alembic upgrade head` after W1.1 migration.

**Next:** [SAAS_BASE_W2_EXECUTION.md](./SAAS_BASE_W2_EXECUTION.md)
