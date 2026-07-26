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

4. Trigger an event from GitHub (e.g. reinstall app) and confirm API logs **200**.

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

**Related:** [DEV_BOOTSTRAP.md](../starter-pack/DEV_BOOTSTRAP.md), [REVIEW_PIPELINE_R0_EXECUTION.md](./waves/REVIEW_PIPELINE_R0_EXECUTION.md)
