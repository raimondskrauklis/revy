# Dev bootstrap checklist (Revy)

Operator runbook: DigitalOcean managed PostgreSQL 17, Keycloak, local Redis, API + SPA. **Mode A** (open registration, no admin approval, no profile form).

**Related:** [REGISTRATION_FLAGS.md](./REGISTRATION_FLAGS.md) · [KEYCLOAK_DEV_CHECKLIST.md](./KEYCLOAK_DEV_CHECKLIST.md) · [DATABASE_CONNECTION_GUIDE.md](../utils/DATABASE_CONNECTION_GUIDE.md)

---

## Prerequisites

- DO managed PostgreSQL cluster (dev + test DB users/databases)
- Keycloak reachable from your machine (local `localhost:8080` or shared dev realm)
- `pipenv`, Node 20+, Docker (Redis only)

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

Test DB (optional local check):

```bash
pipenv run alembic -x test=true upgrade head
```

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
2. Run:

   ```bash
   cd backend
   pipenv run python -m scripts.seed_bootstrap_super_admin
   ```

3. Remove `BOOTSTRAP_SUPER_ADMIN_EMAIL` from `.env` after first successful login.

Register in Keycloak with the **same email** on first login.

---

## 6. Keycloak

Complete [KEYCLOAK_DEV_CHECKLIST.md](./KEYCLOAK_DEV_CHECKLIST.md) before starting the API.

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
| Open `http://localhost:5173` | Login page loads |
| Sign in via Keycloak | Redirect back without console auth errors |
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
