# SaaS base — findings

Baseline for a **fast-start SaaS foundation** on starter-pack rails. **No execution steps.**

**Status:** baseline-ready — W0–W8 **shipped** (2026-07-25).

---

## Goal

Ship a **fast-start SaaS shell** for new projects on starter-pack rails. Revy is first consumer; product verticals remain additive (not removed for “clone”).

Priority surfaces: **user dashboard + settings** (personal + workspace) and **platform admin** (workspace directory, KPIs, audit) for `super_admin`. **Keycloak Admin Console** for platform identity ops — in-app user directory is a **separate future program**.

---

## Build principles

- **Starter-pack is the pattern source** — specs in `internal-docs/starter-pack/docs/`; templates in `internal-docs/starter-pack/templates/`. Product overlays (Revy) stay thin.
- **Scope-first settings IA** — separate **Personal**, **Workspace**, and **Platform** settings; never mix scopes without explicit labels ([setting.page IA guide](https://setting.page/settings-information-architecture-account-app-admin)).
- **Keycloak = auth, PostgreSQL = authorization** — JWT proves identity only; `users.status`, `users.platform_role`, `workspace_memberships.role` drive API permissions ([AUTHZ_MODEL.md](internal-docs/starter-pack/docs/backend/AUTHZ_MODEL.md)). Do not read Keycloak realm roles in FastAPI.
- **No duplicate user admin UI** — password/MFA/session/disable-user → Keycloak; app owns signup lifecycle + workspace RBAC only.
- **Backend enforcement** — plan gates, RBAC, tenancy in API middleware; frontend hides nav but does not authorize ([BILLING.md](internal-docs/starter-pack/docs/backend/BILLING.md)).
- **Additive, not subtractive** — Revy `installations` and items demo remain; base settings routes use generic names (`/settings/team`). Product nav entries coexist.
- **Hand-written Alembic**, unit tests only, EN+LV i18n, `--app-*` tokens — same as scaffold program.
- **Nav honesty** — sidebar links only for shipped waves; layout routes may exist unlinked ([SETTINGS_IA.md](./SETTINGS_IA.md)).
- **Single extension registry** — dashboard widgets, settings integration cards, future charts share one `platform/extensions` registry.

---

## Terminology

| Term | Meaning |
|------|---------|
| **SaaS base** | Reusable platform shell: auth, workspaces, RBAC, dashboard, settings, platform admin |
| **Product vertical** | Domain-specific slice (Revy: GitHub installations → reviews) — plugs into base nav |
| **Personal settings** | User-scoped: profile, security, notifications, appearance |
| **Workspace settings** | Tenant-scoped: general, team, billing, integrations, danger zone |
| **Platform staff** | `users.platform_role = super_admin` — platform settings, signup approval (Mode B), workspace oversight; **no** in-app user directory |
| **Workspace admin** | `workspace_memberships.role = admin` — team, invites, workspace config, billing UI |
| **Workspace operator / viewer** | `operator` / `viewer` — product access per `ROLE_PERMISSIONS`; not workspace settings admins |
| **super_admin bootstrap** | PG seed `platform_role` + KC user same email → first login binds `keycloak_user_id` — see [BOOTSTRAP_SUPER_ADMIN.md](../../internal-docs/starter-pack/docs/backend/BOOTSTRAP_SUPER_ADMIN.md) |
| **Keycloak** | Identity provider — credentials, MFA, SSO; **not** app RBAC source |
| **starter-pack** | Generic template under `internal-docs/starter-pack/` |
| **Fast-start** | Copy repo patterns + strip product folders for next project — not a separate package yet |

---

## What exists vs genuinely new

### Verified — in Revy repo today (reusable base)

| Layer | Capability | Evidence |
|-------|------------|----------|
| Auth | Keycloak OIDC + JWT (RS256, JWKS, audience allowlist) | `backend/app/core/auth.py`, `frontend/src/lib/keycloak.ts` |
| RBAC | Platform `super_admin` + workspace `admin`/`operator`/`viewer` + permission matrix | `backend/app/core/permissions.py`, `enums.py` |
| Tenancy | `X-Workspace-Id`, `require_workspace`, `require_same_workspace` | `backend/app/core/tenancy.py` |
| Registration | Mode A (open) + Mode B (profile + admin approval) | `REGISTRATION_FLAGS.md`, `CompleteProfilePage`, admin approve APIs |
| Platform admin | Signup pending queue — list, approve, reject | `/admin/users`, `backend/app/api/v1/admin/` |
| User API | `GET /me`, `PATCH /me` (profile — **W1**), `PATCH /me/workspace`, `POST /users/complete-profile` | `backend/app/api/v1/me.py` |
| Invitations | Create + accept API + email dispatch | `workspaces/invitations.py`, P3 migration |
| Infra patterns | Pagination, idempotency, email, Celery, health, exceptions | `internal-docs/starter-pack/docs/CROSS_CUTTING.md` |
| Frontend shell | App shell, protected routes, status gates, i18n EN/LV, Quiet* inputs | `AppShellLayout.tsx`, `ProtectedRoute.tsx` |
| Settings route | `/settings` exists | **Stub** — `QuietComponentsDemo` only |
| Dashboard route | `/dashboard` exists | **Stub** — welcome text only; full dashboard **W3** |

### Verified — starter-pack specs (not yet fully implemented in repo)

| Spec | Doc | Gap in repo |
|------|-----|-------------|
| Billing & plan gating | `backend/BILLING.md` | Schema columns on `workspaces`; Stripe routes/webhooks + gating ship **W4** |
| Account lifecycle | `backend/ACCOUNT_LIFECYCLE.md` | `PATCH /me` profile **W1**; export/delete/leave **W6** |
| Audit log | `backend/AUDIT.md` | `api_audit` table + mutation writes ship **W2**; read API **W3**; platform search **W5** |
| In-app notifications | CROSS_CUTTING § Partial | Celery stub; no feed or preferences |
| Settings IA | [SETTINGS_IA.md](./SETTINGS_IA.md) | W0 commits; mirror to starter-pack |

### Genuinely new (this program)

- **Settings information architecture** — personal vs workspace sub-routes, sidebar nav, scope labels.
- **Workspace management UI** — switcher, general settings, team members, invitation list/revoke.
- **User dashboard** — workspace-aware home (activity, quick actions, empty states) — product-agnostic widgets.
- **Platform settings page** — read-only platform config + link to Keycloak Admin for identity ops.
- **Full Stripe integration** — checkout, customer portal, webhooks, plan gating per BILLING.md.

### Reuse caveats / traps

| Trap | Detail |
|------|--------|
| **Two RBAC layers** | `super_admin` is platform (no workspace membership); `admin` is per-workspace — never conflate in UI labels |
| **Keycloak Organizations vs app workspaces** | KC Organizations (KC 26+) is optional IdP grouping; **app `workspaces` table** remains tenant boundary — do not merge without explicit design |
| **Items demo** | Backend CRUD exists; no FE page — pattern reference only |
| **`RequirePermission` unused** | FE route guards exist but not wired to settings sub-routes |
| **No workspace switcher UI** | `PATCH /me/workspace` works; header has no switcher |
| **Billing service removed** | P3 removed `billing.py`; restore from template for Stripe work |
| **Signup queue vs KC user admin** | `/admin/users` approve/reject is **app lifecycle** (`users.status`), not a substitute for Keycloak user management |

---

## Catalog — universal sections

Industry consensus (2025–2026): group by **user mental model and scope**. Wave column = when it ships.

| Section | Rationale | Revy state | Wave |
|---------|-----------|------------|------|
| **Profile** | Name, locale, timezone | Onboarding name only; `PATCH /me` + settings page **W1** | **W1** |
| **Security** | KC account console link | KC handles auth | **W1** |
| **Appearance** | Theme via `localStorage` + `html.dark` (THEME.md) | No toggle yet | **W1** |
| **Personal API keys** | Developer API access | Missing | **Deferred** |
| **Notifications** | Email + in-app | Missing | **Deferred** |
| **Danger zone** | Export, delete account | No API; **W6** | **W6** |

### B. End-user — Workspace settings

**API vs UI:** General, team, and invitation **APIs** ship in **W0** ([W0 execution](./waves/SAAS_BASE_W0_EXECUTION.md)). **Settings pages**, permissions matrix UI, integrations tab, and audit writes ship in **W2**. Wave column below = **UI wave**.

| Section | Rationale | Revy state | Wave |
|---------|-----------|------------|------|
| **General** | Workspace name, slug | APIs W0; UI **W2** | **W2** |
| **Team / members** | List, invite, role, remove | APIs W0; UI **W2** | **W2** |
| **Invitations** | Pending, revoke | Create API exists; list/revoke APIs W0; UI **W2** | **W2** |
| **Permissions matrix** | Read-only role reference | Fixed 3 roles; UI **W2** | **W2** |
| **Integrations** | Base tab + product cards | Revy installations; UI **W2** | **W2** |
| **Billing & plan** | Stripe self-serve | Schema only; full Stripe **W4** | **W4** |
| **Danger zone** | Leave / delete workspace | No API; full lifecycle **W6** | **W6** |

### C. End-user — Dashboard

| Widget | Rationale | Revy state | Wave |
|--------|-----------|------------|------|
| **Welcome + context** | Workspace awareness | Stub page | **W3** |
| **Setup checklist** | Onboarding progress | Missing | **W3** |
| **Quick actions** | Primary CTAs | Missing | **W3** |
| **Recent activity** | Audit-lite card (`GET .../audit`) | Audit writes W2; read API **W3** | **W3** |
| **Product widgets** | Registry `dashboard_widget` slot | W2 starts registry; widget **W3** | **W3** |
| **Plan summary** | Billing status | Missing; widget **W4** | **W4** |

**IA:** [SETTINGS_IA.md](./SETTINGS_IA.md) — two sidebar groups (Personal / Workspace); ≤7 visible items via grouping.

```text
/dashboard
/settings/profile | security | appearance          # W1
/settings/workspace | team | integrations          # W2
/settings/billing                                   # W4
/settings/danger                                    # W6
/admin/dashboard | users | workspaces | audit | settings  # W5
```

### D. Platform super-admin (W5 + W7)

**Locked:** workspace directory, KPI dashboard, audit search, platform settings. **No in-app user directory** — Keycloak Admin for identity; full user panel = **future program**. Impersonation = W7.

| Section | Wave | Revy state |
|---------|------|------------|
| Signup queue (Mode B) | existing | **Implemented** |
| Platform settings + KC link | W5 | Partial — queue exists |
| Workspace directory + suspend | W5 | APIs + UI **W5** |
| Workspace detail (read-first) | W5 | **W5** |
| Platform KPI dashboard | W5 | **W5** |
| Audit log search (cross-tenant) | W5 | Workspace-scoped read W3; platform search **W5** |
| Impersonation | W7 | **Shipped** — W8 closes leave deny-list + audit gaps |
| In-app user directory | **future program** | N/A |

```text
/admin/dashboard                    # KPIs (W5)
/admin/users                        # signup queue (exists)
/admin/workspaces                   # directory (W5)
/admin/workspaces/:id               # detail (W5)
/admin/audit                        # search (W5)
/admin/settings                     # platform config + KC link (W5)
# W7: impersonation APIs + SPA banner
# Future program: in-app user directory
```

**RBAC model (locked, matches starter-pack):**

```text
Keycloak          →  sub, email, email_verified, password/MFA/SSO
PostgreSQL users  →  status, platform_role (super_admin | NULL)
PostgreSQL memberships → admin | operator | viewer per workspace
API               →  require_permission + require_same_workspace (DB only)
```

Workspace `admin` manages **their workspace** (team, billing, settings). `super_admin` manages **platform** via `platform_role` — not a workspace role; no workspace membership.

---

## Audit table (locked schema — W2 migration)

Based on existing tables (`users.id` UUID, `workspaces.id` UUID). Extends AUDIT.md sketch for multi-tenant + W7 impersonation:

```sql
api_audit (
  id              UUID PRIMARY KEY,
  created_at      TIMESTAMPTZ NOT NULL,
  actor_user_id   UUID NOT NULL REFERENCES users(id),   -- real PG user
  impersonator_user_id UUID NULL REFERENCES users(id), -- W7
  workspace_id    UUID NULL REFERENCES workspaces(id), -- NULL for platform-only
  action          TEXT NOT NULL,
  resource_type   TEXT,
  resource_id     TEXT,
  metadata        JSONB DEFAULT '{}'
)
```

Index: `(workspace_id, created_at DESC)` for W3 lite feed; `(created_at DESC)` for W5 cross-tenant search with `super_admin` guard.

**Writable from W2:** team mutations. **W3:** read. **W5:** search + platform read audit. **W6/W7:** lifecycle + impersonation.

---

## Workspace API ownership

| Operation | API | Who | Table |
|-----------|-----|-----|-------|
| Rename workspace | `PATCH /api/v1/workspaces/{id}` | Workspace `admin` | `workspaces.name` (slug immutable v1) |
| List/suspend workspace | `GET/POST /api/v1/admin/workspaces/...` | `super_admin` only | `workspaces.status` (`active`/`suspended`) |
| Team CRUD | `.../workspaces/{id}/members` | Workspace `admin` | `workspace_memberships` |
| Invitations | existing + list/revoke | Workspace `admin` | `workspace_invitations` |

`Permission.admin_workspaces` / `admin_system` — reserved for future staff tiers; W5 gates on `is_super_admin` only (Q10).

---

## Deferred program (explicit — not W0–W7)

| Item | Why deferred |
|------|----------------|
| Personal API keys | Separate auth subsystem (Bearer middleware, schema, rotation) |
| Notifications (email + in-app) | Separate notification system |
| File handling / uploads | Separate storage wave |
| In-app platform user directory | Keycloak Admin + future program |

---

## Platform bootstrap (super_admin)

```text
1. BOOTSTRAP_SUPER_ADMIN_EMAIL in .env
2. seed_bootstrap_super_admin.py → users row (platform_role, pending_activation)
3. Register same email in Keycloak (identity only)
4. First login → get_current_user binds sub, status=active
5. Remove env var; access /admin/* via platform_role in PostgreSQL
```

Keycloak does **not** assign `super_admin`. App does **not** duplicate KC user CRUD in W0–W7.

---

## Locked decisions (2026-07-25)

| Q# | Decision |
|----|----------|
| Q1 | Program in `docs/saas-base/` — W0–W8; W8 = hardening + doc sync; deferred program explicit |
| Q2 | Nested `/settings/*` + two sidebar groups ([SETTINGS_IA.md](./SETTINGS_IA.md)) |
| Q3 | Shared shell; W5 platform admin (split W5.1/W5.2 at execution) |
| Q4 | Stripe standard (W4) |
| Q5 | Security → KC account console |
| Q6 | Single extension registry + dashboard widgets |
| Q7 | Revy vertical additive |
| Q8 | Items demo — pattern reference / fast-start strip optional |
| Q9 | Audit locked schema (W2→W7) |
| Q10 | Single `super_admin`; W5 uses `platform_role` not KC roles |
| Q11 | No KC Organizations |
| Q12 | Workspace directory W5 |
| Q13 | Appearance W1 — localStorage per THEME.md |
| Q14 | Permissions matrix W2 |
| Q15 | Integrations W2 — link to product nav |
| Q16 | Dashboard audit-lite W3 |
| Q17 | Notifications — **deferred program** |
| Q18 | Impersonation W7 — server-side fields |
| Q19 | User directory — **deferred program** |
| Q20 | Stripe standard |
| Q21 | API keys — **deferred program** |
| Q22 | File handling — **deferred program** |
| Q23 | No nav links until wave ships |
| Q24 | Single extension registry |
| Q25 | W5 execution split |
| Q26 | Items demo keep in Revy |
| Q27 | `/installations` canonical; settings tab links |

**Waves:** [README.md](./README.md) — W0–W8 **complete**.

---

## External research / patterns — SaaS base essentials

Focused synthesis for **what every B2B multi-tenant clone needs** (not full ops admin panel).

### Foundation (architecture)

| Source | Takeaway | Adopt / defer / reject |
|--------|----------|------------------------|
| [Clerk multi-tenancy](https://clerk.com/blog/what-is-multi-tenancy-and-why-it-matters-for-b2b-saas) | Collaborative workspaces, org admin portal, tenant switching, strict data isolation | **Adopt** |
| [AWS multi-tenant](https://aws.amazon.com/isv/resources/5-multi-tenant-saas-architecture/) | Tenant context as first-class dimension across identity, data, billing | **Adopt** |
| [Seedium architecture](https://seedium.io/blog/how-to-build-multi-tenant-saas-architecture/) | AuthZ + tenant-aware DB from day one; automate tenant lifecycle | **Adopt** |
| [AUTHZ_MODEL.md](internal-docs/starter-pack/docs/backend/AUTHZ_MODEL.md) | KC = identity; PG = status + platform_role + membership roles | **Adopt** (already locked) |
| [Keycloak Organizations](https://keycloakpro.com/blog/keycloak-multi-tenancy-organizations-guide) | KC 26+ orgs optional at IdP layer | **Reject** — app workspaces only (Q11) |
| [Skycloak auth guide](https://skycloak.io/blog/multi-tenant-authentication-architecture-guide/) | Always enforce isolation at app/DB layer regardless of KC pattern | **Adopt** |

### End-user shell (what boilerplates ship)

| Capability | Industry baseline | Our scope |
|------------|-------------------|-----------|
| Workspace + memberships | Tenanto, Clerk, Stripe docs | **W0/W2** — APIs then team UI |
| Settings IA (personal / workspace) | [setting.page](https://setting.page/settings-information-architecture-account-app-admin), TheFrontKit | **W0** shell, **W1/W2** content |
| Self-serve billing | [Stripe SaaS guide](https://docs.stripe.com/saas), [Stripe subscriptions](https://docs.stripe.com/get-started/use-cases/saas-subscriptions) | **W4** — isolated wave |
| Customer Portal | Stripe-hosted plan/payment/invoice management | **W4** — redirect, not custom UI |
| Dashboard + onboarding checklist | Tenanto, Vellocity | **W3** |
| Notifications prefs | setting.page checklist | **Deferred program** |

### Billing (Stripe — locked full integration)

| Source | Takeaway | Adopt |
|--------|----------|-------|
| [Stripe SaaS](https://docs.stripe.com/saas) | Checkout + Customer Portal + webhooks = minimum viable billing | **Adopt** |
| [Stripe webhooks](https://docs.stripe.com/billing/subscriptions/webhooks) | `checkout.session.completed`, `customer.subscription.updated/deleted`, `invoice.paid`, `invoice.payment_failed` | **Adopt** |
| [DesignRevision 2026](https://designrevision.com/blog/saas-stripe-integration) | Stripe = source of truth; webhooks sync DB; idempotent handlers | **Adopt** |
| [BILLING.md](internal-docs/starter-pack/docs/backend/BILLING.md) | Bill **workspace** not user; `require_plan_feature()` in API | **Adopt** |
| Laravel Cashier pattern ([hafiz.dev](https://hafiz.dev/blog/stripe-integration-in-laravel-complete-guide-to-subscriptions-one-time-payments)) | `Billable` on Team/Workspace model, not User | **Adopt** concept |

### Platform admin (W5 scope)

| Source | Takeaway | Resolution |
|--------|----------|------------|
| [Yaro Labs admin](https://yaro-labs.com/blog/saas-admin-panel) | Workspace lookup + audit = high value | **W5** |
| [vcodewonders RBAC](https://vcodewonders.com/handling-multitenancy-in-saas-roles-permissions-rbac-tenant-isolation/) | Super Admin ≠ Tenant Admin | **Adopt** |
| User decision | KC Admin for user identity; in-app user panel later | **W5** workspace/audit; **future program** user directory |

---

## Data scope & exclusions

**In scope (W0–W7):** catalog sections not in deferred program.

**Explicitly out of scope (this program):**

- Revy review pipeline.
- Keycloak realm automation; KC Organizations sync.
- Per-seat / usage / enterprise `billing_accounts` Stripe splits.
- Mobile-native apps.
- **Deferred program** items (API keys, notifications, file handling, in-app user panel).

**Fast-start:** new projects copy starter-pack + shipped SaaS base; strip `features/installations`, Revy env keys, product nav entries — document strip list after W0 (not required for Revy repo now).

---

## Edge cases

1. **Last workspace admin** — cannot leave or delete self without promoting another admin ([ACCOUNT_LIFECYCLE.md](internal-docs/starter-pack/docs/backend/ACCOUNT_LIFECYCLE.md)).
2. **Multi-workspace users** — switcher must set `X-Workspace-Id`; settings pages must show which scope is active.
3. **Billing owner vs workspace admin** — who can change plan? Starter-pack: workspace `admin`; consider `owner` flag later.
4. **Solo workspace on user delete** — cascade workspace archive per lifecycle spec.
5. **Platform admin cross-tenant reads** — audit-log all workspace directory/detail access (W5).
6. **Mode B registration** — platform admin queue is prerequisite before tenant admin can invite.
7. **Keycloak as source of truth** — profile email may differ from `users.email` until sync on `/me`.
8. **Stripe customer without workspace** — webhook handler must tolerate orphan events.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | Program location | **locked** | `docs/saas-base/` |
| Q2 | Settings route shape | **locked** | Nested `/settings/*` + left sidebar + scope labels |
| Q3 | Platform admin scope | **locked** | W5: workspace dir, KPIs, audit search, settings; KC for users; future program for user panel |
| Q4 | Billing | **locked** | W4 — Stripe standard |
| Q5 | Security UI | **locked** | Keycloak account console link |
| Q6 | Dashboard widgets | **locked** | Registry + audit-lite + product slots |
| Q7 | Revy vertical | **locked** | Keep — additive only |
| Q8 | Items demo | **locked** | Keep |
| Q9 | Audit table | **locked** | W2→W3→W5→W6 |
| Q10 | Internal staff RBAC | **locked** | Single `super_admin` |
| Q11 | KC Organizations | **locked** | No |
| Q12 | Workspace directory | **locked** | W5 |
| Q13 | Appearance | **locked** | W1 — THEME.md localStorage |
| Q14 | Permissions matrix | **locked** | W2 |
| Q15 | Integrations | **locked** | W2 — link to `/installations` |
| Q16 | Dashboard activity | **locked** | W3 |
| Q17 | Notifications | **locked** | Deferred program |
| Q18 | Impersonation | **locked** | W7 server-side |
| Q19 | Platform user UI | **locked** | Deferred program |
| Q20 | Stripe | **locked** | Standard |
| Q21 | API keys | **locked** | Deferred program |
| Q22 | File handling | **locked** | Deferred program |
| Q23 | W0 nav | **locked** | No links until shipped |
| Q24 | Registry | **locked** | Single module |
| Q25 | W5 sizing | **locked** | W5.1 / W5.2 |
| Q26 | Items demo | **locked** | Keep / fast-start strip |
| Q27 | Integrations nav | **locked** | Both; settings links |

---

## Parking lot

- Execution peer-review on [waves/SAAS_BASE_W8_EXECUTION.md](./waves/SAAS_BASE_W8_EXECUTION.md) before LOOP.
- Mirror [SETTINGS_IA.md](./SETTINGS_IA.md) → `internal-docs/starter-pack/docs/frontend/patterns/SETTINGS_IA.md` in W8.6.
- Fast-start strip list → [FAST_START_STRIP_LIST.md](./FAST_START_STRIP_LIST.md) (W8.6).
- Remove duplicate `waves/w0`…`w7/` execution copies (W8.6).

### Post-W7 gap closure (W8 scope)

| Gap | W8 subphase |
|-----|-------------|
| Billing API called for non-admins on dashboard | W8.1 |
| Settings sidebar shows admin routes to all | W8.1 |
| Suspended workspaces in switcher; no tenant status page | W8.1 |
| `POST leave` allowed while impersonating | W8.2 |
| Missing impersonation / workspace_suspended i18n | W8.2 |
| KPI total includes deleted workspaces | W8.3 |
| Expired invitations in pending list | W8.3 |
| Checklist member count first-page only | W8.3 |
| Orphan Stripe webhook retry storm vs findings | W8.4 |
| Export worker / deploy env not documented | W8.5 |
| Human gates W4–W7 never run | W8.5 |
| Findings + runbooks stale vs shipped code | W8.6 |

---

## Devil's advocate — resolutions (2026-07-25)

| Issue | Resolution |
|-------|------------|
| W0 stub pages | Nav links only when wave ships ([SETTINGS_IA.md](./SETTINGS_IA.md)) |
| API keys in W1 | Moved to deferred program |
| Impersonation underspecified | W7: server `impersonated_user_id` on `CurrentUser`; KC session unchanged |
| Audit schema | Locked columns above; W2 migration |
| W5 too large | Execution split W5.1 / W5.2 |
| Settings >7 items | Two sidebar groups |
| Checklist lies | Step registry with `available` per shipped wave |
| Duplicate registries | Single `platform/extensions` registry |
| Clone vs additive | **Fast-start** framing; strip list later |
| Notifications in W6 | Deferred entirely |
| SETTINGS_IA gitignored only | Committed [SETTINGS_IA.md](./SETTINGS_IA.md) |
| Items demo clutter | Keep in Revy; document in fast-start strip list |
| No peer review | Required before each wave execution (per README) |

**Stripe W4 deploy note:** webhook route needs raw body for signature; document in W4 execution — Stripe CLI for dev, public URL + `STRIPE_WEBHOOK_SECRET` in deploy env examples; idempotency via existing `core/idempotency.py` on Checkout create only if needed — webhooks use Stripe event id dedupe table or idempotency keys.

---

## Experiment / verification

| Check | Pass criteria |
|-------|----------------|
| Settings IA | User can reach profile + team without seeing product routes |
| Workspace switcher | Multi-member user switches workspace; API calls use correct header |
| Team admin | Admin invites, lists pending, revokes; non-admin gets 403 |
| Billing | Checkout → webhook → `workspaces.plan` updated; API gate rejects over-quota |
| Platform W5 | Workspace search, suspend, audit search, KPIs |
| Impersonation W7 | Banner + audit reason + TTL |
| Stripe e2e | Checkout → webhook → plan updated; portal changes sync back |
| i18n | All new strings EN + LV |
| Tests | Unit tests for new services; no new `tests/api/` |

---

## References

| Path | Role |
|------|------|
| `docs/starter-pack/README.md` | Completed scaffold program (P0–P5) |
| `docs/starter-pack/SCAFFOLD_FINDINGS.md` | Platform foundation baseline |
| `internal-docs/starter-pack/docs/CROSS_CUTTING.md` | Defined vs partial concerns |
| `internal-docs/starter-pack/docs/backend/BILLING.md` | Stripe + plan gating spec |
| `internal-docs/starter-pack/docs/backend/ACCOUNT_LIFECYCLE.md` | Export / delete / retention |
| `internal-docs/starter-pack/docs/backend/AUDIT.md` | Audit log sketch |
| `internal-docs/starter-pack/docs/backend/TENANCY.md` | Workspace isolation |
| `internal-docs/starter-pack/docs/backend/AUTHZ_MODEL.md` | KC vs PG role split |
| [Stripe SaaS integration](https://docs.stripe.com/saas) | Billing baseline |
| [Keycloak Organizations guide](https://keycloakpro.com/blog/keycloak-multi-tenancy-organizations-guide) | Rejected (Q11) |
| `docs/saas-base/README.md` | Wave index |
| `docs/saas-base/SETTINGS_IA.md` | Committed IA + registry |
| `frontend/src/lib/routerInstance.tsx` | Current routes |
| `frontend/src/components/layout/AppShellLayout.tsx` | Tenant shell nav |
| `frontend/src/features/dashboard/pages/DashboardPage.tsx` | Dashboard stub |
| `frontend/src/features/settings/pages/SettingsPage.tsx` | Settings stub |
| `frontend/src/features/admin/pages/AdminUsersPage.tsx` | Platform signup queue |
