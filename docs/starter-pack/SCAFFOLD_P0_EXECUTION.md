# docs/starter-pack/SCAFFOLD_P0_EXECUTION.md

# P0 — Scaffold baseline (execution)

Phase **P0** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md). **P0 only — retrospective.**

**Goal:** Starter-pack backend + frontend shell in repo with aligned config and hand-written P0/P1 migrations.

**Authority:** `internal-docs/starter-pack/` templates + `internal-docs/product/revy/` overlay.

## Decisions locked for P0

- Hand-written Alembic only — **no** `--autogenerate`; revisions `2026_07_23_2315_0001_*` (P0 identity) and `0002_p1_items` (items demo — not invitations).
- Canonical env: `backend/.env.example`, `frontend/.env.example`.
- `ENVIRONMENT=development`; frontend `--app-*` + `tokens.revy.css`.
- Unit tests only under `backend/tests/unit/`.

## Out of scope for P0 (later phases)

- DO operator bootstrap → **P1**
- Registration/admin APIs + FE forms → **P2**
- Invitations DB, idempotency wire → **P3**
- Revy domain → **P4**
- `.cursorrules`, CI, `AGENTS.md` → **P5** (deferred)

---

## P0.1 — Backend starter-pack copy + Revy config

**What:** FastAPI app, auth, permissions, pagination, P0/P1 migrations, 43 unit tests.

**Files:** `backend/app/**`, `backend/alembic/versions/2026_07_23_2315_*.py`, `backend/.env.example`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/ -q` — 43 passed.

## P0.2 — Frontend starter-pack + Revy tokens

**What:** SPA shell, Keycloak, routing, Quiet*, i18n EN/LV, `tokens.revy.css`.

**Files:** `frontend/src/**`, `frontend/.env.example`

**Deliverable:** `cd frontend && npm test -- --run && npm run build` — green.

## P0.3 — Deploy env hints + plan docs

**What:** `deploy/env-examples/`, `deploy/sql/postgres-extensions.sql`, `docs/starter-pack/` findings + general plan.

**Files:** `deploy/**`, `docs/starter-pack/SCAFFOLD_*.md`

**Deliverable:** `test -f deploy/env-examples/README.md && test -f docs/starter-pack/SCAFFOLD_FINDINGS.md && test -f docs/starter-pack/SCAFFOLD_GENERAL_PLAN.md` — all exist.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/ -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run && npm run build
```

**Status:** **Done** (2026-07-23).

**Next:** [`SCAFFOLD_P1_EXECUTION.md`](./SCAFFOLD_P1_EXECUTION.md)
