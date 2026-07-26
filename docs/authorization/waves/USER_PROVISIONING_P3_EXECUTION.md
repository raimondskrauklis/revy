# docs/authorization/waves/USER_PROVISIONING_P3_EXECUTION.md

# P3 — Bootstrap & email hardening (execution)

Phase **P3** of [`USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md). **P3 only.**

**Goal:** Fail fast on misconfigured bootstrap; document invitation ↔ provision interaction.

## Decisions locked for P3

- On app startup: `async with AsyncSessionLocal() as session:` inside `lifespan` → `await validate_bootstrap_super_admin_config(session)` (same pattern as one-shot DB read; no long-lived session).
- If `BOOTSTRAP_SUPER_ADMIN_EMAIL` set and no matching seed row → warn in `development`, raise in `production` / `staging`.
- **`ENVIRONMENT=test`** → skip guard entirely (D11) so pytest does not require seed.
- Cross-sub email conflict already in P0 — P3 adds integration test + invitation comment only.
- **P3.3:** bootstrap guard + “KC user ≠ PG user” only in `DEV_BOOTSTRAP.md` — P4.2 owns webhook/Google smoke (no duplicate bootstrap sections).
- No migration.

## Out of scope for P3

- Webhook deploy → **P2**
- Full doc sync → **P4**

---

## P3.1 — Startup bootstrap guard

**What:** `validate_bootstrap_super_admin_config(session)` in `backend/app/core/bootstrap.py`; call from `lifespan` after `init_db()` using `AsyncSessionLocal`.

**Files:** `backend/app/core/bootstrap.py` (new), `backend/app/main.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_bootstrap_config.py -q` — green (dev allows missing seed with warning; staging/prod fail).

---

## P3.2 — Invitation + provision comments + integration test

**What:** Module docstring on `keycloak_provisioning.py` — invitee must login (JIT or webhook) before `accept_invitation`; test: provision user then accept invite.

**Files:** `backend/app/services/keycloak_provisioning.py`, `backend/tests/unit/test_keycloak_provisioning.py` (extend), `backend/app/services/invitations.py` (comment only)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_keycloak_provisioning.py tests/unit/test_invitations.py -q` — green.

---

## P3.3 — DEV_BOOTSTRAP operator note (bootstrap only)

**What:** Add § bootstrap startup guard + “run seed before Google login when bootstrap email set”. **Do not** add webhook smoke here (P4.2).

**Files:** `docs/starter-pack/DEV_BOOTSTRAP.md`

**Deliverable:** Section present — manual review.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_bootstrap_config.py tests/unit/test_keycloak_provisioning.py tests/unit/test_invitations.py -q
```

**Next:** [`USER_PROVISIONING_P2_EXECUTION.md`](./USER_PROVISIONING_P2_EXECUTION.md)
