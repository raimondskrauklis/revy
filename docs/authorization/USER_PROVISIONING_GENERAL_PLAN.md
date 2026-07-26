# User provisioning — general plan

From [USER_PROVISIONING_FINDINGS.md](./USER_PROVISIONING_FINDINGS.md). **No file lists or steps** — use `create-execution-plan` per phase.

**Cross-cutting:** unit tests (`backend/tests/unit/`); hand-written Alembic if new tables; structured logging; EN+LV only for new user-facing strings; API enforcement before UI.

---

## Locked decisions

| # | Decision |
|---|----------|
| D1 | **Webhook primary + JIT fallback** — same idempotent `provision_user()`; not webhook-only |
| D2 | **Signup through SPA** — `/login` → Keycloak → `/auth/callback`; no naked KC registration URL as product path |
| D3 | **Keycloak = identity, PostgreSQL = lifecycle + RBAC** — sync on identity events; bootstrap seed is the only PG-first exception |
| D4 | **Hook identity lifecycle, not LOGIN** — `REGISTER`, federated first-login, email update, disable/delete |
| D5 | **Email = canonical username** — unique in KC realm + PG (`uq_users_email`); store lowercase; `sub` is primary key after bind |
| D6 | **Bootstrap env is temporary** — seed → first login → remove; startup guard if env set without seed row |
| D7 | **In-app KC admin deferred** — password/MFA/session ops stay in KC Admin Console; hooks prepare future app user directory |
| D8 | **Prod webhook internal-only** — KC → `http://<api-service>:8000/...` on `revy-net`; **not** exposed via nginx/public URL |
| D9 | **Idempotency key** — prefer listener `eventId` / `id` from payload; fallback `sha256(event_type + userId + time)` — never process same key twice |
| D10 | **Email update** — webhook/JIT may update email on existing `sub`; if new email taken by another row → `identity_email_conflict`, no overwrite |
| D11 | **`ENVIRONMENT=test`** — skip bootstrap startup guard (pytest must not require seed row) |
| D12 | **vymalo `0.10.0-rc.1`** — accepted for KC 26; pin JAR URLs + sha256 in Dockerfile; re-verify on KC minor upgrade |

---

## Program invariants (devil's advocate — locked)

| Risk | Mitigation |
|------|------------|
| Webhook arrives before SPA login | Intended — PG row exists early; JIT is idempotent no-op |
| Webhook fails / API down at signup | JIT on first `/me` (D1) |
| KC Admin manual user | No webhook until KC fires event; **JIT on first login** still provisions — document in runbook, not a product signup path |
| Bootstrap email + REGISTER webhook races seed | Webhook **skip insert** when email matches seeded `pending_activation` super_admin (same as JIT) |
| Google REGISTER without `email_verified` in payload | Treat as verified when event is federated REGISTER / broker first-login (KC Trust email) |
| JWT still valid after KC disable | Accept short TTL; **no** KC session revoke in this program — document; future admin hooks |
| Invite email ≠ Google email | Invitation accept requires **provisioned user email match** — existing invitation validation; out of scope to auto-link |
| vymalo RC dependency | D12 pin + human gate on P2 smoke before prod KC rebuild |
| Idempotency table growth | Store payloads; **no TTL in v1** — acceptable volume; revisit if metrics show bloat |

---

## P0 — Unified provision service

**Goal:** One idempotent provisioning function used by auth middleware and (later) webhook.

**Scope:** In — extract `provision_user_from_keycloak()` from `ensure_user_from_token` + `maybe_auto_provision_user` + bootstrap activation; fix Mode A status path (no misleading `pending_profile` hop); normalize email on write; explicit errors (`provision_email_required`, `identity_email_conflict`); refactor `get_current_user` to call it; unit tests. Out — webhook route, KC listener, migrations unless idempotency needs a table later.

**Deliverables:** Single service module; JIT path unchanged in behaviour but clearer; tests for Mode A/B, bootstrap link, email conflict, missing email.

**Depends on:** Findings baseline.

---

## P1 — Keycloak webhook API

**Goal:** PG user row exists when Keycloak creates or updates identity — before first SPA `/me`.

**Scope:** In — `POST /api/v1/webhooks/keycloak`; verify **`X-Webhook-Secret`** (constant-time); dispatch `REGISTER`, federated first-login, `UPDATE_EMAIL`, disable/delete; call `provision_user_from_keycloak()`; delivery idempotency (D9); skip bootstrap email when seeded row exists; `KEYCLOAK_WEBHOOK_SECRET` in config + `.env.example`; prod endpoint **internal `revy-net` only** (D8). Out — KC container changes (P2); public nginx route for webhook.

**Deliverables:** Webhook handler + service; idempotency table + migration; unit tests for event types and dedupe.

**Depends on:** P0.

---

## P2 — Keycloak event listener (deploy)

**Goal:** Keycloak emits HTTP events to Revy API in dev and production.

**Scope:** In — HTTP Event Listener (vymalo, D12); filter identity events only (D4); **prod URL** `http://revy-api:8000/api/v1/webhooks/keycloak` on `revy-net` (D8); dev `host.docker.internal`; update `deploy/keycloak/config/README.md`. Out — custom Java SPI; SCIM; nginx exposure of webhook path.

**Deliverables:** Documented KC deploy steps; events reaching P1 endpoint in dev; production checklist entry.

**Depends on:** P1.

---

## P3 — Bootstrap & email hardening

**Goal:** Fail fast on misconfigured bootstrap; enforce email identity rules end-to-end.

**Scope:** In — startup guard (D6, D11); cross-`sub` email conflict tests; invitation ↔ provision doc. Out — in-app admin UI.

**Deliverables:** Startup validation; conflict handling tests; operator note in `DEV_BOOTSTRAP.md`.

**Depends on:** P0.

---

## P4 — Docs & operator smoke

**Goal:** Docs match shipped behaviour; operators can verify KC ↔ PG sync.

**Scope:** In — docs closeout; tiered smoke (curl internal webhook + P2 Google path); FE toasts for `provision_email_required` and `identity_email_conflict`; KC realm checklist (email as username, Trust email). Out — full in-app user admin.

**Deliverables:** Committed runbooks; smoke matrix: Google signup → PG row via webhook → SPA login → `active`.

**Depends on:** P0, P1, P2, P3 — full e2e smoke requires P2 listener.

---

## Out of scope

- Keycloak Organizations; SCIM; in-app password/MFA admin
- PG → Keycloak role sync (model C hybrid)
- Manual “add user” in KC Admin without defined onboarding path

---

## Next step

Run **`phase-execution`** from [`waves/USER_PROVISIONING_P0_EXECUTION.md`](./waves/USER_PROVISIONING_P0_EXECUTION.md).
