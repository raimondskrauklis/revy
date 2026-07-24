# Starter-pack scaffold — general plan

Phased goals from [SCAFFOLD_FINDINGS.md](./SCAFFOLD_FINDINGS.md). **No file lists or steps** — use `create-execution-plan` per phase.

**Cross-cutting (every phase):** unit tests for touched logic; starter-pack template sync when core patterns change; EN+LV for any new user-facing strings; no autogenerate migrations.

**Locked exclusions** (from findings):

| Item | Status |
|------|--------|
| `.cursorrules` / `AGENTS.md` / root `README` | Done (P5, 2026-07-25) |
| `.github/workflows/deploy.yml` | Revy-branded; tests via `SKIP_CI_TESTS` |
| Backend platform completeness (registration APIs, invitations, idempotency wire, …) | Phases 2–3 |
| Frontend product completeness (Revy UI beyond starter-pack SPA) | Phase 4+ |

---

## Phase 0 — Scaffold baseline

**Goal:** Starter-pack backend + frontend shell in repo with aligned config and hand-written P0/P1 migrations.

**Scope:** In — template copy, Revy config overlay, env examples, deploy SQL snippet, config/logging/auth/onboarding wiring, template doc sync. Out — Revy domain, Keycloak automation, CI.

**Deliverables:** Runnable app skeleton; `backend/.env.example` + `frontend/.env.example`; Alembic P0/P1 files; 43 backend + 7 frontend unit tests green; findings + this plan in `docs/starter-pack/`.

**Depends on:** —

**Status:** **Complete** (2026-07-23).

---

## Phase 1 — Runnable dev platform

**Goal:** A developer can sign in via Keycloak on DO dev DB and reach `active` + dashboard (Mode A).

**Scope:** In — operator runbook (`postgres-extensions.sql` + migration `pgcrypto`, Keycloak client/audience checklist, optional `seed_bootstrap_super_admin.py`); **re-baseline legacy `backend/.env`** (KP → Revy Keycloak) per P1; registration flag pairing doc (`REGISTRATION_*` ↔ `VITE_REGISTRATION_*`); manual Keycloak → `GET /api/v1/me` → `active` smoke. Out — Mode B admin UI/API; invitations; CI.

**Deliverables:** In-repo dev bootstrap checklist (extensions → migrate → KC user); verified JWT audience; `ENVIRONMENT=development` end-to-end; Mode A flag matrix documented.

**Depends on:** Phase 0.

**Execution notes:** E2E = in-repo `DEV_BOOTSTRAP.md` checklist + manual operator smoke (Q13); not CI until Phase 5.

---

## Phase 2 — Registration & platform flows

**Goal:** Frontend status gates and pages match real backend registration flows (USER_REGISTRATION.md).

**Scope:** In — **backend:** `complete-profile`, admin pending/approve/reject APIs, service tests, Mode A/B branches. **Frontend:** replace `StatusGatePage` placeholders with profile form where required; `/admin/users` pending list + approve/reject actions (not `admin.users.placeholder`). Out — Revy review domain; billing routes.

**Deliverables:** Mode A and Mode B paths testable end-to-end; registration flags paired BE↔FE (gate); no orphan routes or API-only facades.

**Depends on:** Phase 1.

---

## Phase 3 — Shared platform hardening

**Goal:** Close starter-pack gaps that affect every future feature.

**Scope:** In — **invitations migration** (label distinct from `0002_p1_items`) + wire services; fix misleading “P1 migration” comments; idempotency on `POST`; JsonFormatter `extra` merge; wire `tests/conftest.py` fixtures + `ENVIRONMENT=test`; remove `Settings.extra="ignore"`; drop `models/_example_product_item.py.example` if unused; optional `billing` cleanup. Out — Celery Revy queues (unless email path blocked).

**Deliverables:** Invitations accept/create backed by DB; idempotency live; structured logs carry `operation` / `entity_id`; integration test bootstrap ready.

**Depends on:** Phase 2.

---

## Phase 4 — Revy product foundation

**Goal:** First Revy domain vertical on platform rails (not items demo).

**Scope:** In — product models/migrations/services/APIs per **`docs/starter-pack/REVY_PRODUCT_SLICE.md`** (redacted from `internal-docs/product/revy/docs/` — authored in P4.1); Celery queue map from `implementation.revy.md`; replace or sideline items demo. Out — full review pipeline, pgvector RAG.

**Deliverables:** One end-to-end Revy resource CRUD/list with tenancy; workers routable to Revy queues; committed docs sufficient for repo-only contributors.

**Depends on:** Phase 3.

---

## Phase 5 — Agent & cursor identity

**Goal:** Agents and contributor docs match Revy, not KP.

**Scope:** In — root `AGENTS.md`, slim `.cursorrules`, modular `.cursor/rules/` (`--app-*`), remove KP corpus/deep-investigation rules & skills, minimal `README.md`. Out — new `ci.yml` (deploy workflow already Revy); full production deploy redesign.

**Deliverables:** Agent entry points in repo; no misleading KP domain in Cursor context.

**Status:** **Done** (2026-07-25).

---

## Remaining open item

**Q11:** Remove `Settings.extra = "ignore"` in Phase 3 (P3.5) after `backend/.env` is pruned to `Settings` / `.env.example` keys only.

**Next step:** `phase-execution` from [SCAFFOLD_P1_EXECUTION.md](./SCAFFOLD_P1_EXECUTION.md).
