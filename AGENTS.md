# Agent guide — Revy

Entry point for AI agents working in this repo.

**Product:** Revy — AI-assisted code review on GitHub (starter-pack SaaS shell + Revy domain slice).

## Read first

| Topic | Where |
|-------|--------|
| **Dev bootstrap** | [docs/starter-pack/DEV_BOOTSTRAP.md](docs/starter-pack/DEV_BOOTSTRAP.md) |
| **Keycloak (dev/prod)** | [docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md](docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md) |
| **Registration flags** | [docs/starter-pack/REGISTRATION_FLAGS.md](docs/starter-pack/REGISTRATION_FLAGS.md) |
| **Revy product slice (P4)** | [docs/starter-pack/REVY_PRODUCT_SLICE.md](docs/starter-pack/REVY_PRODUCT_SLICE.md) |
| **SaaS base program (W0–W8)** | [docs/saas-base/README.md](docs/saas-base/README.md) — tag `saas-base-v1` |
| **Review pipeline program (R0–R7)** | [docs/review-pipeline/README.md](docs/review-pipeline/README.md) — R0–R3 on `main`; R4–R7 PR stack [#24](https://github.com/raimondskrauklis/revy/pull/24)–[#27](https://github.com/raimondskrauklis/revy/pull/27) |
| **SaaS ops / staging** | [STAGING_VERIFICATION.md](docs/saas-base/STAGING_VERIFICATION.md), [OPS.md](docs/saas-base/OPS.md) |
| **Stripe billing setup** | [docs/utils/STRIPE_BILLING_SETUP.md](docs/utils/STRIPE_BILLING_SETUP.md) |
| **Scaffold program status** | [docs/starter-pack/README.md](docs/starter-pack/README.md) |
| **Product context (full)** | `internal-docs/product/revy/docs/PLATFORM_CONTEXT.md` |
| **Architecture (full)** | `internal-docs/product/revy/docs/architecture.md` |
| **Starter-pack backend patterns** | `internal-docs/starter-pack/docs/backend/AGENT_PATTERNS.md` |
| **Starter-pack frontend drift** | `internal-docs/starter-pack/docs/frontend/patterns/AGENT_DRIFT.md` |
| **Auth / JWKS** | `internal-docs/starter-pack/docs/backend/AUTH.md` |
| **Deploy (Revy)** | `internal-docs/starter-pack/deploy/docs/implementation.md` + `internal-docs/product/revy/deploy/docs/implementation.revy.md` |
| **Env examples** | `deploy/env-examples/`, `backend/.env.example`, `frontend/.env.example` |

`internal-docs/` is gitignored — available to contributors with repo access.

## Cursor rules (modular)

| Rule | Scope |
|------|--------|
| `.cursor/rules/00-core.mdc` | Always |
| `.cursor/rules/backend-python.mdc` | `backend/**` |
| `.cursor/rules/frontend-react.mdc` | `frontend/**` |
| `.cursor/rules/app-color-tokens.mdc` | `frontend/**/*.{tsx,ts,css}` |
| `.cursor/rules/app-i18n.mdc` | `frontend/**` |
| `.cursor/rules/testing.mdc` | tests |
| `.cursor/rules/sentry-mcp.mdc` | Sentry MCP — manual only |

Root [`.cursorrules`](.cursorrules) is a short pointer.

## Skills (Revy)

| Skill | When |
|-------|------|
| `ship-changes` | Ship: branch, commit, push, PR |
| `sentry-fix-issues` | User points at one Sentry issue URL/ID |
| `phase-execution` | Full scaffold execution LOOP from `docs/starter-pack/SCAFFOLD_P*_EXECUTION.md` |
| `chunk-execution` | One scaffold subphase only |
| `babysit-pr` | Triage/fix Greptile review comments on an open PR |

Scaffold planning skills (`create-findings`, `create-general-plan`, `create-execution-plan`, peer-review, `devils-advocate`, `post-finish-gap-pass`) apply to `docs/starter-pack/` program work only.

## Backend quick ref

- Stack: Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, PostgreSQL, Celery.
- Errors: `app.core.exceptions` — never bare `HTTPException`.
- Auth: Keycloak JWT + async JWKS cache — `app/core/auth.py`, `app/core/jwks.py`.
- Lists: cursor pagination (`CursorParams`, `CursorResponse`).
- ORM: `*ORM` suffix, enums in `app/constants/enums.py` (`snake_case` values).
- Migrations: hand-written Alembic — **never** `--autogenerate`.
- Tests: `backend/tests/unit/` only.
- Run from `backend/`: `pipenv run lint`, `pipenv run pytest tests/unit/`.

## Frontend quick ref

- Stack: React 19, TypeScript strict, Vite, Tailwind 4, TanStack Query, Zustand (UI only).
- Tokens: `--app-*` in feature code; Revy brand via `frontend/src/styles/tokens.revy.css`.
- i18n: `t()` — EN + LV (`frontend/src/i18n/`).
- Dates/numbers: `@/lib/date`, `@/lib/locale`, `@/lib/number`.
- Inputs: `QuietInput`, `QuietSelect`, `QuietDateInput` from `@/components/ui/`.
- Errors: `mapApiError()` → `showDomainErrorToast()` (`@/shared/errors`).
- Run from `frontend/`: `npm run lint`, `npm test`, `npm run build`.

## First commands

See [DEV_BOOTSTRAP.md](docs/starter-pack/DEV_BOOTSTRAP.md).

```bash
# Backend (from backend/)
pipenv install && pipenv run uvicorn app.main:app --reload

# Frontend (from frontend/)
npm install && npm run dev
```

## CI / deploy

PR + main: [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) (`CI/CD - Revy`). Set `SKIP_CI_TESTS: "false"` when Actions secrets are ready.

## Sentry MCP

Config: `.cursor/mcp.json` → `https://mcp.sentry.dev/mcp/kp-platform`. Manual debugging only — see `@sentry-fix-issues` skill.
