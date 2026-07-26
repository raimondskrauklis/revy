# GitHub webhook — local development (R0)

How to receive GitHub App webhooks against a local Revy API. Production uses the same path with HTTPS.

**Endpoint:** `POST /api/v1/webhooks/github`  
**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`

---

## Prerequisites

1. Migrations through `0010_github_webhook_deliveries`:

   ```bash
   cd backend
   pipenv run alembic upgrade head
   pipenv run alembic current
   ```

2. `backend/.env`:

   ```text
   GITHUB_WEBHOOK_SECRET=local-webhook-secret
   ```

   Must match the secret configured on the GitHub App or forwarding tool.

3. API running: `pipenv run uvicorn app.main:app --reload --port 8000`

4. Celery worker on `github_events` (optional for async handlers):

   ```bash
   pipenv run celery -A app.workers.celery_app worker -Q github_events,default --loglevel=info
   ```

---

## Option A — smee.io (recommended)

1. Open https://smee.io and create a channel.
2. Set the channel URL as the **Webhook URL** on your GitHub App (or org webhook for testing).
3. Forward to local API:

   ```bash
   npx smee -u https://smee.io/<your-channel> -t http://localhost:8000/api/v1/webhooks/github
   ```

4. Trigger an event from GitHub (e.g. reinstall app or push to a repo) and confirm API logs **200**.

`installation` and `installation_repositories` are sent automatically — no subscribe checkbox. For a repo event, subscribe **Push** on the GitHub App and push a commit.

---

## Option B — GitHub CLI forward

If using `gh` with a registered webhook:

```bash
gh webhook forward --url=http://localhost:8000/api/v1/webhooks/github --events=installation,push
```

Align `GITHUB_WEBHOOK_SECRET` with the secret shown by `gh`.

---

## Manual curl (signature check)

```bash
SECRET=local-webhook-secret
BODY='{"action":"created","installation":{"id":12345}}'
SIG="sha256=$(printf '%s' "$BODY" | openssl dgst -sha256 -hmac "$SECRET" | awk '{print $2}')"

curl -sS -X POST http://localhost:8000/api/v1/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: installation" \
  -H "X-GitHub-Delivery: $(uuidgen)" \
  -H "X-Hub-Signature-256: $SIG" \
  -d "$BODY"
```

Expect HTTP **200**. Duplicate `X-GitHub-Delivery` → **200** without re-enqueue.

---

## Verify persistence

```sql
SELECT delivery_id, event_type, installation_id FROM github_webhook_deliveries ORDER BY received_at DESC LIMIT 5;
```

---

## Troubleshooting

| Symptom | Cause |
|---------|--------|
| `503 github_webhooks_disabled` | Empty `GITHUB_WEBHOOK_SECRET` |
| `422` invalid signature | Secret mismatch between GitHub/smee and `.env` |
| `200` but no status change | Installation id not registered in `github_installations` (orphan — expected until dev register) |
| Task not running | Celery worker not consuming `github_events` |
| Repos not listed | `installation_repositories` webhook or manual sync — see § Repository sync (R1) |

---

## Repository sync (R1)

Webhook `installation_repositories` upserts rows in `github_repositories`. For a full reconcile from GitHub API:

1. Set `GITHUB_APP_ID` and `GITHUB_APP_PRIVATE_KEY_PATH` in `backend/.env`
2. Run Celery worker with `repo_sync` queue: `-Q github_events,repo_sync,…`
3. `POST /api/v1/workspaces/{workspace_id}/installations/{installation_id}/sync-repositories` (workspace admin)

List: `GET …/installations/{installation_id}/repositories`

---

## Pull request ingestion (R2)

Subscribe **Pull request** and **Pull request review** on the GitHub App ([GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md)).

Verify after an `opened` delivery:

```sql
SELECT id, number, title, revision_count FROM github_pull_requests ORDER BY created_at DESC LIMIT 5;
SELECT pull_request_id, revision_number, head_sha FROM github_pull_request_revisions ORDER BY created_at DESC LIMIT 5;
```

List API: `GET /api/v1/workspaces/{workspace_id}/repositories/{repository_id}/pull-requests`

---

## Indexing (R3)

Requires `VOYAGE_API_KEY` (Voyage API — default `REVY_EMBEDDING_BACKEND=voyage`), `GITHUB_APP_ID`, private key, and worker on `indexing` queue. Local/HF embedding track: `architecture.md` §11.3.1 (`REVY_HF_CACHE_PATH` when implemented).

1. `POST …/pull-requests/{pr_id}/revisions/{revision_id}/index` (workspace admin)
2. Poll `GET …/revisions/{revision_id}/index-job` until `status=completed`
3. List chunks: `GET …/revisions/{revision_id}/chunks`
4. Semantic search: `POST …/revisions/{revision_id}/chunks/search` with `{"query":"…","top_k":10}`

Verify:

```sql
SELECT status, chunk_count FROM github_index_jobs ORDER BY created_at DESC LIMIT 3;
SELECT file_path, chunk_index FROM github_code_chunks ORDER BY created_at DESC LIMIT 10;
```

**Related:** [DEV_BOOTSTRAP.md](../starter-pack/DEV_BOOTSTRAP.md), [REVIEW_PIPELINE_R2_EXECUTION.md](./waves/REVIEW_PIPELINE_R2_EXECUTION.md), [REVIEW_PIPELINE_R3_EXECUTION.md](./waves/REVIEW_PIPELINE_R3_EXECUTION.md)
