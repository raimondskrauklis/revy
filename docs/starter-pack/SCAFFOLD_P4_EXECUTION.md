# docs/starter-pack/SCAFFOLD_P4_EXECUTION.md

# P4 — Revy product foundation (execution)

Phase **P4** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md). **P4 only.**

**Goal:** First Revy domain vertical on platform rails — `github_installation` CRUD/list with workspace tenancy.

**Authority:** `internal-docs/product/revy/docs/TENANCY.md`, `PLATFORM_CONTEXT.md` (core entities table); committed slice: `docs/starter-pack/REVY_PRODUCT_SLICE.md`.

## Decisions locked for P4

- **Q12:** Author redacted `REVY_PRODUCT_SLICE.md` in repo **before** any migration/API code (P4.1 blocks P4.2).
- First vertical = **`github_installation`** only (not full review pipeline, webhooks, or pgvector index).
- Workspace-scoped list/create; `admin` permission on workspace; mirror fields from TENANCY.md (installation ID, account login, workspace_id).
- Celery: wire Revy queue names from **`REVY_PRODUCT_SLICE.md` § Celery queues** (copied from `implementation.revy.md` in P4.1); task modules may be stubs until webhook/review program.
- Sideline items demo: no items link in nav today — add installations nav in P4.4; keep items API/code as pattern reference (do not delete migration).
- EN+LV for dashboard installation UI strings.

## Out of scope for P4 (later programs)

- GitHub webhooks, review runs, findings, embeddings → future phases
- Production deploy pipeline → separate program
- `.cursorrules` / CI → **P5** (deferred)

---

## P4.1 — Committed product slice spec

**What:** Redact `github_installation` vertical from `internal-docs/product/revy/docs/` into repo-safe spec: entities, API shapes, permissions, exclusions, **and Celery queue name table** (for P4.5).

**Files:** `docs/starter-pack/REVY_PRODUCT_SLICE.md`

**Deliverable:** File exists; sections: Goal, Entities, API endpoints, Permissions, Celery queues, Exclusions; `rg 'github_events' docs/starter-pack/REVY_PRODUCT_SLICE.md` — match.

## P4.2 — Installations migration + ORM

**What:** Hand-written migration `github_installations` (**no** `--autogenerate`) with `workspace_id` FK, unique `github_installation_id`, account metadata columns per slice.

**Files:** `backend/alembic/versions/<new>_github_installations.py`, `backend/app/models/github_installation.py`, `backend/app/models/__init__.py` (import ORM), `backend/app/constants/enums.py` (if needed)

**Deliverable:** `rg github_installations backend/alembic/versions/` — match.

**Human gate (LOOP pause):** Operator applies migration on DO dev DB before P4.3 API smoke.

## P4.3 — Installations service + API

**What:** Cursor-paginated `GET /api/v1/workspaces/{workspace_id}/installations`, `POST` create (manual register for dev until webhook phase), tenancy + permission guards.

**Files:** `backend/app/services/github_installations.py`, `backend/app/api/v1/workspaces/installations.py`, `backend/app/api/v1/workspaces/__init__.py`, `backend/app/schemas/github_installation.py`, `backend/tests/unit/test_github_installations.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_installations.py -q` — pass.

## P4.4 — Installations dashboard UI

**What:** Workspace settings or dedicated route listing installations; empty state; create form for dev registration.

**Files:** `frontend/src/features/installations/**`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/components/layout/AppShellLayout.tsx` (installations nav), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `cd frontend && npm test -- --run Installations && npm run build` — pass.

## P4.5 — Celery Revy queue map

**What:** Replace generic queue routing using queue names from `REVY_PRODUCT_SLICE.md`; worker entrypoint documents queue list.

**Files:** `backend/app/workers/celery_app.py`, `backend/.env.example` (if queue env vars)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/ -q` — pass; `rg github_events backend/app/workers/` — match.

## P4.6 — Doc sync

**What:** Update plan README status; sync affected docs.

| Doc | Change |
|-----|--------|
| `docs/starter-pack/README.md` | P4 status Done + sha |
| `docs/starter-pack/SCAFFOLD_FINDINGS.md` | Catalog row for github_installation |
| `docs/starter-pack/DEV_BOOTSTRAP.md` | Note installations dev path if needed |

**Deliverable:** README execution table P4 row updated.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_github_installations.py tests/unit/ -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run && npm run build
```

**Human gate:** After P4.2 — operator confirms migration on DO dev DB before P4.3 (see P4.2). Optional: register test installation row via UI on dev workspace.

**Deploy:** Migrations require DO dev DB apply — see Human gates on P4.2.

**Next:** [`SCAFFOLD_P5_EXECUTION.md`](./SCAFFOLD_P5_EXECUTION.md) — **deferred** until product owner invokes Phase 5.
