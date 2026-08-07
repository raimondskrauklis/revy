# GitHub webhook — local development (R0)

How to receive GitHub App webhooks against a local Revy API. Production uses the same path with HTTPS.

**Endpoint:** `POST /api/v1/webhooks/github`  
**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`

**Production / staging droplet:** no smee.io — webhook URL is `https://<api-host>/api/v1/webhooks/github`. Full setup (App ID vs installation ID, PEM permissions, install-before-register, verify script): [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md).

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

Requires `VOYAGE_API_KEY` (`REVY_EMBEDDING_MODEL=voyage-code-3`, `REVY_EMBEDDING_DIMENSIONS=1024`), `GITHUB_APP_ID`, private key, and worker on `indexing` queue. If worker logs `401` on `POST …/access_tokens` while webhooks succeed, see [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) § App JWT and § Troubleshooting (not a PEM rotation / client-secret issue by default). Local/HF embedding track: `architecture.md` §11.3.1 (`REVY_HF_CACHE_PATH` when implemented).

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

---

## Review run (R4)

Requires `MOONSHOT_API_KEY` (`REVY_LLM_PROVIDER=moonshot`), completed R3 index (`VOYAGE_API_KEY`), GitHub App API, and worker on `review` queue.

1. Complete indexing for the revision (R3)
2. `POST …/pull-requests/{pr_id}/revisions/{revision_id}/review` with optional `{"profile":"standard|deep|critical"}` (workspace admin)
3. Poll `GET …/revisions/{revision_id}/review-run` until `status=completed`
4. List findings: `GET …/revisions/{revision_id}/findings`

Verify:

```sql
SELECT status, profile, provider FROM github_review_runs ORDER BY created_at DESC LIMIT 3;
SELECT severity, category, title FROM github_findings ORDER BY created_at DESC LIMIT 10;
```

---

---

## Reconcile + judge (R5)

Runs automatically after R4 review completes; requires worker on `reconciliation` and `judge` queues. Optional `ANTHROPIC_API_KEY` for judge (`REVY_ANTHROPIC_MODEL=claude-sonnet-5`; reconcile still completes without it).

1. After review `status=completed`, reconcile worker fingerprints findings into groups
2. List reconciled set: `GET …/pull-requests/{pr_id}/findings/reconciled` (cursor)
3. Judge runs for high-severity / security findings per R5-Q3 (max 10/run)

Verify:

```sql
SELECT state, fingerprint, severity FROM github_finding_groups ORDER BY updated_at DESC LIMIT 10;
SELECT outcome FROM github_finding_judge_outcomes ORDER BY created_at DESC LIMIT 5;
```

Group states: `active` · `superseded` · `resolved` — see [findings § domain states](./REVIEW_PIPELINE_FINDINGS.md#domain-states-enums).

---

## GitHub publish (R6)

Requires completed R4 review + R5 reconcile, GitHub App **Checks** + **Pull requests** write, worker on `github_publish` queue, `REVY_BOT_LOGIN` set.

1. Publish runs automatically after reconcile; admin retry: `POST …/revisions/{revision_id}/publish`
2. Poll `GET …/revisions/{revision_id}/publish-job` until `status=completed`
3. On GitHub: check run `revy/review` + PR summary comment; inline comments for `error`/`critical` with line anchors

Verify:

```sql
SELECT status, head_sha, github_check_run_id, github_comment_id FROM github_publish_jobs ORDER BY created_at DESC LIMIT 3;
```

Re-run publish on same `head_sha` updates the existing check run and comment in place.

Check `conclusion`: `failure` if any active `error`/`critical`; `success` if none; `neutral` if only `warning`/`info`.

---

## Reviewer UI (R7)

Requires R4+ API reachable from frontend; merge badge uses latest publish job + R6-Q2 logic.

1. Open `/reviewer` (nav appears when reviewer API probe succeeds)
2. Browse repositories → pull requests → findings for a revision
3. Confirm merge readiness badge matches check conclusion

Verify: browser EN+LV strings; `npm run build` passes with `features/reviewer/` routes registered.

---

## Automation (R8)

Requires migration `0017`, worker queues unchanged from R4–R6, GitHub App **Issue comments** subscribed.

### Autostart

On `pull_request` `opened` or `synchronize` (only when a **new revision** row is created), Revy enqueues index → review → reconcile → publish when `workspaces.review_autostart_enabled` is `true` (default).

Toggle: workspace admin PATCH `/api/v1/workspaces/{workspace_id}` with `review_autostart_enabled`, or Settings → Workspace in the app.

### `@revy review`

On `issue_comment` `created` with body matching `@revy review` on an **open** PR (not draft), Revy runs the full pipeline for the PR `head_sha` revision regardless of autostart toggle.

- Ignores comments from `REVY_BOT_LOGIN`
- Admin `POST …/index` sets `trigger_source=manual` and does **not** chain to review

Verify:

1. Open PR → autostart chain (check index/review/publish jobs + GitHub check)
2. Comment `@revy review` on same PR → pipeline re-runs
3. Disable autostart → new push does not autostart; `@revy review` still works
4. Manual index API does not auto-review

```sql
SELECT trigger_source, status FROM github_index_jobs ORDER BY created_at DESC LIMIT 5;
SELECT review_autostart_enabled FROM workspaces LIMIT 5;
```
