# PostgreSQL connection guide (Revy)

How to connect to the **DigitalOcean managed PostgreSQL 17** database used by Revy — for pgAdmin, one-off SQL, and understanding Alembic.

**Canonical env:** `backend/.env.example` → copy to `backend/.env` (gitignored).

**Related:** `deploy/sql/postgres-extensions.sql`, `deploy/env-examples/README.md`, `docs/starter-pack/SCAFFOLD_P1_EXECUTION.md` (dev bootstrap).

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | App + Alembic (dev) — `postgresql+asyncpg://…` |
| `TEST_DATABASE_URL` | Pytest / future integration tests |

Revy does **not** use KP-style `PROD_DATABASE_URL` in the app env. Production URLs live in deploy secrets / droplet `.env` only.

Example shape (from `backend/.env.example`):

```text
DATABASE_URL=postgresql+asyncpg://revy-user-dev:****@….db.ondigitalocean.com:25060/revy-dev?ssl=require
TEST_DATABASE_URL=postgresql+asyncpg://revy-user-test:****@….db.ondigitalocean.com:25060/revy-dev?ssl=require
```

Use the **exact** database name and user from your DO cluster (e.g. `revy-dev`, `revy-user-dev`).

---

## DigitalOcean: pooled vs direct

DO exposes multiple connection modes:

| Mode | Typical port | Use for |
|------|--------------|---------|
| **Connection pool** | `25060` | FastAPI runtime (`DATABASE_URL` in `.env`) |
| **Direct / session** | From DO console (“Connection parameters”) | **Alembic migrations**, extensions, one-off DDL |

**Rule:** Run `pipenv run alembic upgrade head` with the **direct (non-pooled)** URL from the DO control panel. Pooled connections can make DDL look successful while nothing persists.

App runtime may keep the pooled URL on port `25060`.

---

## Operator setup (once per database)

Run as **`doadmin`** in pgAdmin (or `psql`), connected to the **target database** (e.g. `revy-dev`), not `defaultdb`.

### 1. Extensions (doadmin)

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS pgcrypto;
```

(`pgcrypto` is also created in Alembic P0 if the app user can install it — pre-installing as `doadmin` is safer on DO.)

See `deploy/sql/postgres-extensions.sql`.

### 2. App user grants (doadmin, on `revy-dev`)

PostgreSQL 15+ / DO: `public` is owned by `pg_database_owner`. App users need explicit `CREATE`:

```sql
GRANT CONNECT ON DATABASE "revy-dev" TO "revy-user-dev";
GRANT USAGE, CREATE ON SCHEMA public TO "revy-user-dev";
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "revy-user-dev";
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "revy-user-dev";
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO "revy-user-dev";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "revy-user-dev";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "revy-user-dev";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO "revy-user-dev";
```

Repeat for `revy-user-test` (or your `TEST_DATABASE_URL` user) on the **same or separate** test database.

**Verify** (run for each app user):

```sql
SELECT has_schema_privilege('revy-user-dev', 'public', 'CREATE');
SELECT has_schema_privilege('revy-user-test', 'public', 'CREATE');
```

`ALTER SCHEMA public OWNER TO …` often fails on DO — **not required** if `GRANT CREATE` is set.

---

## Migrations (Alembic)

From `backend/`:

```bash
# Use direct connection URL for this command (see above)
pipenv run alembic upgrade head
pipenv run alembic current
```

Hand-written revisions only — **no** `--autogenerate`. Revision ids use the long form `YYYY_MM_DD_HHMM_NNNN_slug` (see `backend/alembic.ini`).

### `alembic_version.version_num` length

Default Alembic uses `VARCHAR(32)`. Revy revision ids are longer (~50+ chars). The repo registers `RevyPostgresqlImpl` (`backend/app/core/alembic_postgresql.py`) so new installs use **`VARCHAR(128)`**, and `backend/alembic/env.py` widens an existing `VARCHAR(32)` column before migrating.

**Applies to every database Alembic connects to** — dev (`DATABASE_URL`), test (`alembic -x test=true` → `TEST_DATABASE_URL`), staging, CI. No per-environment SQL needed; run upgrade once per database.

If you hit `StringDataRightTruncationError` on `version_num`, pull latest `env.py` + `alembic_postgresql.py` and re-run upgrade on that database.

### Test migrations

```bash
cd backend
pipenv run alembic -x test=true upgrade head
pipenv run alembic -x test=true current
```

Uses `TEST_DATABASE_URL` from `backend/.env`. The **test DB user** (e.g. `revy-user-test`) needs the same `GRANT USAGE, CREATE ON SCHEMA public` as the dev user — even when test and dev share one database name, users are separate roles.

If `TEST_DATABASE_URL` points at a **different** database (e.g. `revy-test`), run extensions + grants on **that** database too.

---

## App schema (after P0 + P1 migrations)

| Table | Role |
|-------|------|
| `users` | Keycloak-linked accounts, `user_status` |
| `workspaces` | Tenants |
| `workspace_memberships` | User ↔ workspace + `user_role` |
| `items` | Starter-pack demo CRUD |
| `alembic_version` | Alembic head revision |

Enums: `user_role`, `user_status`, `workspace_status`, `platform_role`.

---

## pgAdmin / psql

1. Host / port / database / user from `backend/.env` (`DATABASE_URL`).
2. SSL: **require**.
3. Connect to the **same database name** as in the URL (`revy-dev`, not a generic `revy` unless that is what DO created).

Quick checks:

```sql
SELECT current_user, current_database();
SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1;
SELECT version_num FROM alembic_version;
```

---

## Direct `asyncpg` script (ad hoc)

For one-off scripts outside FastAPI, strip the SQLAlchemy driver prefix:

```python
# postgresql+asyncpg://… → postgresql://…
url = os.environ["DATABASE_URL"].replace("postgresql+asyncpg://", "postgresql://")
url = url.replace("?ssl=require", "")
conn = await asyncpg.connect(url, ssl=ssl.create_default_context())
```

Prefer verified TLS (`ssl.create_default_context()`). Emergency only: `DATABASE_SSL_INSECURE=1` disables verification (same pattern as legacy KP scripts).

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| `permission denied for schema public` | `GRANT CREATE ON SCHEMA public` on **this** database; user name matches `.env` |
| `has_schema_privilege` true in pgAdmin but false from app | Grants on wrong DB (`revy` vs `revy-dev`) or wrong user |
| `StringDataRightTruncationError` on `version_num` | Revy Alembic impl + widen helper (see above) |
| Migrations log success but no tables | Used **pooled** URL for Alembic — switch to **direct** URL |
| `CREATE EXTENSION` fails for app user | Run extensions as **doadmin** first |
| `CantChangeRuntimeParamError` (asyncpg) | Remove `?ssl=require` from URL; pass `ssl=` context |
| Connection refused | DO trusted sources / firewall; VPN |

---

## What this guide is not

- Not KP analytics (`raw_eis_*`, `PROD_DATABASE_URL`, `scripts/utils/db_utils.py` — those do not exist in Revy).
- Not production droplet ops (see `deploy/env-examples/`).
- Not a substitute for `docs/starter-pack/` execution runbooks.
