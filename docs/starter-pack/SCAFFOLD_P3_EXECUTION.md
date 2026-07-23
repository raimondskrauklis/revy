# docs/starter-pack/SCAFFOLD_P3_EXECUTION.md

# P3 — Shared platform hardening (execution)

Phase **P3** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md) § Reuse caveats. **P3 only.**

**Goal:** Close starter-pack gaps that block every future feature (invitations, idempotency, logging, test bootstrap).

**Authority:** `internal-docs/starter-pack/docs/backend/INVITATIONS.md`, `IDEMPOTENCY.md`.

## Decisions locked for P3

- Alembic revision label **`invitations`** — not “P1”; distinct from `0002_p1_items`.
- Hand-written migration only; **LOOP pauses** after migration subphase until operator applies on DO dev DB.
- Idempotency on all **POST** mutation routes shipped so far: items create, workspace invitations create, invitations accept, users complete-profile, admin approve/reject (if POST).
- Remove `Settings.extra = "ignore"` only **after** local `backend/.env` contains **only** keys allowed by `Settings` / `backend/.env.example` (Q11 — P3.5). Not limited to `KP_*` — drop any orphan key (`STORAGE_*`, `FRONTEND_BASE_URL`, etc.).
- Drop `backend/app/models/_example_product_item.py.example` if still unused.
- Optional: remove `billing` service/schemas or add “carryover” comment — prefer remove if zero imports.

## Out of scope for P3 (later phases)

- Revy `github_installation` domain → **P4**
- Celery Revy queue map → **P4**
- CI / `.cursorrules` → **P5** (deferred)

---

## P3.1 — Invitations migration

**What:** Hand-written `workspace_invitations` table per INVITATIONS.md (**no** `--autogenerate`); revision id `YYYY_MM_DD_HHMM_NNNN_invitations` (next sequence after `0002`).

**Files:** `backend/alembic/versions/<new>_invitations.py`, `backend/app/models/invitations.py` (new ORM), `backend/app/models/__init__.py` (import ORM — `alembic/env.py` does `import app.models`)

**Deliverable:** Migration file exists; `rg workspace_invitations backend/alembic/versions/` — match.

**Human gate (LOOP pause):** Operator runs `alembic upgrade head` on DO dev DB before P3.2.

## P3.2 — Wire invitations service + fix comments

**What:** Implement `create_invitation` / `accept_invitation` against DB; send email via existing dispatch; fix “P1 migration” comments in `invitations.py`, `enums.py`, API modules.

**Files:** `backend/app/services/invitations.py`, `backend/app/api/v1/workspaces/invitations.py`, `backend/app/api/v1/invitations.py`, `backend/app/constants/enums.py`, `backend/tests/unit/test_invitations.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_invitations.py -q` — pass.

## P3.3 — Idempotency on POST routers

**What:** Attach idempotency per IDEMPOTENCY.md on POST handlers listed in locked decisions. **Wiring:** add a FastAPI dependency (or router dependency) that resolves `user_sub` from `get_current_user`, calls `load_idempotent_response` **before** handler body parsing, and `store_idempotent_response` on success — `load_idempotent_response` calls `await request.body()` once; do not read body again in handler without using cached bytes / Pydantic from dependency.

**Files:** `backend/app/core/idempotency.py` (add `idempotency_guard` Depends factory if needed), `backend/app/api/v1/items.py`, workspace + global invitations, users complete-profile, admin approve/reject, `backend/tests/unit/test_idempotency.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_idempotency.py -q` — pass.

## P3.4 — JsonFormatter `extra` merge

**What:** Merge `record.__dict__` extras (excluding std LogRecord keys) into JSON log output.

**Files:** `backend/app/core/logging.py`, `backend/tests/unit/test_logging_config.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_logging_config.py -q` — pass.

## P3.5 — Test bootstrap + Settings cleanup

**What:** Uncomment/wire `tests/conftest.py` fixtures; document `ENVIRONMENT=test`. **First:** prune local `backend/.env` so **every key** is defined on `Settings` / listed in `backend/.env.example` (remove legacy KP and non-Revy keys — e.g. `FRONTEND_BASE_URL`, `STORAGE_*`, `PROD_DATABASE_URL`, `RAW_FILES_BUCKET`, `ENABLE_REQUEST_LOGGING`, not only `KP_*` prefixes). Verify boot: `cd backend && pipenv run python -c "from app.core.config import settings; print(settings.environment)"`. **Then** remove `extra="ignore"` from Settings. Sync starter-pack template **if** `internal-docs/` is available — otherwise skip and note in commit.

**Files:** `backend/tests/conftest.py`, `backend/app/core/config.py`, `docs/starter-pack/DEV_BOOTSTRAP.md` (§ Env pruning), `internal-docs/starter-pack/templates/backend/app/core/config.py` (optional)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/ -q` — all pass; `rg 'extra=\"ignore\"' backend/app/core/config.py` — no match; Settings loads without validation errors on pruned `.env`.

## P3.6 — Scaffold cruft cleanup

**What:** Delete `_example_product_item.py.example`; remove unused `billing` module/schemas if unreferenced.

**Files:** `backend/app/models/_example_product_item.py.example`, `backend/app/services/billing.py`, `backend/app/schemas/billing.py`, `backend/app/services/__init__.py`

**Deliverable:** `cd backend && pipenv run lint && pipenv run pytest tests/unit/ -q` — pass.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_invitations.py tests/unit/test_idempotency.py tests/unit/test_logging_config.py tests/unit/ -q
```

**Deploy:** Migrations (P3.1, if continuing) require DO dev DB apply — see Human gate on P3.1.

**Human gate:** After P3.1 migration subphase — operator confirms `alembic upgrade head` on DO dev DB before P3.2.

**Next:** [`SCAFFOLD_P4_EXECUTION.md`](./SCAFFOLD_P4_EXECUTION.md)
