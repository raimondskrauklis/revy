# User provisioning — findings

Baseline for fixing **Keycloak user exists, PostgreSQL `users` row missing**. No execution steps.

**Status:** shipped (2026-07-26)

**Shipped summary:** Unified `provision_user_from_keycloak()` (JIT + webhook); `POST /api/v1/webhooks/keycloak` with idempotency; vymalo listener in KC image; bootstrap startup guard; FE provision error toasts.

**Related:** [README.md](./README.md) · [REGISTRATION_FLAGS.md](../starter-pack/REGISTRATION_FLAGS.md) · `internal-docs/starter-pack/docs/backend/USER_REGISTRATION.md` · `AUTHZ_MODEL.md` · `BOOTSTRAP_SUPER_ADMIN.md` · `TENANCY.md`

---

## Problem statement

Operator signs up via Keycloak (email/password or Google IdP). User appears in Keycloak Admin Console. **No row in PostgreSQL `users`.**

This is reported as a bug but matches current implementation when the **app API is never successfully called with a valid JWT** — or when provisioning preconditions fail silently (401 before insert).

---

## Revy decision vs old KP pattern

| Topic | Old KP-style mental model | Revy (starter-pack + shipped code) |
|-------|---------------------------|-------------------------------------|
| Tenant | Organisation / institution created at bootstrap | **`workspaces`** — no `organizations` table |
| Platform operator | Org + admin user at setup | **`users.platform_role = super_admin`**, **no workspace membership** |
| End-user tenant | Entity created after login + form | **Personal workspace** on activation (Mode A auto or Mode B approve) |
| Identity source | Keycloak (+ optional early webhook) | Keycloak for **auth only**; PostgreSQL for **lifecycle + RBAC** |
| When PG user appears | Webhook or stepped onboarding | **First authenticated API request** (`get_current_user`) |

Revy explicitly rejected copying KP `users.organization_id` / institution model — see `AUTHZ_MODEL.md` anti-patterns and `SAAS_BASE_FINDINGS.md` § Keycloak Organizations.

---

## What docs say

### Starter-pack (`internal-docs/starter-pack/docs/backend/`)

| Doc | Claim |
|-----|--------|
| `USER_REGISTRATION.md` | Mode A: open signup → workspace + `active` after email verified. Mode B: profile form → `pending_approval` → admin approve. |
| `USER_REGISTRATION.md` | Step 4: **"Webhook or first GET /api/v1/me"** creates `users` row |
| `BOOTSTRAP_SUPER_ADMIN.md` | DB seed first → register same email in KC → first login binds `sub` → remove env var |
| `AUTHZ_MODEL.md` | Checklist: **"Keycloak webhook or first-login creates user row"** |
| `TENANCY.md` | Provisioning table: bootstrap = no workspace; open signup = workspace on verify; closed = workspace on approve |

### Committed Revy docs

| Doc | Claim |
|-----|--------|
| `REGISTRATION_FLAGS.md` | Mode A/B env pairing; auto-provision on first JWT |
| `DEV_BOOTSTRAP.md` | Optional bootstrap super admin; smoke = login → `GET /me` → `status: active` |
| `SAAS_BASE_FINDINGS.md` | Mode A + Mode B + `complete-profile` + admin approve APIs **shipped** (W0–W8) |
| `SCAFFOLD_FINDINGS.md` | **Stale** on registration — written pre-P2; lists complete-profile / admin APIs as missing |

---

## What code actually does

### Single provisioning entry point

PostgreSQL users are created **only** inside `get_current_user` (JWT auth dependency):

```text
Bearer JWT
  → decode_access_token (iss, aud/azp, signature)
  → ensure_user_from_token(sub, email, email_verified)   # INSERT users if missing
  → maybe_auto_provision_user(...)                        # workspace + active (Mode A)
  → activate_bootstrap_super_admin(...)                   # bootstrap path only
  → session.commit()
```

**Files:** `backend/app/core/auth.py`, `backend/app/services/users.py` (`ensure_user_from_token`), `backend/app/services/onboarding.py` (`maybe_auto_provision_user`, `activate_user_with_workspace`).

### No Keycloak webhook

| Mechanism | In docs? | In repo? |
|-----------|----------|----------|
| Keycloak `user-registered` / event listener | Yes (`USER_REGISTRATION.md`, `BOOTSTRAP_SUPER_ADMIN.md`) | **No** — no route, no handler, no `KEYCLOAK_WEBHOOK_SECRET` usage |
| JIT on first API call | Yes | **Yes** — canonical path |
| Seed script (`seed_bootstrap_super_admin.py`) | Yes | **Yes** — bootstrap only |
| Invitation accept | N/A | Requires **existing** `UserORM` (`active`); does not create users |

**Implication:** Keycloak signup alone never touches PostgreSQL. User must complete SPA login and hit a protected endpoint (typically `GET /api/v1/me`).

### `ensure_user_from_token` rules

| Condition | Result |
|-----------|--------|
| Row exists for `keycloak_user_id` (`sub`) | Return existing; maybe update email / clear `pending_email_verification` |
| Email matches `BOOTSTRAP_SUPER_ADMIN_EMAIL` and seeded row exists | Return seeded row (placeholder `keycloak_user_id`) |
| **`email` missing from JWT** | **`return None` → 401 "User not provisioned"** — no INSERT |
| Email present | INSERT `users` with `resolve_initial_user_status(email_verified)` |

### Status after insert (before auto-provision)

`resolve_initial_user_status` (`onboarding.py`):

| `email_verified` | `REGISTRATION_REQUIRE_PROFILE_FORM` | `REGISTRATION_REQUIRE_ADMIN_APPROVAL` | Initial status |
|------------------|-------------------------------------|---------------------------------------|----------------|
| false | * | * | `pending_email_verification` |
| true | true | * | `pending_profile` |
| true | false | true | `pending_approval` |
| true | false | false | **`pending_profile`** (not `active`) |

Mode A then runs `maybe_auto_provision_user` on the **same request** if both registration flags are false and `email_verified` is true → workspace + `status=active`.

**Edge case (documented):** Mode A can briefly expose `pending_profile` in `/me` response on the same request that activates — `REGISTRATION_FLAGS.md` § Warnings.

### Bootstrap super admin (optional, separate path)

```text
1. BOOTSTRAP_SUPER_ADMIN_EMAIL in backend/.env
2. seed (before API start):
      local:  pipenv run python -m scripts.seed_bootstrap_super_admin
      droplet: docker run --rm --network revy-net --env-file /mnt/revy_volume/backend/.env \
               registry.digitalocean.com/revy-container-registry/revy-api:latest \
               python -m scripts.seed_bootstrap_super_admin
      → INSERT users (super_admin, pending_activation, placeholder keycloak_user_id)
3. Login in SPA with same email (KC or Google) — / or landing → /login
4. First GET /me → activate_bootstrap_super_admin binds sub, status=active
5. Remove BOOTSTRAP_SUPER_ADMIN_EMAIL from .env
```

**Not required** for normal signup. **Required** only for first platform `super_admin` before any admin UI.

Bootstrap seed **not run** + bootstrap email set → normal signup still works but creates a **regular** user (not `super_admin`) on first `/me`.

### Frontend trigger chain

```text
/ → LandingPage (public; authenticated → /dashboard)
/login → keycloak.login()
/auth/callback → refetchUser() → GET /api/v1/me
ProtectedRoute → gates on user.status (verify-email, complete-profile, pending-approval)
```

**Files:** `frontend/src/contexts/AuthContext.tsx`, `frontend/src/features/auth/pages/AuthCallbackPage.tsx`, `frontend/src/components/auth/ProtectedRoute.tsx`.

If `/me` fails (401), `user` stays `null` — no Postgres row.

---

## Verified local state (2026-07-26)

- `revy-dev` database: **`users` count = 0**
- `backend/.env`: `BOOTSTRAP_SUPER_ADMIN_EMAIL` set; **seed script not executed**
- Symptom consistent with: KC user created, **app login `/me` never succeeded**

---

## Failure modes (ranked by likelihood)

| # | Cause | Symptom |
|---|--------|---------|
| 1 | Signup only in Keycloak / Google — never returned to SPA or API down | KC user yes, PG no |
| 2 | **`email` absent from access token** (common Google IdP mapper gap) | 401 `User not provisioned` |
| 3 | JWT rejected before provision (`Invalid token audience`, `iss` mismatch prod vs local) | 401, no INSERT |
| 4 | `email_verified: false` | Row may exist as `pending_email_verification`; operator may not notice |
| 5 | Mode B flags on without completing profile / approval | Row exists, not `active`, no workspace |
| 6 | Wrong database (staging KC + dev PG) | KC user yes, PG empty on DB you query |

---

## Google IdP specifics

| Keycloak Google IdP | Why |
|---------------------|-----|
| **Trust email = On** | Sets `email_verified` for Mode A auto-provision |
| Client `revy-web` scopes include `email` | `ensure_user_from_token` requires `email` claim |
| Redirect URI on Google OAuth client | `…/realms/revy/broker/google/endpoint` |

Decode access token after login: must have `sub`, `email`, `azp: revy-web`.

---

## Industry patterns (for general plan discussion)

| Pattern | Pros | Cons | Revy today |
|---------|------|------|------------|
| **A. JIT on first API call** | Simple; no KC extension; DB stays source of truth | No PG row until app contacted; debugging confuses operators | **Current** |
| **B. Keycloak Event Listener → HTTP webhook** | PG row on KC registration; audit trail | Infra + secret rotation; must handle retries/idempotency | Documented, **not built** |
| **C. Keycloak SPI (custom provider)** | Same as B, in-process | Ops burden, KC upgrade coupling | Not considered |
| **D. SCIM / enterprise HR sync** | B2B provisioning | Overkill for PLG SaaS | Out of scope |
| **E. KC Organizations (26+)** | IdP-level grouping | Revy **rejected** — app `workspaces` is tenant boundary | Out of scope |

Starter-pack recommendation remains **A** for greenfield PLG; **B** optional if operators need KC-console parity with PG before first app login.

---

## Gaps & doc drift

| Gap | Severity | Notes |
|-----|----------|-------|
| Docs promise webhook **or** first-login; only first-login exists | **High** — operator expectation | Update `USER_REGISTRATION.md` or implement webhook |
| `SCAFFOLD_FINDINGS.md` registration row outdated | Low | Says complete-profile / admin APIs missing — shipped in W0 |
| No unit tests for `ensure_user_from_token` | Medium | Only mocked in auth impersonation tests |
| `resolve_initial_user_status` returns `pending_profile` when Mode A flags off | Low | Works via same-request auto-provision; confusing for debugging |
| No structured log when provision skipped (`email` missing) | Medium | Today → generic 401 |
| Invitation flow assumes user already provisioned | Low | Invite email must login first |

---

## Decisions (locked 2026-07-26)

| Q# | Resolution |
|----|------------|
| Q1 | Webhook primary + JIT idempotent fallback — see [USER_PROVISIONING_GENERAL_PLAN.md](./USER_PROVISIONING_GENERAL_PLAN.md) D1 |
| Q2 | SPA signup path only (`/login` → `/auth/callback`) — D2 |
| Q3 | KC identity source; PG sync on identity events; bootstrap seed exception — D3, D4 |
| Q4 | Unified `provision_user_from_keycloak()`; fix Mode A status path — P0 |
| Q5 | Startup guard when bootstrap env set without seed row — P3 |
| Q6 | Email unique KC + PG; lowercase store; `provision_email_required` / `identity_email_conflict` — D5, P0 |

---

## Devil's advocate pass (2026-07-26)

Reviewed against general plan + execution waves. **Gaps closed in plan** (see [USER_PROVISIONING_GENERAL_PLAN.md](./USER_PROVISIONING_GENERAL_PLAN.md) § Program invariants, D8–D12):

| Was missing | Now locked |
|-------------|------------|
| Prod webhook on public URL | Internal `revy-net` only (D8) |
| Idempotency key if payload has no id | D9 fallback hash |
| Email change overwriting another user | D10 conflict |
| pytest vs bootstrap guard | D11 skip when `ENVIRONMENT=test` |
| vymalo RC risk | D12 pin + sha256 |
| KC disable + valid JWT | Documented accept; no session revoke in program |
| FE only one error code | P4 both provision + conflict toasts |
| HMAC vs shared secret drift | General plan aligned to `X-Webhook-Secret` |

**Residual (accepted):** idempotency table no TTL; no Celery retry queue; invite email ≠ Google email not auto-linked; KC session revoke deferred.

---

## Smoke checklist (current intended flow)

**Normal user (Mode A):**

1. `REGISTRATION_REQUIRE_*=false` (backend + frontend)
2. Login via SPA → `/auth/callback`
3. `GET /api/v1/me` → 200, `status: active`, `memberships.length >= 1`
4. `SELECT * FROM users WHERE email = …` → one row

**Platform super_admin:**

1. Set `BOOTSTRAP_SUPER_ADMIN_EMAIL`
2. Run `seed_bootstrap_super_admin`
3. Login same email via SPA
4. `/me` → `platform_role: super_admin`, `memberships: []`
5. Remove bootstrap env var

---

## File map (implementation)

| File | Role |
|------|------|
| `backend/app/core/auth.py` | JWT + provision orchestration |
| `backend/app/services/users.py` | `ensure_user_from_token`, bootstrap activation |
| `backend/app/services/onboarding.py` | Status resolution, workspace provision |
| `backend/app/api/v1/me.py` | Primary post-login endpoint |
| `backend/app/api/v1/users.py` | `POST /users/complete-profile` (Mode B) |
| `backend/app/api/v1/admin/users.py` | Approve/reject pending (Mode B) |
| `backend/scripts/seed_bootstrap_super_admin.py` | Bootstrap seed |
| `frontend/src/contexts/AuthContext.tsx` | KC init + `/me` fetch |
