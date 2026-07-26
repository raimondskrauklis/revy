# GitHub App — target configuration (R0–R8)

**End-state** values for one Revy GitHub App when the review pipeline is complete. Use this to register production/staging once — avoid revisiting permissions each phase.

**Incremental / today-only:** [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md)  
**Description copy-paste:** [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md)

**Authority:** [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md), [REVIEW_PIPELINE_PROGRAM.md](../review-pipeline/REVIEW_PIPELINE_PROGRAM.md), [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).

---

## Create form — all fields

### General

| Field | Production | Staging / dev |
|-------|------------|---------------|
| **GitHub App name** | `revy` | `revy-staging` / `revy-dev` |
| **Description** | [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md) | same |
| **Homepage URL** | `https://revy.createit.digital` | `http://localhost:5173` |

### Identifying and authorizing users

| Field | Target value | Notes |
|-------|--------------|-------|
| **Callback URL** | `https://revy.createit.digital/settings/integrations/github/callback` | Placeholder until OAuth install UI ships; ignored until then |
| **Expire user authorization tokens** | ✓ Checked | GitHub default |
| **Request user authorization (OAuth) during installation** | ✓ Checked (prod) / ☐ (dev manual register) | Prod: install-from-Revy flow. Dev: unchecked if installing from GitHub UI only |
| **Enable Device Flow** | ☐ Unchecked | Not used |

### Webhook

| Field | Value |
|-------|-------|
| **Active** | ✓ |
| **Webhook URL** | `https://<api-host>/api/v1/webhooks/github` |
| **Webhook secret** | Generate → `GITHUB_WEBHOOK_SECRET` (same in GitHub + backend env) |

### Post-install (when OAuth install ships)

| Field | Value |
|-------|-------|
| **Setup URL** | `https://revy.createit.digital/installations?setup=1` |
| **Redirect on update** | ✓ (repo add/remove on installation) |

Until OAuth install ships: leave **Setup URL** empty; link installations via Revy **Register installation** form.

### Where can this GitHub App be installed?

| Environment | Value |
|-------------|-------|
| Production | **Any account** |
| Personal dev | **Only on this account** |

---

## Repository permissions (target)

Set once at app creation. All other repository permissions stay **No access**.

| Permission | Access | Phase | Purpose |
|------------|--------|-------|---------|
| **Metadata** | Read | R1 | Repo list, installation metadata |
| **Contents** | Read | R1, R3 | Repo sync, clone, index |
| **Pull requests** | Read and write | R2, R6 | Ingest PRs (read); post review comments (write) |
| **Checks** | Write | R6 | Create/update check runs on PRs |
| **Commit statuses** | Read | R6 (optional) | Read CI status for review context |

**Organization permissions:** No access  
**Account permissions:** No access

> **Note:** GitHub App permissions are the **maximum** the app can request. Installation owners still choose repo access at install time.

---

## Subscribe to events (target)

### Automatic — no checkbox

GitHub delivers these to every App. Revy handlers: R0–R2.

| `X-GitHub-Event` | Phase | Revy use |
|------------------|-------|----------|
| `installation` | R0 | `github_installations.status` |
| `installation_repositories` | R1 | `github_repositories` upsert/remove |

Do **not** enable **Installation target** (`installation_target`) — different event, not used.

### Subscribe in form — check these

| Form label | `X-GitHub-Event` | Phase | Revy use |
|------------|------------------|-------|----------|
| **Push** | `push` | R0+ | Re-index / re-review trigger |
| **Pull request** | `pull_request` | R2, R8 | PR + revision ingestion; autostart pipeline |
| **Pull request review** | `pull_request_review` | R2 | Review activity sync |
| **Issue comment** | `issue_comment` | R8 | `@revy review` on-demand pipeline |
| **Check run** | `check_run` | R6 (optional) | External CI check context |
| **Check suite** | `check_suite` | R6 (optional) | External CI suite context |

### Leave unchecked

`Installation target`, `Meta`, `Security advisory`, `Create`, `Delete`, `Fork`, `Public`, `Release`, `Repository`, `Repository dispatch`, `Star`, `Watch`, `Label`, `Commit comment`, `Gollum`, `Workflow dispatch`, `Workflow job`, `Workflow run`, `Issues`, `Deployment`, `Deployment status`, etc.

---

## Backend environment (target)

Droplet: `/mnt/revy_volume/backend/.env` — see `deploy/env-examples/backend.env.production.example`.

### GitHub App (required R0+)

```env
GITHUB_APP_ID=<numeric app id>
GITHUB_APP_PRIVATE_KEY_PATH=/mnt/revy/secrets/github-app.pem
GITHUB_WEBHOOK_SECRET=<same as GitHub App webhook secret>
REVY_BOT_LOGIN=revy[bot]
```

**Installation tokens:** GitHub may return longer `ghs_…` tokens (~520 chars) during its 2026 rollout. Revy uses them as opaque strings and does not persist them — no env change. See [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md) § Installation access tokens.

### Review pipeline data paths (R3+ worker)

```env
REVY_REPOS_ROOT=/data/repos
REVY_WORKTREES_ROOT=/data/worktrees
REVY_HF_CACHE_PATH=/data/hf-cache
```

### Embeddings (R3 indexing)

**Start with API** (shipped R3 v1). **Parallel track:** self-hosted models behind `EmbeddingBackend` — same chunk tables, switch via `REVY_EMBEDDING_BACKEND` when implemented. Authority: `internal-docs/product/revy/docs/architecture.md` §11.3–11.3.1.

| Backend | When | Model (examples) | Required env |
|---------|------|------------------|--------------|
| **Voyage API** (default) | Production / first deploy | `voyage-3-lite` (shipped), eval → `voyage-code-3` | `VOYAGE_API_KEY`, `REVY_EMBEDDING_MODEL`, `REVY_EMBEDDING_DIMENSIONS` |
| **Local / HF** (parallel) | Experiments, air-gapped | `jina-embeddings-v2-base-code` (CPU), `nomic-embed-code` (GPU) | `REVY_EMBEDDING_BACKEND=local`, `REVY_HF_CACHE_PATH`, `REVY_LOCAL_EMBEDDING_MODEL` |

**Reranker (future §11.3 stage 3):** `REVY_RERANKER_BACKEND=bge-reranker-v2-m3` (self-hosted) or Voyage rerank API — not required for R3 v1 dense search.

```env
REVY_EMBEDDING_BACKEND=voyage
VOYAGE_API_KEY=
REVY_EMBEDDING_MODEL=voyage-3-lite
REVY_EMBEDDING_DIMENSIONS=512
# REVY_HF_CACHE_PATH=/data/hf-cache
# REVY_LOCAL_EMBEDDING_MODEL=jina-embeddings-v2-base-code
# REVY_RERANKER_BACKEND=bge-reranker-v2-m3
```

### Model providers (LLM)

**Primary (R4 review):** Moonshot Kimi via OpenAI-compatible API (`https://api.moonshot.ai/v1`).

| Profile | Default model | Env override |
|---------|---------------|--------------|
| Standard | `kimi-k2.7-code` | `REVY_MOONSHOT_MODEL_STANDARD` |
| Deep | `kimi-k3` | `REVY_MOONSHOT_MODEL_DEEP` |
| Critical | `kimi-k3` | `REVY_MOONSHOT_MODEL_CRITICAL` |

**Secondary (R5 judge):** Anthropic Claude — independent-family cross-check / escalation only (not the R4 default reviewer). See `internal-docs/product/revy/docs/architecture.md` §13–14.

```env
REVY_LLM_PROVIDER=moonshot
MOONSHOT_API_KEY=
REVY_MOONSHOT_MODEL_STANDARD=kimi-k2.7-code
REVY_MOONSHOT_MODEL_DEEP=kimi-k3
REVY_MOONSHOT_MODEL_CRITICAL=kimi-k3
ANTHROPIC_API_KEY=
# REVY_ANTHROPIC_MODEL=claude-sonnet-4-20250514
```

### Review SLAs

```env
REVY_DEFAULT_REVIEW_PROFILE=standard
REVY_REVISION_TIMEOUT_STANDARD_SECONDS=900
REVY_REVISION_TIMEOUT_DEEP_SECONDS=1500
REVY_REVISION_TIMEOUT_CRITICAL_SECONDS=1800
```

### Celery worker (v1 single worker)

```bash
pipenv run celery -A app.workers.celery_app worker \
  -Q github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance,default \
  --loglevel=info
```

---

## After app creation

| Step | Action |
|------|--------|
| 1 | **Generate private key** → PEM on volume → `GITHUB_APP_PRIVATE_KEY_PATH` |
| 2 | Copy **App ID** → `GITHUB_APP_ID` |
| 3 | `alembic upgrade head` on target DB |
| 4 | Deploy API + worker with env above |
| 5 | **Install App** on customer org (all repos or selected) |
| 6 | Link installation in Revy workspace (manual register until OAuth UI) |
| 7 | Verify webhook deliveries → **200** on `POST /api/v1/webhooks/github` |
| 8 | Optional: `POST …/sync-repositories` for full repo reconcile |

---

## Phase → capability map

| Phase | GitHub App needs | Revy env / infra |
|-------|------------------|------------------|
| **R0** | Webhook active + secret; `installation` (auto) | `GITHUB_WEBHOOK_SECRET`, Celery `github_events` |
| **R1** | Metadata + Contents Read; `installation_repositories` (auto) | `GITHUB_APP_ID`, private key, `repo_sync` |
| **R2** | Pull requests Read and write (covers ingest); subscribe **Pull request**, **Pull request review** | PR migrations |
| **R3** | (no new GitHub settings) | `VOYAGE_API_KEY`, `REVY_EMBEDDING_*`, `REVY_HF_CACHE_PATH` (local track), `indexing` queue |
| **R4** | (no new GitHub settings) | `MOONSHOT_API_KEY`, Kimi model tiers, `review` queue |
| **R5** | (no new GitHub settings) | `ANTHROPIC_API_KEY` (judge), `reconciliation`, `judge` queues |
| **R6** | + Pull requests Write, Checks Write; optional **Check run** / **Check suite** | `github_publish` queue |
| **R7** | (no new GitHub settings) | Reviewer UI only |

**Recommendation:** Configure permissions and events from this doc at app creation. Phases R3–R5 need no GitHub console changes.

---

## API surface (full product)

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/v1/webhooks/github` | HMAC |
| `GET/POST` | `/api/v1/workspaces/{id}/installations` | JWT |
| `GET` | `/api/v1/workspaces/{id}/installations/{id}/repositories` | JWT |
| `POST` | `/api/v1/workspaces/{id}/installations/{id}/sync-repositories` | JWT (admin) |
| R2+ | PR / revision APIs | JWT |
| R4+ | Review / findings APIs | JWT |
| R6 | (publish is worker → GitHub API, not inbound) | installation token |

---

## One-page checklist

```text
[ ] App name + description + homepage
[ ] Webhook URL + secret → GITHUB_WEBHOOK_SECRET
[ ] Metadata Read, Contents Read
[ ] Pull requests Read and write, Checks Write
[ ] Push, Pull request, Pull request review subscribed
[ ] installation + installation_repositories (automatic — nothing to click)
[ ] Private key on volume → GITHUB_APP_PRIVATE_KEY_PATH
[ ] App ID → GITHUB_APP_ID
[ ] Worker queues: github_events … github_publish … maintenance
[ ] Install on org + register in Revy workspace
[ ] Webhook delivery 200 OK
```
