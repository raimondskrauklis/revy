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
| **Review pipeline program (R0–R8)** | [docs/review-pipeline/README.md](docs/review-pipeline/README.md) — R0–R8 + review-quality on `main` |
| **Cursor agent workflow (quick ref)** | [docs/utils/CURSOR_AGENT_WORKFLOW.md](docs/utils/CURSOR_AGENT_WORKFLOW.md) — human / master / Bugbot verbs |
| **Agent orchestration (living)** | [docs/review-pipeline/agents/README.md](docs/review-pipeline/agents/README.md) — LOOP, gates, prompts |
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

## Agent workflow

| Topic | File |
|-------|------|
| **Flow manifest** | [.agent/manifest.json](.agent/manifest.json) — scope: default `backend/**`, add `frontend/**` per program |
| **Skill catalog** | [.agent/skills.catalog.json](.agent/skills.catalog.json) |
| **Review context SSOT** | [.revy/review-context.json](.revy/review-context.json) — Moonshot/Greptile; mirrored to [.agent/review-context.json](.agent/review-context.json) for agent workflow |
| **Orchestration** | [docs/review-pipeline/agents/README.md](docs/review-pipeline/agents/README.md) |
| **Staging validation E2E** | [AGENT_WORKFLOW_PACK_E2E_VALIDATION.md](docs/review-pipeline/staging-validation/AGENT_WORKFLOW_PACK_E2E_VALIDATION.md) |
| **Bugbot (pre-push)** | [.cursor/BUGBOT.md](.cursor/BUGBOT.md) |

## Skills (Revy)

Full installed set: [.agent/manifest.json](.agent/manifest.json) → `skills.installed` · tiers: [.agent/skills.catalog.json](.agent/skills.catalog.json).

| Tier | Skills |
|------|--------|
| **Meta** | `bootstrap-workflow` |
| **Core** | `phase-execution`, `ship-changes`, `chunk-execution` |
| **Planning** | `create-findings`, `create-general-plan`, `create-execution-plan`, `architecture-peer-review`, `execution-peer-review`, `devils-advocate`, `post-finish-gap-pass` |
| **Sentry** | `sentry-fix-issues` |
| **Docs export** | `md-formatting`, `md-docx-export`, `docx-md-export` |
| **Staging validation** | `staging-validation` |

`babysit-pr` is in the catalog but **not installed** — Greptile off (`integrations.greptile: false`). Enable Greptile in manifest first, then install via `bootstrap-workflow` audit.

**Default gate:** local Bugbot before every push. **Revy:** never push while `gh pr checks` shows Revy `pending` / `in_progress` — wait for `pass`/`fail`/`skipping`/`neutral`, then push; wait again after push before the next one. Greptile is optional — enable in `.agent/manifest.json` when user asks.

**PR titles:** `feat(<program-slug>): <what shipped>` — phase labels (`R0`–`R8`) belong on LOOP commits, not as the PR title alone. Update with `gh pr edit` when batched scope grows. Details: `.cursor/skills/ship-changes/SKILL.md`.

Planning skills apply to phased program work under `docs/starter-pack/` or `docs/review-pipeline/`.

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
