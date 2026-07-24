# Starter-pack scaffold — findings

Baseline for Revy greenfield platform foundation (starter-pack → repo). **No execution steps.**

**Status:** baseline-ready (peer-reviewed 2026-07-24).

---

## Locked exclusions

**Phases 1–4:** agents must not opportunistically “fix” backend/frontend product gaps listed below.

| Exclusion | Status (2026-07-25) |
|-----------|------------------------|
| **`.cursorrules` / agent entry** | **Resolved (P5)** — `AGENTS.md`, modular `.cursor/rules/`, slim `.cursorrules` |
| **Deploy workflow** | **Resolved early** — `.github/workflows/deploy.yml` is Revy-branded; tests gated by `SKIP_CI_TESTS` |
| **Root `README`** | **Resolved (P5)** — minimal contributor entry |
| **Backend platform completeness** | Phases 2–3 scope — registration, invitations, idempotency routes, etc. |
| **Frontend product completeness** | Phase 4+ — review pipeline UI beyond starter-pack shell |

**Related (deferred):** production droplet runtime tuning; Keycloak realm automation; flip `SKIP_CI_TESTS` when CI secrets ready.

---

## Build principles

- **Starter-pack is source of patterns** — copy/align templates in `internal-docs/starter-pack/templates/`; product overlay in `internal-docs/product/revy/`.
- **Hand-written Alembic only** — no `--autogenerate`; KP-style revision ids `YYYY_MM_DD_HHMM_NNNN_slug`.
- **Fail-fast config** — required env in `Settings`; URLs/secrets not hardcoded in code (`CONFIG.md`).
- **Async SQLAlchemy 2.0 `Mapped`** — `TimestampedModel` / `AuditableModel`; enums in `app/constants/enums.py`, `snake_case` values.
- **Tests in `tests/unit/` only** — no new `tests/api/` or `tests/service/`.
- **Fix shared infra once** — template + Revy + starter-pack docs stay in sync when core patterns change.
- **No misleading UI** — routes/gates that imply backend flows must have matching APIs (called out as gaps below).

---

## Terminology

| Term | Meaning |
|------|---------|
| **starter-pack** | Generic SaaS template under `internal-docs/starter-pack/` |
| **product overlay** | Revy-specific docs/env under `internal-docs/product/revy/` |
| **scaffold** | P0 identity + **P1 items demo** migration — not Revy review domain |
| **invitations migration** | Future Alembic revision for `workspace_invitations` — **not** `0002_p1_items` (naming trap) |
| **`ENVIRONMENT`** | `development` \| `staging` \| `production` \| `test` — **not** `local` |
| **`--app-*`** | Frontend design tokens (starter-pack); Revy brand via `tokens.revy.css` (`--rv-*` on `--app-*`) |

---

## What exists vs genuinely new

### Verified — in repo

| Layer | What | Evidence |
|-------|------|----------|
| Backend app | FastAPI factory, health, auth/JWKS, permissions, pagination, email, Celery skeleton, idempotency module | `backend/app/main.py`, `backend/app/core/*`, ~78 Python files under `backend/` |
| Backend API | `/api/v1/me`, `/items`, workspaces invitations stub, invitations accept stub | `backend/app/api/v1/` |
| Backend DB | P0 users/workspaces/memberships + P1 items migrations | `backend/alembic/versions/2026_07_23_2315_0001_*.py`, `0002_*.py` |
| Backend config | Revy fields (GitHub App, model keys, `revy_*` paths) + wired `LOG_*`, `registration_*`, `SECRET_KEY` fingerprint, `keycloak_frontend_client_id` | `backend/app/core/config.py`, `security.py`, `logging.py`, `auth.py` |
| Backend tests | 43 unit tests | `pipenv run pytest tests/unit/` |
| Test seed stub | `seed_test_data.py` no-op (CI placeholder) | `backend/scripts/seed_test_data.py` |
| Frontend | Full starter-pack SPA (auth, routing, Quiet*, i18n EN/LV, settings demo) | `frontend/src/**` (~67 files) |
| Frontend brand | `tokens.revy.css` imported after `tokens.css` | `frontend/src/index.css` |
| Frontend tests | 7 unit tests; lint/build pass | `frontend/package.json` scripts |
| Deploy hints | `deploy/env-examples/`, `deploy/sql/postgres-extensions.sql` | repo root `deploy/` |
| Env canon | `backend/.env.example`, `frontend/.env.example` | verified |

### Verified — starter-pack templates synced (recent)

Revy changes flowed back to `internal-docs/starter-pack/templates/backend/` for: `logging.py`, `security.py`, `auth.py`, `onboarding.py`, `users.py`, `database.py`, `idempotency.py`, `config.py`, `sentry.py`, tests; docs `CONFIG.md`, `AUTH.md`, `IDEMPOTENCY.md`; env examples.

### Genuinely new (Revy, not in starter-pack)

- `backend/app/core/config.py` — GitHub App, Moonshot/Anthropic/Voyage, `revy_*` paths, review timeouts.
- `deploy/env-examples/*` — Revy production templates.
- `frontend/src/styles/tokens.revy.css` — brand overlay.

### Reuse caveats / traps

| Trap | Detail |
|------|--------|
| **KP `.cursorrules`** | **Resolved (P5)** — `AGENTS.md` + modular `--app-*` rules. |
| **`.github/workflows/deploy.yml`** | **Resolved** — Revy-branded; `SKIP_CI_TESTS` until secrets ready. |
| **`legacy backend/.env`** | KP Keycloak (`kp-platform`), `FRONTEND_BASE_URL`, storage/mailgun keys — re-baseline in **P1** before smoke; full prune in **P3.5** before dropping `extra="ignore"`. |
| **`Settings.extra = "ignore"`** | Masks orphan keys in `backend/.env` — remove in P3.5 after env matches `Settings` / `.env.example`. |
| **JWT audience** | Strict allowlist (`revy-api`, `revy-web`) — Keycloak mappers must match or login fails. |
| **`pgcrypto` vs deploy SQL** | P0 migration creates `uuid_generate_v7()` via `pgcrypto`; `deploy/sql/postgres-extensions.sql` lists `vector`, `uuid-ossp`, `pg_trgm` only — run **both** on DO. |
| **Auth `session.commit()` in `get_current_user`** | Provisioning side-effect on every authenticated request — works but complicates transaction boundaries. |
| **JsonFormatter** | `logger.info(..., extra={})` fields not merged into JSON output — ops context lost. |
| **Items slice** | Demo CRUD only — pattern reference, not Revy product. Alembic `0002_p1_items` = **items**, not invitations. |
| **P1 label collision** | Code/comments in `invitations.py`, `enums.py` say “P1 migration” for `workspace_invitations` — misleading; Alembic P1 is items (`0002_p1_items.py`). |
| **Dual registration config** | Backend `REGISTRATION_REQUIRE_*` + frontend `VITE_REGISTRATION_REQUIRE_*` — must be **manually paired**; mismatch looks like a bug (Mode B BE + Mode A FE). |
| **Platform vs workspace admin** | `/admin/users` = **platform** signup queue (`super_admin` only). `admin:users` = **workspace** member invites (P3). FE route still uses `admin:users` — **fix in P2** (locked in execution). |
| **`billing` scaffold** | `app/services/billing.py` + schemas exist; no API routes — starter-pack carryover; optional Phase 3 cleanup. |
| **KP `deploy.yml` landmine** | Still runs `scripts.seed_test_data` when tests enabled; stub is no-op — **do not flip `SKIP_CI_TESTS`** until P5 `ci.yml` replaces KP CI. |

---

## Catalog — capabilities vs completeness

| Capability | Starter-pack spec | Revy repo state |
|----------|-------------------|-----------------|
| Keycloak JWT auth | `AUTH.md` | **Verified** — decode + allowlist |
| User bootstrap / super_admin | `BOOTSTRAP_SUPER_ADMIN.md` | **Verified** — seed script + activation |
| Open registration (Mode A) | `USER_REGISTRATION.md` | **Partial** — auto-provision in `get_current_user`; no `complete-profile` API; FE gates are `StatusGatePage` placeholders only |
| Admin approval (Mode B) | `USER_REGISTRATION.md` | **Missing** — `/admin/users` placeholder (`admin.users.placeholder`); no admin APIs |
| Invitations | `INVITATIONS.md` | **Stub** — no `workspace_invitations` migration |
| Idempotency | `IDEMPOTENCY.md` | **Module only** — not wired to routers |
| Email | `EMAIL.md` | **Verified** — console + Mailgun providers |
| Cursor lists / items | `AGENT_PATTERNS.md` | **Verified** — items slice |
| Celery | generic queues | **Revy queue map** — `github_events` routes wired (P4); task modules stub |
| `github_installation` | TENANCY.md | **Verified** — migration, API, dashboard UI (P4) |
| Frontend status gates | `ProtectedRoute.tsx` | **Verified** — `VITE_REGISTRATION_*`; routes render informational `StatusGatePage`, not forms/admin queue |
| Migrations applied | — | **Assumption** — files exist; DO apply not verified in CI |

---

## Advice / options

| Topic | Recommendation | Defer/reject |
|-------|----------------|--------------|
| In-repo `AGENTS.md` | Adopt starter-pack `AGENTS.md` + Revy overlay section | **Defer** (user) |
| Replace `.cursorrules` | Short pointer + modular rules like starter-pack | **Defer** (user) |
| CI/CD workflow | New minimal Revy `ci.yml`; retire KP `deploy.yml` when ready | **Defer** (user) |
| `internal-docs/` wiring | Point `.cursorrules` / `AGENTS.md` at `internal-docs/product/revy/` when rules updated | **Defer** |
| Registration next | Backend APIs before more Revy domain work | **Adopt** (priority 2 in platform review) |
| Items demo | Keep until first Revy resource replaces it | **Adopt** |

---

## Data scope & exclusions

**In scope for this program:** platform shell (auth, tenancy, users, workspaces, starter UI, env, migrations scaffold).

**Explicitly out of scope (this program):** see [Locked exclusions](#locked-exclusions) plus:
- Revy domain (repos, PR reviews, findings, embeddings, GitHub webhooks).
- Keycloak realm provisioning automation.
- Production droplet runtime.

**Excluded from verification:** live DO database state, Keycloak realm config, production deploy.

---

## Edge cases

1. **Keycloak `aud: account`** — browser tokens may not include `revy-api` in `aud`; `azp` check is critical.
2. **Email verified lag** — user row `pending_email_verification` until KC confirms; status transition on next `/me`.
3. **Multi-workspace** — `X-Workspace-Id` required when >1 membership; single membership auto-selected.
4. **Bootstrap email** — must match Keycloak registration; placeholder `keycloak_user_id` until first login.
5. **DO managed PG** — extensions and migrations are operator-run, not docker-compose. Target **PostgreSQL 17** per `deploy/sql/postgres-extensions.sql` header (not “16+” generically).
6. **`pending_profile` + Mode A** — `resolve_initial_user_status` may return `pending_profile` even when both `REGISTRATION_REQUIRE_*` are false; `maybe_auto_provision_user` activates on same auth request. FE does not gate on `pending_profile` when `VITE_REGISTRATION_REQUIRE_PROFILE_FORM=false`. If auto-provision fails/skips, user could reach dashboard while `/me` still shows `pending_profile`.
7. **Registration env pairing** — document Mode A/B matrix (`REGISTRATION_*` ↔ `VITE_REGISTRATION_*`) in Phase 1 checklist; gate in Phase 2.

---

## Decisions registry

| Q# | Question | Status | Resolution |
|----|----------|--------|------------|
| Q1 | `ENVIRONMENT` value for dev | **locked** | `development` (not `local`) |
| Q2 | Canonical backend env template | **locked** | `backend/.env.example` only |
| Q3 | Public URL for emails | **locked** | `APP_PUBLIC_URL`; no `FRONTEND_BASE_URL` |
| Q4 | Frontend tokens | **locked** | `--app-*` + `tokens.revy.css` |
| Q5 | Postgres for dev | **locked** | DO managed (no local PG container) |
| Q6 | Redis local | **locked** | `backend/docker-compose.yml` Redis only |
| Q7 | Cursor rules / deploy workflow | **locked** | Leave as-is for now |
| Q8 | Root `AGENTS.md` / `README` | **locked** | Defer |
| Q9 | Plan docs location | **locked** | `docs/starter-pack/` in repo; product context in `internal-docs/` |
| Q10 | Template sync policy | **locked** | Core pattern changes → update `internal-docs/starter-pack/templates/` |
| Q11 | `extra="ignore"` on Settings | **open** | Remove in P3.5 after `backend/.env` pruned to `Settings` / `.env.example` only |
| Q12 | Phase 4 product spec source | **locked** | Redacted slice in `docs/starter-pack/REVY_PRODUCT_SLICE.md` before P4.2 (author from `internal-docs/product/revy/docs/`) |
| Q13 | Phase 1 E2E verification | **locked** | In-repo checklist in `DEV_BOOTSTRAP.md`; manual operator Keycloak smoke; not CI until Phase 5 |
| Q14 | Phase 2 frontend scope | **locked** | Profile form + admin pending queue UI (replace placeholders); not API-only |

---

## Parking lot (Phase-0 prerequisites for later waves)

- Clean `backend/.env` (prune to `Settings` / `.env.example` only); drop `extra="ignore"` in P3.5.
- Apply `deploy/sql/postgres-extensions.sql` + `alembic upgrade head` on DO dev DB.
- Keycloak smoke test (real token → `/api/v1/me`).
- Registration APIs (`complete-profile`, admin approve/reject).
- `workspace_invitations` migration + wire services.
- Wire idempotency on `POST` mutations.
- JsonFormatter `extra` merge.
- Wire `tests/conftest.py` fixtures + `ENVIRONMENT=test` bootstrap (file exists as commented stub).
- Fix invitations “P1 migration” comments when adding **invitations migration** (distinct from `0002_p1_items`).
- Registration flag matrix doc (`REGISTRATION_*` ↔ `VITE_REGISTRATION_*`).
- Optional: remove orphan `billing` service/schemas or document as carryover.
- Extend `seed_test_data.py` when integration fixtures are needed (no-op stub exists).
- Revy Celery queue map.
- Replace KP `.cursorrules` / add `AGENTS.md`.
- Revy CI workflow (**new** `ci.yml` — do not enable tests in KP `deploy.yml`).

---

## Devil's advocate

- **Facade platform:** FE registration/admin routes without APIs → false sense of completeness.
- **Agent confusion (mitigated P5):** was KP `.cursorrules` vs Revy code — now `AGENTS.md` + `--app-*` rules.
- **Skipped CI:** regressions until minimal workflow exists.
- **Auth commit in dependency:** subtle bugs when routes expect rollback semantics.
- **internal-docs gitignored:** new contributors without internal-docs see incomplete picture unless `docs/starter-pack/` is kept current.

---

## Experiment / verification

| Check | Pass criteria |
|-------|----------------|
| Backend unit | `cd backend && pipenv run test` — 43 passed |
| Frontend unit + build | `cd frontend && npm test && npm run build` — green |
| Lint | `pipenv run lint`, `npm run lint` — green |
| Migration SQL | P0+P1 apply cleanly on empty **PG 17** (DO dev) with `pgcrypto` + `postgres-extensions.sql` |
| Keycloak E2E | New user → JWT → `GET /api/v1/me` → `status: active` (Mode A); registration flags paired BE↔FE |
| Registration Mode B | User stops at `pending_approval` until admin approve API |

---

## References

| Path | Role |
|------|------|
| `internal-docs/starter-pack/AGENTS.md` | Starter-pack agent entry |
| `internal-docs/starter-pack/docs/CROSS_CUTTING.md` | Cross-cutting inventory |
| `internal-docs/product/revy/README.md` | Product overlay |
| `backend/.env.example` | Revy backend env canon |
| `deploy/env-examples/README.md` | Deploy env index |
| `backend/app/main.py` | App entry |
| `frontend/src/lib/routerInstance.tsx` | FE routes |
| `backend/app/api/v1/workspaces/invitations.py` | Invitations stub (“P1 migration” comment — misleading) |
| `backend/app/services/billing.py` | Orphan scaffold (no routes) |
| `frontend/src/features/auth/pages/StatusGatePage.tsx` | Placeholder status pages (not forms) |
| `frontend/src/features/admin/pages/AdminUsersPage.tsx` | Admin placeholder |
| `.github/workflows/deploy.yml` | KP pipeline; runs no-op `seed_test_data` if `SKIP_CI_TESTS` disabled |
| `backend/scripts/seed_test_data.py` | No-op stub — extend when integration fixtures needed |
| `.cursorrules` | **Stale (KP)** — do not trust for Revy |

---

## Peer review (2026-07-24)

**Verdict:** Findings and general plan match repo; Phase 0 **Complete** is fair. Gaps are sequencing, naming collisions, and underspecified Phase 2/4 scope — not wrong baseline facts.

**Accepted fixes (this revision):** P1 vs invitations naming; dual registration config; FE placeholder scope; `pending_profile` edge case; conftest wording; PG 17 target; `billing` carryover; `deploy.yml` / `seed_test_data` landmine; Q12–Q14 locked; execution plans P0–P5 in `docs/starter-pack/`.

**Expect through Phases 1–4:** KP `.cursorrules` will mislead agents until Phase 5 — acceptable given locked exclusion.

**Execution peer-review (2026-07-24):** P2 platform-admin fix applied; P1/P3/P4/P5 medium items incorporated; P0 retrospective nits and P1 `npm run build` omission **declined** (doc-only phase). P5: audit KP rules selectively — keep `sentry-mcp.mdc`, do not blanket-delete `.cursor/rules/`. **Second pass:** P1 legacy `.env` re-baseline; P2 admin router mount; P3/P4 `models/__init__.py`; P3.5 full env prune + idempotency body-read note.

**Final pass (2026-07-24):** Execution files P0–P5 updated; findings/general plan synced (`seed_test_data` stub, Q11 prune wording). **BLOCK cleared** — safe for `phase-execution` from P1.
