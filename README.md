# Revy

AI-assisted code review for GitHub.

**Status:** Active experimental service with a live demo. Single maintainer.
**Live demo:** https://revy.createit.digital/

> *"Beware of bugs; a small defect can sink a great ship."*

Revy connects to GitHub repositories and reviews every pull request through a multi-stage AI pipeline: ingest → index → review → reconcile → judge → publish. It ingests PRs, indexes changed code, runs LLM review, reconciles findings across revisions, judges them for quality, and publishes a `revy/review` check run back to GitHub. The goal is to catch regressions, flag risky patterns, and surface evidence before merge, without replacing human judgment.

## What works today

- **Self-service GitHub App install** from inside the app. Workspace-scoped; one workspace can manage multiple installations.
- **Automatic reviews** on PR open and every push. `@revy review` re-runs on demand. Per-workspace autostart toggle.
- **Context beyond the diff.** Revy indexes the whole file each hunk lives in, not just the hunk, and retrieval pulls in related code from other files so cross-file impact can be checked.
- **Engineering context.** A small manifest in the repo (`.revy/review-context.json`) points at the planning docs for the active work — findings, general plan, execution plan. Revy reads them at the PR's head commit and treats locked decisions as authoritative when reviewing and judging. This is the single biggest quality lever observed so far.
- **Multi-stage LLM review** with standard / deep / critical profiles, a separate judge model, and configurable LLM providers.
- **Finding lifecycle** tracked across pushes: addressed, dismissed, still open. Stale items are closed automatically.
- **GitHub publish**: `revy/review` check run plus review comments on the PR.
- **Free tier**: 25 completed review runs per workspace; failed runs do not count. Paid plan available.
- **Team console**: workspace settings, team management, billing, audit log, reviewer UI. English + Latvian.

## How Revy is built, and why it matters for review quality

Revy reviews its own pull requests. Every feature ships the same way: a findings document (what exists, what is missing, decisions locked), a general plan (phases and goals), and per-phase execution plans; then code, one phase per commit, with the plans committed alongside it. Cursor agents run this loop; the skills that drive it live in [`.cursor/skills/`](.cursor/skills/) and the agent entry point is [`AGENTS.md`](AGENTS.md).

The payoff is that the reviewer is never guessing at intent. The manifest points Revy at the plans, the plans state the decisions, and the review checks the diff against them rather than against generic advice. In daily use on this repository, that combination has made Revy a reviewer worth waiting for, not a bot to dismiss.

## Not yet

- No structural (LSP / call-graph) context; cross-file impact relies on retrieval, not a code graph.
- No incremental re-index; every push re-indexes the changed files.
- No email digests.

## Try it

Open https://revy.createit.digital/ and:

1. Sign up / sign in.
2. Create or join a workspace.
3. Install the Revy GitHub App on a repository.
4. Open a pull request in that repository.
5. Wait for the `revy/review` check to appear and read the findings.

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

See [backend/.env.example](backend/.env.example) and [frontend/.env.example](frontend/.env.example) for required variables.

## Self-hosting

`deploy/` contains sanitized example configs:

- [deploy/env-examples/](deploy/env-examples/) backend and frontend env templates.
- [deploy/keycloak/config/](deploy/keycloak/config/) Keycloak 26 docker-compose and Dockerfile.
- [deploy/nginx/](deploy/nginx/) example vhosts for `app.example.com` and `auth.example.com`.
- [deploy/sql/postgres-extensions.sql](deploy/sql/postgres-extensions.sql) required PostgreSQL extensions.

Replace `example.com` with your domain and fill in real credentials before deploying.

## Contact

- Open a GitHub issue.
- Email: raimonds.krauklis [at] gmail.com

Issues welcome.

## License

[MIT](LICENSE)
