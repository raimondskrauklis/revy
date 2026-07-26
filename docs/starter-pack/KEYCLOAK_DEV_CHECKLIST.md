# Keycloak dev checklist (Revy)

Configure realm and clients so browser tokens pass `app.core.auth` validation.

**Env canon:** `backend/.env.example`, `frontend/.env.example`  
**Audience logic:** `backend/app/core/auth.py` — allowlist `revy-api` + `revy-web`

---

## Realm

| Setting | Value |
|---------|--------|
| Realm name | `revy` |
| Login with email | On |
| Email as username | Recommended |
| Verify email | On (dev users: complete verification or relax required action) |

Backend: `KEYCLOAK_REALM=revy`  
Production API (docker): `KEYCLOAK_URL=http://keycloak:8080` **and** `KEYCLOAK_ISSUER=https://auth.revy.createit.digital/realms/revy` (JWT `iss` from browser login uses the public host).  
Frontend: `VITE_KEYCLOAK_REALM=revy`

---

## Client: `revy-api` (confidential)

| Setting | Value |
|---------|--------|
| Client ID | `revy-api` |
| Client authentication | On |
| Standard flow | Off (API client — tokens via service/user flows as needed) |
| Direct access grants | Off (prefer browser via `revy-web`) |

**Backend env:**

```text
KEYCLOAK_CLIENT_ID=revy-api
KEYCLOAK_CLIENT_SECRET=<from Keycloak credentials tab>
```

Service account / mapper: ensure access tokens intended for the API include audience or azp the backend accepts (see below).

---

## Client: `revy-web` (public SPA)

| Setting | Value |
|---------|--------|
| Client ID | `revy-web` |
| Client authentication | Off (public) |
| Standard flow | On |
| Valid redirect URIs | `http://localhost:5173/*`, `http://127.0.0.1:5173/*`, `https://revy.createit.digital/*` |
| Web origins | `http://localhost:5173`, `http://127.0.0.1:5173`, `https://revy.createit.digital` |

**Frontend env:**

```text
VITE_KEYCLOAK_CLIENT_ID=revy-web
VITE_KEYCLOAK_URL=http://localhost:8080
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Production (`createit.digital`):**

```text
VITE_KEYCLOAK_URL=https://auth.revy.createit.digital
VITE_API_BASE_URL=https://revy.createit.digital/api/v1
```

Keycloak is on a **dedicated subdomain** (`auth.revy.createit.digital`), not a path on the app host (`/auth`). Nginx configs: `internal-docs/starter-pack/deploy/nginx/` (see `auth.revy.createit.digital.conf`). TLS: DNS-01 — `docs/utils/CERTBOT_DIGITALOCEAN_DNS_RENEWAL.md`.

Adjust URLs if Keycloak runs behind a different host or path prefix (local dev only).

---

## JWT audience / azp (critical)

The API allowlist is `revy-api` + `revy-web` (`auth.py`).

**Required:** `azp` must be `revy-web` (browser) or `revy-api`.

**`aud` handling:**

- If `aud` is **omitted**, validation passes when `azp` is allowed.
- If `aud` is a **string**, it must be `revy-api` or `revy-web` — `aud: account` alone returns `Invalid token audience`.
- If `aud` is a **list**, at least one entry must be in the allowlist.

Browser tokens often include `aud: account`. Configure Keycloak so the access token either omits `aud`, includes `revy-api` / `revy-web` in `aud`, or use a mapper that adds the API client to audience — see `internal-docs/starter-pack/deploy/docs/keycloak.md`.

**Verify after login** (decode access token at [jwt.io](https://jwt.io) or API logs):

- `iss` ends with `/realms/revy`
- `azp` is `revy-web`
- `email` / `sub` present

Failure symptom: `401` / `Invalid token audience` on `/api/v1/me`.

**Fix:** Keycloak client scopes / audience mappers — align with `internal-docs/starter-pack/deploy/docs/keycloak.md`.

---

## Optional: bootstrap super admin

If using `BOOTSTRAP_SUPER_ADMIN_EMAIL`, register that exact email in Keycloak before first API login. See [DEV_BOOTSTRAP.md](./DEV_BOOTSTRAP.md) §5.

---

## Google IdP (optional)

| Setting | Value |
|---------|--------|
| Trust email | On |
| Case-sensitive username | Off |
| Default scopes | `openid email profile` |
| Realm: Login with email | On |
| Realm: Email as username | On (recommended) |

Backend webhook + JIT require `email` on the KC user. Federated first-login events provision with `email_verified=true` when Trust email is on.

Set `KEYCLOAK_WEBHOOK_SECRET` in backend `.env` and match `WEBHOOK_HTTP_AUTH_PASSWORD` in KC `.env` (see `deploy/keycloak/config/.env.example`).

---

## Smoke (tiered)

| Tier | Steps | Pass criteria |
|------|-------|---------------|
| **A — webhook only** | `curl -X POST http://localhost:8000/api/v1/webhooks/keycloak -H 'X-Webhook-Secret: $SECRET' -H 'Content-Type: application/json' -d '{"id":"smoke-1","type":"REGISTER","userId":"kc-smoke","details":{"email":"smoke@example.com","email_verified":"true"}}'` | `200`; row in `keycloak_webhook_deliveries`; row in `users` |
| **B — Google + KC listener** | P2 KC rebuild → Google signup → SPA login | Tier A rows **before** SPA `/me`; `GET /api/v1/me` → `status: active` (Mode A) |

**Baseline (no webhook):** Login at `http://localhost:5173` → JIT `/me` still provisions (fallback). No repeated 401 on API calls.

See also [DEV_BOOTSTRAP.md](./DEV_BOOTSTRAP.md) and [docs/authorization/README.md](../authorization/README.md).
