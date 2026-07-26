# docs/authorization/waves/USER_PROVISIONING_P1_EXECUTION.md

# P1 — Keycloak webhook API (execution)

Phase **P1** of [`USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md). Baseline: findings § No Keycloak webhook. **P1 only.**

**Goal:** `POST /api/v1/webhooks/keycloak` creates/updates PG users on KC identity events before first SPA `/me`.

## Decisions locked for P1

- **Listener (pinned — P2 deploys same artifact):** [vymalo/keycloak-webhook](https://github.com/vymalo/keycloak-webhook) HTTP provider **`0.10.0-rc.1`** (KC 26 per upstream matrix). JARs: `keycloak-webhook-provider-core` + `keycloak-webhook-provider-http` (shaded `-all.jar` from releases).
- **Auth contract:** shared secret via request header **`X-Webhook-Secret`** (constant-time compare) — matches vymalo HTTP provider env `WEBHOOK_HTTP_BASE_PATH` + secret config; document exact env keys in `keycloak_webhook.py` module docstring after reading release README in P1.1.
- Secret: `KEYCLOAK_WEBHOOK_SECRET` — required when webhooks enabled; verify incoming `X-Webhook-Secret` header (not HMAC body unless spike proves vymalo sends signature instead — then lock one method only).
- Idempotency (D9): `delivery_id` = payload `id` / `eventId` if present; else `sha256(f"{event_type}:{user_id}:{time}")` hex; PK in `keycloak_webhook_deliveries`.
- Hand-written Alembic migration only — **LOOP pauses after P1.2** for migration apply.
- Events handled: `REGISTER`, federated/broker first-login, profile/email update, user disable/delete (D4). **Do not** provision on `LOGIN`.
- Federated REGISTER: treat `email_verified=True` when event type is broker/federated register (KC Trust email).
- Handler calls `provision_user_from_keycloak()` from P0; email update uses D10; disable/delete → `suspended` or `deleted`.
- Bootstrap: webhook **skip new insert** when email matches seeded `pending_activation` super_admin (link on first JIT login).
- Return 2xx quickly; no Celery in P1.
- Unit tests only.

## Out of scope for P1 (later phases)

- KC container listener JAR/config → **P2**
- Startup bootstrap guard → **P3**
- Operator doc smoke → **P4**

---

## P1.1 — Listener contract spike + config + delivery model

**What:** Read vymalo `0.10.0-rc.1` HTTP provider README; lock payload shape + `X-Webhook-Secret` verification in `backend/app/integrations/keycloak_webhook.py` module docstring. Add `Settings.keycloak_webhook_secret`; `keycloak_webhooks_enabled` property (mirror `github_webhooks_enabled`); ORM `KeycloakWebhookDeliveryORM`; register in `models/__init__.py`. Uncomment/set `KEYCLOAK_WEBHOOK_SECRET` in `.env.example`.

**Files:** `backend/app/integrations/keycloak_webhook.py` (docstring only in spike), `backend/app/core/config.py`, `backend/app/models/keycloak_webhook_delivery.py` (new), `backend/app/models/__init__.py`, `backend/.env.example`, `deploy/env-examples/backend.env.production.example`

**Deliverable:** Module docstring lists pinned listener version, header name, and sample REGISTER payload fields used by P1.4.

---

## P1.2 — Migration `keycloak_webhook_deliveries`

**What:** Hand-written Alembic revision — table with `delivery_id` PK, `event_type`, `payload_json` JSONB, `received_at`. Chain after latest head.

**Files:** `backend/alembic/versions/2026_07_26_*_keycloak_webhook_deliveries.py` (new)

**Deliverable:** `cd backend && pipenv run alembic upgrade head` — applies cleanly on dev DB.

**LOOP pause:** apply migration before P1.3.

---

## P1.3 — Verify + idempotency service

**What:** `verify_keycloak_webhook_secret(header, secret)` — constant-time compare of `X-Webhook-Secret`; `accept_keycloak_webhook(session, delivery_id, event_type, payload)` — dedupe insert, return `accepted: bool`.

**Files:** `backend/app/integrations/keycloak_webhook.py` (new), `backend/app/services/keycloak_webhooks.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_keycloak_webhook_verify.py -q` — green (create in this subphase).

---

## P1.4 — Event dispatch + provision wiring

**What:** `apply_keycloak_webhook_event(session, event_type, payload)` — map event → provision or status update; parse `sub`, `email`, `email_verified`, `enabled`; compute `delivery_id` per D9; bootstrap skip per locked decisions.

**Files:** `backend/app/services/keycloak_webhooks.py`, `backend/app/services/keycloak_provisioning.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_keycloak_webhooks.py -q` — green (REGISTER, duplicate delivery, UPDATE email success + conflict, disable user, bootstrap skip).

---

## P1.5 — Router

**What:** `POST /api/v1/webhooks/keycloak` — raw body, `X-Webhook-Secret` verify, accept + dispatch, commit; **`router.include_router(keycloak.router)`** in `webhooks/__init__.py` (required — route does not mount otherwise).

**Files:** `backend/app/api/v1/webhooks/keycloak.py` (new), `backend/app/api/v1/webhooks/__init__.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_keycloak_webhook.py -q` — green (handler tests mirroring `test_github_webhook.py` pattern).

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_keycloak_webhook_verify.py tests/unit/test_keycloak_webhooks.py tests/unit/test_keycloak_webhook.py tests/unit/test_keycloak_provisioning.py -q
```

**Next:** [`USER_PROVISIONING_P3_EXECUTION.md`](./USER_PROVISIONING_P3_EXECUTION.md)
