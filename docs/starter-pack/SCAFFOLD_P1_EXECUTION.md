# docs/starter-pack/SCAFFOLD_P1_EXECUTION.md

# P1 — Runnable dev platform (execution)

Phase **P1** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md) § Edge cases, § Reuse caveats. **P1 only.**

**Goal:** Developer signs in via Keycloak on DO dev DB and reaches `active` + dashboard (Mode A).

**Authority:** `internal-docs/starter-pack/docs/backend/AUTH.md`, `BOOTSTRAP_SUPER_ADMIN.md`, `USER_REGISTRATION.md` (Mode A).

## Decisions locked for P1

- PostgreSQL **17** on DO managed; extensions + migrations are **operator-run** (not docker-compose PG).
- Run `deploy/sql/postgres-extensions.sql` **and** allow P0 migration `CREATE EXTENSION pgcrypto` (uuid v7).
- Mode A flags: `REGISTRATION_REQUIRE_ADMIN_APPROVAL=false`, `REGISTRATION_REQUIRE_PROFILE_FORM=false` on **both** backend and frontend.
- E2E verification = in-repo checklist + **manual** operator smoke (Q13); not CI.
- **Local env re-baseline:** If `backend/.env` predates Revy scaffold (e.g. `KEYCLOAK_REALM=kp-platform`, `FRONTEND_BASE_URL`, KP storage keys), re-baseline against `backend/.env.example` + `KEYCLOAK_DEV_CHECKLIST.md` **before** Keycloak smoke — `.env` is gitignored; never commit it.
- Do **not** touch `.cursorrules`, `.github/workflows/deploy.yml`, registration APIs, or invitations.

## Out of scope for P1 (later phases)

- `POST /users/complete-profile`, admin APIs → **P2**
- Invitations migration → **P3**
- CI workflow → **P5** (deferred)

---

## P1.1 — Postgres extensions SQL (pgcrypto)

**What:** Add `pgcrypto` to `deploy/sql/postgres-extensions.sql` so operator script matches P0 migration needs; keep PG 17 header comment.

**Files:** `deploy/sql/postgres-extensions.sql`

**Deliverable:** File contains `vector`, `uuid-ossp`, `pg_trgm`, `pgcrypto`; grep confirms: `rg pgcrypto deploy/sql/postgres-extensions.sql`

## P1.2 — Dev bootstrap checklist

**What:** In-repo operator runbook: copy env → **re-baseline legacy `backend/.env`** (drop any key not in `backend/.env.example` / `Settings`; replace KP Keycloak `kp-platform` → Revy `revy` / `revy-api` / `revy-web` per checklist) → extensions on `revy` + `revy_test` → `alembic upgrade head` → Redis compose → optional `seed_bootstrap_super_admin.py` → start API/FE → smoke steps.

**Files:** `docs/starter-pack/DEV_BOOTSTRAP.md`

**Deliverable:** Checklist includes **§ Re-baseline legacy .env** with KP→Revy Keycloak table; ordered steps through `GET /api/v1/me` → `status: active` pass/fail.

## P1.3 — Registration flag matrix

**What:** Document Mode A/B pairing of `REGISTRATION_*` ↔ `VITE_REGISTRATION_*`; warn on mismatch.

**Files:** `docs/starter-pack/REGISTRATION_FLAGS.md`

**Deliverable:** Table for Mode A (P1 default) and Mode B (P2); links from `DEV_BOOTSTRAP.md` and comments in `backend/.env.example` + `frontend/.env.example`.

## P1.4 — Keycloak dev checklist

**What:** Realm `revy`, clients `revy-api` / `revy-web`, audience/azp alignment with `auth.py` allowlist, redirect URIs for `localhost:5173`, email verification on.

**Files:** `docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md`

**Deliverable:** Checklist references `KEYCLOAK_*` and `VITE_KEYCLOAK_*` from env examples; notes `aud: account` + `azp` fallback.

## P1.5 — Env example cross-links

**What:** One-line pointers in env examples to `REGISTRATION_FLAGS.md` and `DEV_BOOTSTRAP.md` (no new env keys).

**Files:** `backend/.env.example`, `frontend/.env.example`

**Deliverable:** `rg 'docs/starter-pack/(DEV_BOOTSTRAP|REGISTRATION_FLAGS)' backend/.env.example frontend/.env.example` — both files match.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/ -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run
```

**Human gate:** Operator re-baselines local `backend/.env` (if legacy KP), completes `DEV_BOOTSTRAP.md` on DO dev DB + Keycloak, records smoke pass (JWT → `/api/v1/me` → `active`). LOOP may commit after automated gates; human gate tracked in README status note.

**Deploy:** None — dev-only docs + deploy SQL comment fix.

**Next:** [`SCAFFOLD_P2_EXECUTION.md`](./SCAFFOLD_P2_EXECUTION.md)
