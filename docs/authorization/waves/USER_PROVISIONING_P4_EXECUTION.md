# docs/authorization/waves/USER_PROVISIONING_P4_EXECUTION.md

# P4 — Docs & operator smoke (execution)

Phase **P4** of [`USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md). **P4 only — final phase.**

**Goal:** Committed docs match shipped behaviour; operators can verify KC ↔ PG sync.

**Depends on:** P0, P1, P2, P3 — full e2e smoke requires P2 listener deploy.

## Decisions locked for P4

- Update findings status to **shipped** with program summary.
- FE toasts: `errors.provision_email_required` + `errors.identity_email_conflict` (EN+LV).
- Wire both in **`AuthContext.refetchUser`** via `mapApiError` → `showDomainErrorToast`.
- Sync starter-pack `USER_REGISTRATION.md` in `internal-docs` (manual — gitignored).
- Smoke matrix **tiered:** (A) curl POST webhook → PG row; (B) P2 dev Google → webhook → PG → SPA `active`.
- No `changelog.json` — internal platform change.

## Out of scope for P4

- In-app user admin directory
- KC password/MFA UI

---

## P4.1 — Authorization docs closeout

**What:** Update `USER_PROVISIONING_FINDINGS.md` (status shipped); webhook + JIT diagram in `docs/authorization/README.md`; fix stale `SCAFFOLD_FINDINGS.md` registration row.

**Files:** `docs/authorization/USER_PROVISIONING_FINDINGS.md`, `docs/authorization/README.md`, `docs/starter-pack/SCAFFOLD_FINDINGS.md`

**Deliverable:** Findings reflects unified provision + webhook.

---

## P4.2 — Operator runbooks (webhook + Google smoke)

**What:** `KEYCLOAK_DEV_CHECKLIST.md` — Google IdP (Trust email, email scope), **realm email-as-username**, tiered smoke; `REGISTRATION_FLAGS.md` — drop stale Mode A note if P0 fixed; `DEV_BOOTSTRAP.md` — cross-link only.

**Files:** `docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md`, `docs/starter-pack/REGISTRATION_FLAGS.md`, `docs/starter-pack/DEV_BOOTSTRAP.md`

**Deliverable:** Smoke table with tiers A + B.

---

## P4.3 — FE provision error toasts

**What:** In `AuthContext.refetchUser`, on `/me` failure: `mapApiError` → `showDomainErrorToast` for `provision_email_required` and `identity_email_conflict`. Add both keys under `errors.*` in EN+LV.

**Files:** `frontend/src/contexts/AuthContext.tsx`, `frontend/src/shared/errors/errorMapper.ts` (if needed), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`, `frontend/src/contexts/AuthContext.test.tsx` (new or extend)

**Deliverable:** `cd frontend && npm test -- --run AuthContext` — green (both error codes).

---

## P4.4 — Doc sync table + waves README

**What:** Mark all waves **done** + sha in [`waves/README.md`](./README.md); update `USER_PROVISIONING_GENERAL_PLAN.md` P4 depends on P0–P2.

| Doc | Change |
|-----|--------|
| `docs/authorization/README.md` | Program status |
| `docs/authorization/waves/README.md` | All phases done + sha |
| `docs/authorization/USER_PROVISIONING_GENERAL_PLAN.md` | P4 depends P0–P2 |
| `docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md` | Tiered smoke |
| `internal-docs/.../USER_REGISTRATION.md` | Webhook + JIT (manual sync) |

**Files:** `docs/authorization/README.md`, `docs/authorization/waves/README.md`, `docs/authorization/USER_PROVISIONING_GENERAL_PLAN.md`

**Deliverable:** README execution table all rows `done (<sha>)`.

---

**Phase gate** (from repo root):

```bash
cd backend && pipenv run lint && pipenv run pytest tests/unit/test_keycloak_provisioning.py tests/unit/test_keycloak_webhook.py tests/unit/test_bootstrap_config.py -q
cd frontend && npm run lint && npm test -- --run AuthContext
```

**Human gate (non-gate):** Tier B smoke from P4.2 after P2 deploy on dev/staging.

**Next:** none — program complete.
