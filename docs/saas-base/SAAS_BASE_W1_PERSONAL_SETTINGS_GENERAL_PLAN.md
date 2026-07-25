# SaaS base W1 — personal settings

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; `PATCH` APIs idempotent where applicable.

---

## Goal

Ship **personal-scope** settings: profile, security, and appearance.

**Scope:** In — `/settings/profile` (name, locale, timezone; email read-only from `/me`); `PATCH /api/v1/me` (`active` users; locale `en`|`lv`; IANA timezone); `GET /me` returns locale/timezone; i18n sync on login/profile save; `/settings/security` with Keycloak account-console link; `/settings/appearance` per [SETTINGS_IA.md](./SETTINGS_IA.md) (`localStorage` + `themeStore` + shared `applyTheme()`, no DB column); redirect `/settings` → `/settings/profile`; user menu → profile. Out — personal API keys (**deferred**), notifications (**deferred**), workspace settings, billing, avatar upload.

**Deliverables:** Profile editable after onboarding; security page documents KC boundary; theme persists via `app-theme` localStorage; complete-profile flow still works for Mode B; UI language follows saved profile locale.

**Depends on:** W0 (settings shell + user menu).

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W1_EXECUTION.md](./waves/SAAS_BASE_W1_EXECUTION.md) → `phase-execution`.
