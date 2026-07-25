# Settings & shell IA (committed)

Repo-safe settings information architecture for SaaS base W0–W8. Full patterns: `internal-docs/starter-pack/docs/frontend/` (THEME.md, state.md, ROUTING.md).

---

## Scope groups (sidebar)

Show **two groups** in settings sidebar — not 10 flat links:

| Group | Label (i18n) | Sections |
|-------|--------------|----------|
| **Personal** | `settings.group.personal` | Profile, Security, Appearance |
| **Workspace** | `settings.group.workspace` | General, Team, Integrations, Billing, Danger |

**Rule:** Sidebar lists only routes whose wave has shipped. Unshipped routes are not linked (no “coming soon” pages).

**W8:** Workspace group links filtered by permission — `workspace` and `billing` require `admin:users`; `team`, `integrations`, and `danger` visible to any member. Matches `RequirePermission` on routes.

**Plan display (W8):** `GET /me` returns `workspace_plan: "free" | "pro" | null` for the active workspace. Dashboard extensions, checklist, and plan widget read this field — **not** `GET .../billing` (admin-only for Stripe checkout/portal).

**Tenant status:** `/workspace-suspended` when workspace is suspended; `/me` memberships exclude non-`active` workspaces.

Notifications, API keys: **deferred** — no nav entry until their wave lands.

---

## Routes

```text
/settings                    → W0: neutral shell (settings.shell.title); W1+: redirect /settings/profile
/settings/profile              W1
/settings/security             W1 (Keycloak account console link)
/settings/appearance           W1
/settings/workspace            W2
/settings/team                 W2 (includes read-only permissions matrix)
/settings/integrations         W2 (product cards; Revy → /installations)
/settings/billing              W4 — operator setup: [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md)
/settings/danger               W6
```

Platform (`super_admin`):

```text
/admin/dashboard               W5
/admin/users                   existing (Mode B signup queue)
/admin/workspaces              W5
/admin/workspaces/:id          W5
/admin/audit                   W5
/admin/settings                W5 (+ Keycloak Admin link)
```

---

## Integrations vs product nav

| Surface | Role |
|---------|------|
| `/installations` (Revy) | **Canonical** connect/manage flow |
| `/settings/integrations` | Status summary + deep-link to product route |

Fast-start for new projects: drop product nav + integration card; keep base tab shell.

---

## Extension registry (single module)

One registry, multiple slots — avoid separate widget vs integration vs chart registries.

```text
frontend/src/platform/extensions/
  registry.ts          # registerExtension({ id, slot, component, permission?, order })
  slots.ts             # Slot enum: dashboard_widget | settings_integration
```

Products register at app bootstrap (e.g. `registerRevyExtensions()`). Charts reuse `dashboard_widget` slot with `kind: 'chart'`.

---

## Theme (appearance)

Per `internal-docs/starter-pack/docs/frontend/foundations/THEME.md`:

- `localStorage` key `app-theme`: `light` | `dark` | `system`
- Toggle `html.dark` class; FOUC script in `index.html`
- Optional `stores/themeStore.ts` (Zustand) — UI state only; **no DB column**

---

## W0 anti-facade rule

- Shell layout + route outlets may exist early.
- **Sidebar/nav must not link** to pages without APIs (scaffold P2 lesson).
- Header (switcher, user menu) ships W0.
