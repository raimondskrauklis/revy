# Revy

AI-assisted code review for GitHub.

**Live demo:** https://revy.createit.digital/

Revy connects to your GitHub repositories and reviews pull requests with an AI pipeline: ingest PRs, index code changes, run multi-stage LLM review, reconcile findings across revisions, and publish a `revy/review` check run back to GitHub. Findings are grouped, judged for quality, and tracked until they are resolved or dismissed.

> Try it: open https://revy.createit.digital/, sign in with your Keycloak account, install the GitHub App on a repository, and open a pull request.

## What it does

- **GitHub App installation** — workspace-scoped; one workspace can manage multiple installations.
- **PR ingestion** — listens to `pull_request` and `push` webhooks.
- **Code indexing** — chunks changed files and computes embeddings for retrieval context.
- **LLM review** — multi-stage reviewer (standard / deep / critical profiles) with a separate judge model for quality.
- **Finding reconciliation** — groups findings across PR revisions, tracks resolution, and closes stale items.
- **GitHub publish** — posts a `revy/review` check run with review comments.
- **Team console** — React SPA with workspace settings, team management, billing, audit log, and reviewer UI.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, Celery |
| Database | PostgreSQL 17 + pgvector |
| Cache / broker | Redis |
| Auth | Keycloak (OpenID Connect) |
| Frontend | React 19, TypeScript, Vite, Tailwind 4, TanStack Query |
| i18n | English + Latvian |
| Deploy | Docker + GitHub Actions → DigitalOcean (example configs in `deploy/`) |

## Repo layout

```text
backend/        FastAPI API, Alembic migrations, unit tests
frontend/       React SPA
deploy/         Example docker-compose, nginx, env templates, SQL snippets
```

## Local development

1. Copy and fill environment files:

   ```bash
   cp backend/.env.example backend/.env
   cp frontend/.env.example frontend/.env.local
   ```

2. Start dependencies (PostgreSQL with `vector` extension, Redis, Keycloak).
3. From `backend/`:

   ```bash
   pipenv install
   pipenv run alembic upgrade head
   pipenv run uvicorn app.main:app --reload
   ```

4. From `frontend/`:

   ```bash
   npm install
   npm run dev
   ```

See `backend/.env.example` and `frontend/.env.example` for required variables.

## Self-hosting

`deploy/` contains sanitized example configs:

- `deploy/env-examples/` — backend and frontend env templates.
- `deploy/keycloak/config/` — Keycloak 26 docker-compose and Dockerfile.
- `deploy/nginx/` — example vhosts for `app.example.com` and `auth.example.com`.
- `deploy/sql/postgres-extensions.sql` — required PostgreSQL extensions.

Replace `example.com` with your domain and fill in real credentials before deploying.

## Testing the live site

Open https://revy.createit.digital/ and:

1. Sign up / sign in.
2. Create or join a workspace.
3. Install the Revy GitHub App.
4. Open any pull request in a connected repository.
5. Wait for the `revy/review` check to appear and review the findings.

## License

MIT
