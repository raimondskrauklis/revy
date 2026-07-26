# docs/authorization/waves/USER_PROVISIONING_P0_EXECUTION.md

# P0 — Unified provision service (execution)

Phase **P0** of [`USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md). Baseline: [`USER_PROVISIONING_FINDINGS.md`](../USER_PROVISIONING_FINDINGS.md). **P0 only.**

**Goal:** Single idempotent `provision_user_from_keycloak()` — JIT auth path calls it; P1 webhook reuses same function.

## Decisions locked for P0

- New module `backend/app/services/keycloak_provisioning.py` — canonical provision entry.
- **`async def provision_user_from_keycloak(...)`** — all DB I/O async (matches existing services).
- Email stored **lowercase** on insert/update; lookup remains case-insensitive.
- Missing email → `UnauthorizedError` with `error_code=provision_email_required`.
- Same email, different `sub` → `ConflictError` with `error_code=identity_email_conflict` (no silent merge).
- Same `sub`, email change on existing row → update email if new address not taken; else `identity_email_conflict` (D10).
- Mode A (`REGISTRATION_REQUIRE_*` both false) + `email_verified` → one transaction ends `status=active` with workspace (no intermediate `pending_profile` exposed).
- Bootstrap: seeded `pending_activation` row matched by email before new insert; `activate_bootstrap_super_admin` logic folded into provision service.
- `ensure_user_from_token` becomes thin wrapper or removed — callers use provision service only from `auth.py`.
- No migration in P0.
- Unit tests only.

## Out of scope for P0 (later phases)

- Webhook route, idempotency table → **P1**
- KC HTTP listener → **P2**
- API startup bootstrap guard → **P3**
- Doc/runbook updates → **P4**

---

## P0.1 — Provision service + email normalization

**What:** Add `async def provision_user_from_keycloak(session, *, sub, email, email_verified, display_name=None) -> UserORM` with normalized email, bootstrap email skip, insert-or-update by `sub`, structured log `user_provisioned`.

**Files:** `backend/app/services/keycloak_provisioning.py` (new), `backend/app/services/users.py` (extract/move logic), `backend/app/services/onboarding.py` (called from provision service)

**Deliverable:** Module imports cleanly — `cd backend && pipenv run python -c "from app.services.keycloak_provisioning import provision_user_from_keycloak"`

---

## P0.2 — Mode A/B status + workspace activation

**What:** Consolidate `resolve_initial_user_status`, `maybe_auto_provision_user`, `activate_user_with_workspace` invocation inside provision service so Mode A verified email returns `active` + membership in same flush; Mode B gates unchanged.

**Files:** `backend/app/services/keycloak_provisioning.py`, `backend/app/services/onboarding.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_onboarding.py -q` — green.

---

## P0.3 — Auth middleware refactor

**What:** `get_current_user` calls `await provision_user_from_keycloak(...)` after JWT decode; remove duplicate orchestration from `auth.py`; keep impersonation + workspace resolution unchanged. **Update** `test_auth_impersonation.py` patch targets from `ensure_user_from_token` / `maybe_auto_provision_user` / `activate_bootstrap_super_admin` → `provision_user_from_keycloak`.

**Files:** `backend/app/core/auth.py`, `backend/app/services/users.py`, `backend/tests/unit/test_auth_impersonation.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_decode_access_token.py tests/unit/test_auth_impersonation.py tests/unit/test_me_routes.py tests/unit/test_users_me.py -q` — green.

---

## P0.4 — Provision error codes

**What:** Raise `UnauthorizedError` / `ConflictError` with `error_code=` on provision service only — **no** `exception_handlers.py` changes (handlers already emit `exc.error_code`).

**Files:** `backend/app/core/exceptions.py`, `backend/app/services/keycloak_provisioning.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_exception_handlers.py -q` — green.

---

## P0.5 — Unit tests (provision service)

**What:** New `test_keycloak_provisioning.py` — Mode A auto workspace; Mode B `pending_profile`/`pending_approval`; bootstrap link by email; missing email; email conflict cross-sub; email update on same sub; idempotent second call same `sub`.

**Files:** `backend/tests/unit/test_keycloak_provisioning.py` (new), adjust `backend/tests/unit/test_users_complete_profile.py` / `test_admin_users.py` if imports shift

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_keycloak_provisioning.py -q` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_keycloak_provisioning.py tests/unit/test_onboarding.py tests/unit/test_decode_access_token.py tests/unit/test_auth_impersonation.py tests/unit/test_me_routes.py tests/unit/test_users_me.py tests/unit/test_users_complete_profile.py tests/unit/test_admin_users.py -q
```

**Next:** [`USER_PROVISIONING_P1_EXECUTION.md`](./USER_PROVISIONING_P1_EXECUTION.md)
