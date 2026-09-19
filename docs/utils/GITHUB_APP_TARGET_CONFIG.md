# GitHub App — target configuration (R0–R8)

**End-state** values for one Revy GitHub App when the review pipeline is complete. Use this to register production/staging once — avoid revisiting permissions each phase.

**Incremental / today-only:** [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md)  
**Description copy-paste:** [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md)

**Authority:** [GITHUB_ONBOARDING_FINDINGS.md](../github-onboarding/GITHUB_ONBOARDING_FINDINGS.md) Q8/Q12, [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md), [REVIEW_PIPELINE_PROGRAM.md](../review-pipeline/REVIEW_PIPELINE_PROGRAM.md), [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md).

---

## Create form — all fields

### General

| Field | Production | Staging / dev |
|-------|------------|---------------|
| **GitHub App name** | `revy` | `revy-staging` / `revy-dev` |
| **Description** | [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md) | same |
| **Homepage URL** | `https://revy.createit.digital` | `http://localhost:5173` |

### Identifying and authorizing users

| Field | Production | Staging / dev | Notes |
|-------|------------|---------------|-------|
| **Callback URL** | `https://revy.createit.digital/api/v1/github/callback` | `http://localhost:8000/api/v1/github/callback` | Public API GET (Q12). Not the SPA. Hops use `GITHUB_OAUTH_PUBLIC_BASE`, not `APP_PUBLIC_URL` (`:5173` locally). |
| **Expire user authorization tokens** | ✓ Checked | ✓ Checked | GitHub default |
| **Request user authorization (OAuth) during installation** | ☐ Unchecked | ☐ Unchecked | Q8 — GitHub forbids this together with a chosen Callback URL |
| **Enable Device Flow** | ☐ Unchecked | ☐ Unchecked | Not used |

### Webhook

| Field | Value |
|-------|-------|
| **Active** | ✓ |
| **Webhook URL** | `https://<api-host>/api/v1/webhooks/github` |
| **Webhook secret** | Generate → `GITHUB_WEBHOOK_SECRET` (same in GitHub + backend env) |

### Post-install

| Field | Production | Staging / dev | Notes |
|-------|------------|---------------|-------|
| **Setup URL** | `https://revy.createit.digital/api/v1/github/setup` | `http://localhost:8000/api/v1/github/setup` | Public API GET (Q12). Live GitHub App dashboard paste is **P4**. |
| **Redirect on update** | ✓ | ✓ | Repo add/remove re-enters Setup URL |

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
| **Contents** | **Read and write** | R1, R3, R6 | Repo sync, clone, index (read); **`resolveReviewThread`** on addressed inline findings (write) |
| **Pull requests** | Read and write | R2, R6 | Ingest PRs (read); post review comments + resolve threads (write) |
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
GITHUB_APP_ID=<numeric app id from app settings About — NOT installation URL>
GITHUB_APP_PRIVATE_KEY_PATH=/mnt/revy_volume/secrets/github-app.pem
GITHUB_WEBHOOK_SECRET=<same as GitHub App webhook secret>
REVY_BOT_LOGIN=<app-slug>[bot]
```

**Installation tokens:** GitHub may return longer `ghs_…` tokens (~520 chars) during its 2026 rollout. Revy mints them per request and does not persist them — no env change. **App JWT** lifetime (`iat` / `exp`) is enforced in code — see [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md) § App JWT.

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
| **Voyage API** (default) | Production / first deploy | `voyage-code-3` @ 1024 (migration `0021`) | `VOYAGE_API_KEY`, `REVY_EMBEDDING_MODEL`, `REVY_EMBEDDING_DIMENSIONS` |
| **Local / HF** (parallel) | Experiments, air-gapped | `jina-embeddings-v2-base-code` (CPU), `nomic-embed-code` (GPU) | `REVY_EMBEDDING_BACKEND=local`, `REVY_HF_CACHE_PATH`, `REVY_LOCAL_EMBEDDING_MODEL` |

**Reranker (future §11.3 stage 3):** `REVY_RERANKER_BACKEND=bge-reranker-v2-m3` (self-hosted) or Voyage rerank API — not required for R3 v1 dense search.

```env
REVY_EMBEDDING_BACKEND=voyage
VOYAGE_API_KEY=
REVY_EMBEDDING_MODEL=voyage-code-3
REVY_EMBEDDING_DIMENSIONS=1024
# REVY_HF_CACHE_PATH=/data/hf-cache
# REVY_LOCAL_EMBEDDING_MODEL=jina-embeddings-v2-base-code
# REVY_RERANKER_BACKEND=bge-reranker-v2-m3
```

### Model providers (LLM)

Live path is **RTU** (`REVY_REVIEWER_PROVIDER=rtu`, `REVY_JUDGE_PROVIDER=rtu`). One origin, one key. Moonshot.ai and direct Anthropic stay in code for switch-back. Bedrock stays optional.

| Role | Model | Transport | Env |
|------|-------|-----------|-----|
| Reviewer standard | `azure_ai/kimi-k2.7-code` | OpenAI `POST /v1/chat/completions` | `REVY_RTU_MODEL_STANDARD` |
| Reviewer deep / critical | `azure_ai/claude-fable-5-1` | OpenAI `POST /v1/chat/completions` | `REVY_RTU_MODEL_DEEP` / `_CRITICAL` |
| Judge | `azure_ai/claude-opus-5` | Anthropic `POST /v1/messages` | `REVY_RTU_MODEL_JUDGE` |

`RTU_API_KEY` is the RTU virtual key (reviewer + judge). Leave `MOONSHOT_API_KEY` and `ANTHROPIC_API_KEY` empty until you switch those providers. Do not set `ANTHROPIC_BASE_URL` or `ANTHROPIC_AUTH_TOKEN` for RTU.

```env
REVY_REVIEWER_PROVIDER=rtu
REVY_JUDGE_PROVIDER=rtu
RTU_API_BASE=https://llm.ai.rtu.lv
RTU_API_KEY=
REVY_RTU_MODEL_STANDARD=azure_ai/kimi-k2.7-code
REVY_RTU_MODEL_DEEP=azure_ai/claude-fable-5-1
REVY_RTU_MODEL_CRITICAL=azure_ai/claude-fable-5-1
REVY_RTU_MODEL_JUDGE=azure_ai/claude-opus-5
REVY_MOONSHOT_MODEL_STANDARD=kimi-k2.7-code
REVY_MOONSHOT_MODEL_DEEP=kimi-k3
REVY_MOONSHOT_MODEL_CRITICAL=kimi-k3
MOONSHOT_API_BASE=https://api.moonshot.ai/v1
MOONSHOT_API_KEY=
ANTHROPIC_API_KEY=
REVY_ANTHROPIC_MODEL=claude-sonnet-5
```

**Bedrock (optional M1):** IAM auth instead of `ANTHROPIC_API_KEY` for judge and/or reviewer.

```env
AWS_REGION=eu-central-1
REVY_JUDGE_PROVIDER=bedrock
REVY_BEDROCK_JUDGE_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0
# REVY_REVIEWER_PROVIDER=bedrock
# REVY_BEDROCK_REVIEWER_MODEL_ID=anthropic.claude-sonnet-4-20250514-v1:0
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
| 1 | **Generate private key** → PEM at `/mnt/revy_volume/secrets/github-app.pem` → `chown 1000:deploy`, `chmod 640` → `GITHUB_APP_PRIVATE_KEY_PATH` |
| 2 | Copy **App ID** (About page) → `GITHUB_APP_ID` — verify with [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md) § Verify on droplet |
| 3 | `alembic upgrade head` on target DB |
| 4 | Deploy API + worker with env above |
| 5 | **Install App** on customer org/account (all repos or selected) — note **installation ID** from settings URL |
| 6 | Link installation from Revy connect wizard (HMAC Setup/Callback). Manual register remains a fallback until P4 live paste. |
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
| **R6** | + Pull requests Write, **Contents Write**, Checks Write; optional **Check run** / **Check suite** | `github_publish` queue; inline thread resolve |
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
| `GET/PATCH` | `/api/v1/workspaces/{id}/model-policy` | JWT (`admin:users`) |
| `GET` | `/api/v1/workspaces/{id}/model-catalog` | JWT (`admin:users`) |
| R2+ | PR / revision APIs | JWT |
| R4+ | Review / findings APIs | JWT |
| R6 | (publish is worker → GitHub API, not inbound) | installation token |

---

## One-page checklist

```text
[ ] App name + description + homepage
[ ] Webhook URL + secret → GITHUB_WEBHOOK_SECRET
[ ] Metadata Read, Contents Read and write
[ ] Pull requests Read and write, Checks Write
[ ] Push, Pull request, Pull request review subscribed
[ ] installation + installation_repositories (automatic — nothing to click)
[ ] Private key on volume → GITHUB_APP_PRIVATE_KEY_PATH
[ ] App ID → GITHUB_APP_ID
[ ] Worker queues: github_events … github_publish … maintenance
[ ] Install on org + register in Revy workspace
[ ] Webhook delivery 200 OK
```
