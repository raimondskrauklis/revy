# Revy

AI-assisted code review for GitHub — FastAPI backend + React SPA on the starter-pack platform shell.

## Quick start

1. [Dev bootstrap](docs/starter-pack/DEV_BOOTSTRAP.md) — env, DB, Keycloak, local API + frontend
2. [Keycloak checklist](docs/starter-pack/KEYCLOAK_DEV_CHECKLIST.md)
3. [Agent guide](AGENTS.md) — Cursor rules, skills, doc map

## Repo layout

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI API (`pipenv`, Alembic, `tests/unit/`) |
| `frontend/` | React 19 + Vite SPA |
| `deploy/` | Env examples, SQL snippets |
| `docs/starter-pack/` | Committed scaffold runbooks |
| `internal-docs/` | Full starter-pack + product docs (gitignored) |

## CI

[`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) — lint, build, deploy to DigitalOcean.
