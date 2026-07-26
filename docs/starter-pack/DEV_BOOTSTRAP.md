# Dev bootstrap checklist (Revy)

Operator runbook: DigitalOcean managed PostgreSQL 17, Keycloak, local Redis, API + SPA. **Mode A** (open registration, no admin approval, no profile form).

**Related:** [REGISTRATION_FLAGS.md](./REGISTRATION_FLAGS.md) · [KEYCLOAK_DEV_CHECKLIST.md](./KEYCLOAK_DEV_CHECKLIST.md) · [DATABASE_CONNECTION_GUIDE.md](../utils/DATABASE_CONNECTION_GUIDE.md)

---

## Prerequisites

- DO managed PostgreSQL cluster (dev + test DB users/databases)
- Keycloak reachable from your machine (local `localhost:8080` or shared dev realm)
- `pipenv`, Node 24 LTS+, Docker (Redis only)

---

## 1. Re-baseline legacy `backend/.env`

`backend/.env` is gitignored. If it predates the Revy scaffold (copied from KP), replace KP values before smoke tests.

| KP / legacy | Revy (canonical) |
|-------------|----------------|
| `KEYCLOAK_REALM=kp-platform` | `KEYCLOAK_REALM=revy` |
| `KEYCLOAK_CLIENT_ID=kp-platform-api` (or similar) | `KEYCLOAK_CLIENT_ID=revy-api` |
| `KEYCLOAK_FRONTEND_CLIENT_ID` missing or wrong | `KEYCLOAK_FRONTEND_CLIENT_ID=revy-web` |
| `FRONTEND_BASE_URL` | **Remove** — use `APP_PUBLIC_URL` |
| `DO_KP_FILES_BUCKET`, KP mailgun keys, etc. | **Remove** — keep only keys in `backend/.env.example` |

**Steps:**

1. `cp backend/.env.example backend/.env` (or diff and fix in place).
2. Set `DATABASE_URL`, `TEST_DATABASE_URL`, `KEYCLOAK_*`, `SECRET_KEY` for your environment.
3. Confirm `ENVIRONMENT=development` (not `local`).
4. Mode A flags (must match frontend — see [REGISTRATION_FLAGS.md](./REGISTRATION_FLAGS.md)):

   ```text
   REGISTRATION_REQUIRE_ADMIN_APPROVAL=false
   REGISTRATION_REQUIRE_PROFILE_FORM=false
   ```

5. Copy frontend env: `cp frontend/.env.example frontend/.env.local` and align `VITE_KEYCLOAK_*` with backend.

### Env pruning (P3 — strict Settings)

`Settings` rejects unknown keys. Before running the API or tests after P3, ensure `backend/.env` contains **only** variables defined in `backend/.env.example` / `app.core.config.Settings`.

Remove legacy carryover keys, for example:

- `FRONTEND_BASE_URL` → use `APP_PUBLIC_URL`
- `STORAGE_*`, `RAW_FILES_BUCKET`, `DO_KP_*`
- `PROD_DATABASE_URL`, `ENABLE_REQUEST_LOGGING`
- Any `KP_*` prefix from the KP platform fork

Verify:

```bash
cd backend && pipenv run python -c "from app.core.config import settings; print(settings.environment)"
```

For CI and local unit tests, set `ENVIRONMENT=test` when using a dedicated test database (see `TEST_DATABASE_URL` in `.env.example`).

---

## 2. PostgreSQL extensions (doadmin)

On each target database (`revy-dev` / `revy_test` — use your DO names), as **doadmin**:

```bash
# From repo — paste SQL in pgAdmin or psql
cat deploy/sql/postgres-extensions.sql
```

Must include: `vector`, `uuid-ossp`, `pg_trgm`, `pgcrypto`.

Grant app users `USAGE, CREATE` on `public` — see [DATABASE_CONNECTION_GUIDE.md](../utils/DATABASE_CONNECTION_GUIDE.md).

---

## 3. Migrations

From `backend/`, use the **direct** (non-pooled) connection URL in `.env` for DDL:

```bash
cd backend
pipenv run alembic upgrade head
pipenv run alembic current
```

**Verify:** `pipenv run alembic current` prints a revision id (not empty). Online migrations use `AUTOCOMMIT` in `backend/alembic/env.py` — without it, asyncpg rolls back on disconnect and you get no tables / no `alembic_version` despite success logs.

Test DB (optional local check):

```bash
pipenv run alembic -x test=true upgrade head
```

Optional: register a test GitHub installation via **Installations** in the dashboard — **install the app on GitHub first**, then use the installation ID from `https://github.com/settings/installations/<id>` (not the App ID). See [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md).

---

## 4. Local Redis

```bash
cd backend
docker compose up -d
docker compose ps   # redis healthy
```

---

## 5. Optional bootstrap super admin

One-time per environment if you need a platform `super_admin` before normal registration:

1. Set `BOOTSTRAP_SUPER_ADMIN_EMAIL=you@example.com` in `backend/.env`.
2. Run the seed **before** starting the API (staging/production fail fast if the row is missing while this env var is set):

   **Local dev:**

   ```bash
   cd backend
   pipenv run python -m scripts.seed_bootstrap_super_admin
   ```

   **Droplet (one-off container — does not start uvicorn):**

   ```bash
   docker run --rm \
     --network revy-net \
     --env-file /mnt/revy_volume/backend/.env \
     registry.digitalocean.com/revy-container-registry/revy-api:latest \
     python -m scripts.seed_bootstrap_super_admin
   ```

3. Remove `BOOTSTRAP_SUPER_ADMIN_EMAIL` from `.env` after first successful login.

Register in Keycloak with the **same email** on first login.

**Startup guard:** When `BOOTSTRAP_SUPER_ADMIN_EMAIL` is set, the API validates on boot that a matching `super_admin` seed row exists (`pending_activation`). Run the seed script **before** starting the API or enabling SSO login when using bootstrap — a crash-looping `revy-api` container cannot seed itself. In `development`, a missing seed logs a warning; in `staging`/`production`, startup fails fast. `ENVIRONMENT=test` skips the guard (pytest).

**KC user ≠ PG user:** Keycloak holds identity only; PostgreSQL `users` is created by the KC identity webhook (primary) or JIT on first authenticated `/api/v1/me` (fallback). See [docs/authorization/README.md](../authorization/README.md).

---

## 6. Keycloak

Complete [KEYCLOAK_DEV_CHECKLIST.md](./KEYCLOAK_DEV_CHECKLIST.md) before starting the API.

**Production DNS (createit.digital):** app `https://revy.createit.digital`, Keycloak `https://auth.revy.createit.digital` — set matching `VITE_KEYCLOAK_*` in GitHub Actions and `ALLOWED_ORIGINS` on the droplet.

---

## 7. Start API and frontend

```bash
# Terminal 1 — API
cd backend && pipenv run uvicorn app.main:app --reload --port 8000

# Terminal 2 — SPA
cd frontend && npm run dev
```

---

## 8. Smoke test (manual — Q13)

| Step | Pass criteria |
|------|----------------|
| Open `http://localhost:5173` | Public landing page loads (`/`); `/login` shows SSO |
| Sign in via Keycloak (`/login` or landing CTA) | Redirect back without console auth errors |
| `GET http://localhost:8000/health` | `200` |
| Browser → API `GET /api/v1/me` (authenticated) | `200`, `"status": "active"` |
| Dashboard | Loads after login (Mode A) |

**Fail common causes:**

- `Invalid token audience` — client ids / realm mismatch; see Keycloak checklist.
- `permission denied for schema public` — DB grants on correct database/user.
- `pending_email_verification` — verify email in Keycloak or disable required action for dev.

Record smoke date + operator in your team notes (not committed).

---

## Phase gate (automated — no Keycloak required)

```bash
cd backend && pipenv run lint && pipenv run pytest tests/unit/ -q
cd frontend && npm run lint && npm test -- --run
```

---

## 9. Migrations 0008–0009 (SaaS base W6–W7)

After W6/W7 ship, `alembic upgrade head` applies:

| Revision | Purpose |
|----------|---------|
| `0008` | Data export jobs (`export_jobs`) |
| `0009` | Impersonation sessions (`impersonation_sessions`) |

---

## 10. Celery worker (export + maintenance)

Data export (W6) and maintenance tasks run on the **`maintenance`** queue:

```bash
cd backend
pipenv run celery -A app.workers.celery_app worker -Q maintenance,default --loglevel=info
```

Set `EXPORT_STORAGE_PATH` (default `/tmp/revy/exports` in dev) and optional `EXPORT_TTL_DAYS` (default `7`) in `backend/.env`. Production: see `deploy/env-examples/backend.env.production.example`.

---

## 11. Ops pointers (W8)

| Topic | Doc |
|-------|-----|
| Staging sign-off checklist | [docs/saas-base/STAGING_VERIFICATION.md](../saas-base/STAGING_VERIFICATION.md) |
| Export worker, Stripe webhook, bootstrap | [docs/saas-base/OPS.md](../saas-base/OPS.md) |
| Stripe setup | [docs/utils/STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md) |
| Review pipeline ops | [GITHUB_WEBHOOK_DEV.md](../review-pipeline/GITHUB_WEBHOOK_DEV.md) (R0+) |
