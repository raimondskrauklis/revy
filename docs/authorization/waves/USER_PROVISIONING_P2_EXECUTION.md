# docs/authorization/waves/USER_PROVISIONING_P2_EXECUTION.md

# P2 — Keycloak event listener deploy (execution)

Phase **P2** of [`USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md). **P2 only.**

**Goal:** Keycloak container sends identity events to Revy `POST /api/v1/webhooks/keycloak` in dev and production.

## Decisions locked for P2

- **Same artifact as P1:** [vymalo/keycloak-webhook](https://github.com/vymalo/keycloak-webhook) **`0.10.0-rc.1`** — `keycloak-webhook-provider-core-*-all.jar` + `keycloak-webhook-provider-http-*-all.jar` copied to `/opt/keycloak/providers/` before `kc.sh build`.
- **Prod webhook URL (D8):** `http://revy-api:8000/api/v1/webhooks/keycloak` on `revy-net` — **do not** add nginx location on public hosts.
- **Dev URL:** `http://host.docker.internal:8000/api/v1/webhooks/keycloak` when API runs on host; or `http://revy-api:8000/...` when API container shares `revy-net`.
- Secret matches `KEYCLOAK_WEBHOOK_SECRET`; listener sends `X-Webhook-Secret`.
- JAR pin (D12): document sha256 of both shaded JARs in Dockerfile comment.

## Out of scope for P2

- In-app admin UI → deferred
- SCIM → out of program

---

## P2.1 — Dockerfile + pinned JARs

**What:** Download vymalo `0.10.0-rc.1` shaded JARs in Dockerfile `RUN curl -L ...` (pin URLs + sha256 comment); copy to `providers/`; rebuild with existing `kc.sh build`.

**Files:** `deploy/keycloak/config/Dockerfile`, `deploy/keycloak/config/README.md`

**Deliverable:** `cd deploy/keycloak/config && docker compose build` — succeeds.

---

## P2.2 — Compose env + listener config

**What:** vymalo HTTP env vars; wire in compose; **confirm nginx configs have no public `/webhooks/keycloak` route** (D8).

**Files:** `deploy/keycloak/config/docker-compose.yml`, `deploy/keycloak/config/.env.example`, `deploy/env-examples/backend.env.production.example`, `deploy/nginx/` (verify only — no new public route)

**Deliverable:** `.env.example` documents dev URL (`host.docker.internal`) and prod URL.

---

## P2.3 — Dev wiring runbook

**What:** Step-by-step: API with secret → KC rebuild → register test user → confirm `keycloak_webhook_deliveries` + `users` rows.

**Files:** `deploy/keycloak/config/README.md` (pointer only — full smoke checklist in P4.2)

**Deliverable:** Runbook section with log/SQL check commands.

---

**Phase gate** (from repo root):

```bash
cd deploy/keycloak/config && docker compose build
cd ../../../backend && pipenv run lint && pipenv run pytest tests/unit/test_keycloak_webhook.py tests/unit/test_keycloak_webhooks.py -q
```

**Human gate:** Operator runs P2.3 dev smoke — KC event reaches API before SPA login.

**Deploy:** Rebuild KC on droplet — `docker compose build --no-cache && docker compose up -d` from `/mnt/revy_volume/keycloak/config/`.

**Next:** [`USER_PROVISIONING_P4_EXECUTION.md`](./USER_PROVISIONING_P4_EXECUTION.md)
