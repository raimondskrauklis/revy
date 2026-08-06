# GitHub App setup (Revy)

How to create and configure a **GitHub App** for Revy — webhooks (R0), repository metadata sync (R1), and workspace installations (P4).

**Verified against:** [GitHub Apps docs](https://docs.github.com/en/apps/creating-github-apps), Revy R0/R1 (`docs/review-pipeline/`), `backend/app/integrations/github_api.py` (App JWT `iat`/`exp`), `backend/app/core/config.py`.

**Related:** `backend/.env.example`, `deploy/env-examples/backend.env.production.example`, [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md) (form copy-paste), [GITHUB_APP_TARGET_CONFIG.md](./GITHUB_APP_TARGET_CONFIG.md) (full R0–R7 target values), [REVIEW_PIPELINE_FINDINGS.md](../review-pipeline/REVIEW_PIPELINE_FINDINGS.md), [GITHUB_WEBHOOK_DEV.md](../review-pipeline/GITHUB_WEBHOOK_DEV.md) (local forwarding), [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md), [OPS.md](../saas-base/OPS.md).

> **Registering once for the full product?** Use [GITHUB_APP_TARGET_CONFIG.md](./GITHUB_APP_TARGET_CONFIG.md) instead of the minimal tables below.

---

## What Revy uses the GitHub App for

```text
GitHub
  → POST /api/v1/webhooks/github  (HMAC X-Hub-Signature-256)
  → idempotent store (github_webhook_deliveries)
  → Celery github_events queue
  → update github_installations / github_repositories

Revy API (optional, when GITHUB_APP_ID + private key set)
  → GitHub App JWT
  → installation access token
  → list installation repositories (full sync)
```

| Capability | Env required | Webhook events (`X-GitHub-Event`) |
|------------|--------------|-------------------------------------|
| Webhook ingestion | `GITHUB_WEBHOOK_SECRET` | Any signed delivery |
| Installation status updates | webhook secret + row in `github_installations` | `installation` (automatic) |
| Repository metadata | webhook secret + registered installation | `installation_repositories` (automatic) |
| Push logging (stub) | webhook secret + **Push** subscribed | `push` |
| Full repository sync API | `GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY_PATH` | — (API, not webhook) |

OAuth “Install Revy” button in the product UI is **not shipped yet** — installations are linked via the **manual register** form (`/installations`) until a later phase.

---

## App ID vs installation ID (do not mix)

GitHub assigns **two different numbers**. Using the wrong one in `.env` or the Revy register form is a common setup mistake.

| ID | What it is | Where to find it | Used in |
|----|------------|------------------|---------|
| **App ID** | The GitHub App itself (one per app) | App settings → **About** → **App ID** (`https://github.com/settings/apps/<slug>`) | `GITHUB_APP_ID` in backend `.env` |
| **Installation ID** | One install of that app on a user/org | After **Install App** → URL `https://github.com/settings/installations/<id>` | Revy **Register installation** form only |

```text
Create app → App ID → .env (GITHUB_APP_ID)
Install app on GitHub account/org → Installation ID → Revy UI register form
```

**Order matters:** complete **Install App** on GitHub **before** registering in Revy. Registering an ID from the app settings page (or before install) will not work.

`REVY_BOT_LOGIN` must match the app slug: `<app-slug>[bot]` (e.g. `revybot[bot]`).

**Verify on droplet** (uses real PEM + env; replace `INSTALLATION_ID`):

```bash
docker exec -i revy-api python <<'PY'
import asyncio, httpx
from app.core.config import settings
from app.integrations.github_api import create_app_jwt

INSTALLATION_ID = 0  # paste from github.com/settings/installations/<id>

async def main() -> None:
    print("GITHUB_APP_ID (env):", settings.github_app_id)
    jwt = create_app_jwt()
    h = {"Authorization": f"Bearer {jwt}", "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    async with httpx.AsyncClient(timeout=30.0) as c:
        app = await c.get("https://api.github.com/app", headers=h)
        print("GET /app:", app.status_code)
        if app.status_code == 200:
            data = app.json()
            print("app_id (GitHub):", data.get("id"), "slug:", data.get("slug"))
            print("env matches app:", str(settings.github_app_id) == str(data.get("id")))
        tok = await c.post(f"https://api.github.com/app/installations/{INSTALLATION_ID}/access_tokens", headers=h)
        print("token mint:", tok.status_code, "(expect 201)")

asyncio.run(main())
PY
```

Account ID for the register form: `gh api user --jq .id` (personal) or org API for organizations.

---

## Prerequisites (Revy side)

1. **Migrations** through `0011_github_repositories` (includes `0010_github_webhook_deliveries`):

   ```bash
   cd backend
   pipenv run alembic upgrade head
   pipenv run alembic current
   ```

2. **API** running and reachable at a public HTTPS URL (staging/production) or tunneled locally (see [GITHUB_WEBHOOK_DEV.md](../review-pipeline/GITHUB_WEBHOOK_DEV.md)).

3. **Celery worker** consuming `github_events` (and `repo_sync` for full sync):

   ```bash
   cd backend
   pipenv run celery -A app.workers.celery_app worker \
     -Q github_events,repo_sync,default --loglevel=info
   ```

---

## Step 1 — Create the GitHub App

1. Open **GitHub** → **Settings** → **Developer settings** → **GitHub Apps** → **New GitHub App**.

   Direct link: https://github.com/settings/apps/new

2. Fill in the form — field-by-field:

### General

| Field | Value | Notes |
|-------|-------|-------|
| **GitHub App name** | `revy` / `revy-staging` / `revy-dev` | Globally unique; use env suffix |
| **Description** | Copy from [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md) | Shown to users during install |
| **Homepage URL** | `https://revy.createit.digital` (prod) or `http://localhost:5173` (dev) | Same as `APP_PUBLIC_URL` — SPA, not API |

### Identifying and authorizing users

| Field | Value | Notes |
|-------|-------|-------|
| **Callback URL** | Leave empty, or homepage URL | **Ignored** until Revy uses GitHub user OAuth. Not Keycloak `/auth/callback`. |
| **Expire user authorization tokens** | ✓ **Checked** | GitHub default; safe to leave on. Ignored until user-token flow ships. |
| **Request user authorization (OAuth) during installation** | ☐ **Unchecked** | Revy uses **installation** tokens + manual register today — not per-user OAuth at install |
| **Enable Device Flow** | ☐ **Unchecked** | For CLI/headless user auth only — not used by Revy |

### Webhook

| Field | Value | Notes |
|-------|-------|-------|
| **Active** | ✓ **Checked** | Required for R0+ |
| **Webhook URL** | `https://<api-host>/api/v1/webhooks/github` | API host, not SPA — e.g. `https://revy.createit.digital/api/v1/webhooks/github` if API is on same domain |
| **Webhook secret** | Generate (see below) | **You choose** the value — not provided by GitHub |

Generate secret:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

- Paste into GitHub → **Webhook secret**
- Paste into `GITHUB_WEBHOOK_SECRET` in backend env

For local dev, `local-webhook-secret` is fine if your forwarder uses the same value.

### Permissions

Expand **Repository permissions** first — event checkboxes below only appear for permissions you grant.

| Section | Setting |
|---------|---------|
| **Repository permissions → Metadata** | **Read** |
| **Repository permissions → Contents** | **Read** |
| **Repository permissions** (everything else) | **No access** |
| **Organization permissions** | **No access** (all collapsed defaults) |
| **Account permissions** | **No access** (all collapsed defaults) |

### Subscribe to events

GitHub shows only **optional** events here. Events tied to permissions you granted appear after you set **Metadata** and **Contents** (e.g. **Push**).

**Automatic (not in this list — do not look for checkboxes):**

| `X-GitHub-Event` header | GitHub docs | Revy handler |
|-------------------------|-------------|--------------|
| `installation` | All Apps receive by default | Updates `github_installations.status` |
| `installation_repositories` | All Apps receive by default | Upserts `github_repositories` |

Do **not** confuse **Installation target** (in the form) with **Installation** (automatic). Revy does not use `installation_target`.

**Check in the form (shipped R0 + R1):**

| Form label | `X-GitHub-Event` | Enable | Revy handler |
|------------|------------------|--------|--------------|
| **Push** | `push` | ✓ | Logged stub today |

**Leave unchecked** (visible after Contents: Read, not used by Revy today):

| Form label | `X-GitHub-Event` |
|------------|------------------|
| Installation target | `installation_target` |
| Meta | `meta` |
| Security advisory | `security_advisory` |
| Create | `create` |
| Delete | `delete` |
| Fork | `fork` |
| Public | `public` |
| Release | `release` |
| Repository | `repository` |
| Repository dispatch | `repository_dispatch` |
| Star | `star` |
| Watch | `watch` |
| Label | `label` |
| Commit comment | `commit_comment` |
| Gollum | `gollum` |
| Workflow dispatch | `workflow_dispatch` |
| Workflow job | `workflow_job` |
| Workflow run | `workflow_run` |

**Future (R2+)** — enable when permission is added:

| Form label | `X-GitHub-Event` | Requires permission |
|------------|------------------|---------------------|
| **Pull request** | `pull_request` | **Pull requests: Read** (R2) |

Source: [GitHub webhook events](https://docs.github.com/en/webhooks/webhook-events-and-payloads); Revy `SUPPORTED_EVENTS` in `backend/app/services/github_webhooks.py`.

### Where can this GitHub App be installed?

| Environment | Choice |
|-------------|--------|
| Personal dev | **Only on this account** |
| Staging / production | **Any account** (orgs install from GitHub) |

### Post-install (optional, not used yet)

| Field | Value |
|-------|-------|
| **Setup URL** | Leave empty | Post-install redirect for setup wizards — OAuth install UI not shipped |
| **Redirect on update** | Leave unchecked | Only relevant with Setup URL |

3. Click **Create GitHub App**.

**Copy-paste description text:** [GITHUB_APP_DESCRIPTION.md](./GITHUB_APP_DESCRIPTION.md)

---

## Step 1b — After creation (same settings page)

| Section | Action |
|---------|--------|
| **About → App ID** | Copy → `GITHUB_APP_ID` |
| **About → Client ID** | Note for future OAuth install — not used by backend today |
| **Private keys** | **Generate** → save `.pem` → `GITHUB_APP_PRIVATE_KEY_PATH` |
| **Client secrets** | **Not used by Revy backend** — OAuth user/install flow only; generating one does not fix API 401s |
| **Install App** (sidebar) | Install on org/account → get installation ID for Revy register form |

---

## Step 2 — Generate a private key

1. On the app’s settings page → **Private keys** → **Generate a private key**.
2. GitHub downloads a `.pem` file **once** — store it securely; it cannot be re-downloaded.

| Environment | Path |
|-------------|------|
| **Local** | Outside the repo, e.g. `~/.config/revy/github-app.pem` |
| **Droplet** | `/mnt/revy_volume/secrets/github-app.pem` (block volume; see PEM permissions below) |

Set `GITHUB_APP_PRIVATE_KEY_PATH` to that **in-container** absolute path (same as host path when mounted by `deploy.yml`). **Never** commit the key or put it in `.env` as inline text.

### Droplet volume permissions (Docker)

`revy-api` and `revy-worker` run as **`appuser`** (uid **1000** in `backend/Dockerfile`). Data dirs and PEM owned `deploy:deploy` cause `PermissionError` inside the container.

`deploy` has **no passwordless sudo** — CI fixes ownership via a root `alpine` container (see `deploy.yml`). Re-run manually after adding PEM or if dirs were created outside deploy:

```bash
docker run --rm --user root \
  -v /mnt/revy_volume/data:/data \
  -v /mnt/revy_volume/secrets:/secrets \
  alpine:3.20 \
  sh -ec '
    for d in repos worktrees exports hf-cache; do
      mkdir -p "/data/$d"
      chown -R 1000:1000 "/data/$d"
      chmod -R 2770 "/data/$d"
    done
    if [ -f /secrets/github-app.pem ]; then
      chown 1000:1000 /secrets/github-app.pem
      chmod 640 /secrets/github-app.pem
    fi
  '

docker restart revy-api revy-worker
```

---

## Step 3 — Copy App ID

On the same GitHub App page, under **About**:

- **App ID** → `GITHUB_APP_ID` (numeric string, e.g. `123456`)

Optional: note **Client ID** — not used by Revy backend today (OAuth install deferred).

---

## Step 4 — Environment variables

### Local (`backend/.env`)

```env
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=/Users/you/.config/revy/github-app.pem
GITHUB_WEBHOOK_SECRET=local-webhook-secret
REVY_BOT_LOGIN=revy[bot]
```

### Droplet (`/mnt/revy_volume/backend/.env`)

See `deploy/env-examples/backend.env.production.example`:

```env
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=/mnt/revy_volume/secrets/github-app.pem
GITHUB_WEBHOOK_SECRET=<same-as-github-app-webhook-secret>
REVY_BOT_LOGIN=revy[bot]
```

| Variable | Required for | Purpose |
|----------|--------------|---------|
| `GITHUB_WEBHOOK_SECRET` | Webhooks | HMAC verify on `POST /api/v1/webhooks/github`; empty → `503 github_webhooks_disabled` |
| `GITHUB_APP_ID` | Full repo sync API | GitHub App JWT `iss` claim |
| `GITHUB_APP_PRIVATE_KEY_PATH` | Full repo sync API | PEM file for JWT signing |
| `REVY_BOT_LOGIN` | Display / future publish | Bot login label (default `revy[bot]`) |

`GITHUB_APP_ID` + key are **optional** for webhooks-only operation. Without them, `POST …/sync-repositories` returns `503 github_api_disabled`.

Restart API and Celery after changing env.

---

## Step 5 — Install the app on GitHub

1. GitHub App settings → **Install App** (left sidebar).
2. Choose target **organization** or **personal account**.
3. Select repositories (all or selected).
4. Confirm install.

### Find installation metadata for Revy

After install, open the installation in GitHub. The URL contains the numeric **installation ID**:

```text
https://github.com/settings/installations/<INSTALLATION_ID>
```

You also need:

- **Account login** — org or user slug (e.g. `acme-corp`)
- **Account ID** — numeric GitHub account id (org/user settings or API)
- **Account type** — `organization` or `user`

---

## Step 6 — Register installation in Revy

**Prerequisite:** Step 5 (**Install App** on GitHub) completed — use the installation ID from `https://github.com/settings/installations/<id>`, not the App ID from **About**.

Until OAuth install ships, link the GitHub installation to a **workspace** manually:

1. Log in to Revy as a workspace **admin** on a **pro** workspace (`installations.create` plan gate).
2. Open **Installations** (`/installations`) or **Settings → Integrations**.
3. Submit the **Register installation** form:

   | Field | Source |
   |-------|--------|
   | Installation ID | `https://github.com/settings/installations/<INSTALLATION_ID>` |
   | Account login | Org/user slug (e.g. `raimondskrauklis`) |
   | Account ID | `gh api user --jq .id` (personal) or org numeric id |
   | Account type | `organization` or `user` |

API equivalent: `POST /api/v1/workspaces/{workspace_id}/installations` (workspace admin).

**Security (interim):** the form does not call GitHub to prove ownership — it only stores the mapping. Real auth is webhook HMAC + app PEM for API. OAuth install from Revy (future) will replace manual register. One `github_installation_id` can link to only one workspace (`ConflictError` otherwise).

Webhook `installation` events only update rows that **already exist** in `github_installations`. Unregistered installation IDs are logged and acknowledged with **200** (no retry storm).

---

## Step 7 — Verify webhooks

### Production / staging

1. GitHub App → **Advanced** → **Recent deliveries** (or installation → webhook deliveries).
2. Trigger an event (e.g. reinstall app, add a repo).
3. Expect **200** from `https://<api-host>/api/v1/webhooks/github`.

### Database check

```sql
SELECT delivery_id, event_type, installation_id
FROM github_webhook_deliveries
ORDER BY received_at DESC
LIMIT 5;
```

### Full repository sync (optional)

When `GITHUB_APP_ID` and private key are set:

```http
POST /api/v1/workspaces/{workspace_id}/installations/{installation_id}/sync-repositories
```

Workspace admin + idempotency header. Worker must consume `repo_sync`.

List repos:

```http
GET /api/v1/workspaces/{workspace_id}/installations/{installation_id}/repositories
```

---

## Local development

Public HTTPS is required for GitHub → your machine. Use a forwarder:

| Tool | Doc |
|------|-----|
| smee.io | [GITHUB_WEBHOOK_DEV.md](../review-pipeline/GITHUB_WEBHOOK_DEV.md) § Option A |
| `gh webhook forward` | Same doc § Option B |

Set GitHub App webhook URL to the smee channel (or forward target). Keep `GITHUB_WEBHOOK_SECRET` aligned on both sides.

---

## Deploy checklist

1. `alembic upgrade head` on target database (through `0011`).
2. Place `github-app.pem` at `/mnt/revy_volume/secrets/github-app.pem`; run the **Droplet volume permissions** docker one-liner above → `GITHUB_APP_PRIVATE_KEY_PATH`
3. Set `GITHUB_APP_ID` (**App ID**, not installation ID), `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_WEBHOOK_SECRET`, `REVY_BOT_LOGIN` in `/mnt/revy_volume/backend/.env`.
4. **Install App** on GitHub for each target account/org; note each **installation ID**.
5. GitHub App webhook URL → `https://<api-host>/api/v1/webhooks/github`.
6. Webhook secret matches `GITHUB_WEBHOOK_SECRET`.
7. Celery worker: `-Q github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,…` (see `.github/workflows/deploy.yml`).
8. Register each **installation ID** per workspace in Revy UI (pro plan).
9. Run **Verify on droplet** script (`token mint: 201`).
10. Confirm **Recent deliveries** show 200; open a test PR for autostart / `@revy review`.

---

## API surface (reference)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `POST` | `/api/v1/webhooks/github` | HMAC (`X-Hub-Signature-256`) | Webhook handler |
| `GET` | `/api/v1/workspaces/{id}/installations` | JWT | List installations |
| `POST` | `/api/v1/workspaces/{id}/installations` | JWT (admin) | Manual register |
| `GET` | `/api/v1/workspaces/{id}/installations/{id}/repositories` | JWT | List mirrored repos |
| `POST` | `/api/v1/workspaces/{id}/installations/{id}/sync-repositories` | JWT (admin) | Full sync via GitHub API |

---

## App JWT (GitHub API auth)

Revy authenticates as the GitHub App with a short-lived **JWT** (`create_app_jwt()` in `backend/app/integrations/github_api.py`), then exchanges it for an **installation access token** per API call. Installation tokens are **not cached** — there is nothing to refresh in `.env`.

| Claim | Revy value | GitHub rule |
|-------|------------|-------------|
| `iat` | `now - 60` | Up to 60s in the past (clock drift) |
| `exp` | `iat + 600` | At most **600 seconds after `iat`** (10-minute max JWT lifetime) |
| `iss` | `GITHUB_APP_ID` | App ID from **About** (not installation URL id; not Client ID unless you standardize on that) |

**Do not** set `exp = now + 600` while `iat = now - 60` — that is an 11-minute window and GitHub returns `401` with `'Expiration time' claim ('exp') is too far in the future` on `GET /app` and `POST …/access_tokens`.

**Client secrets** (GitHub App settings) are for OAuth only — Revy does not read them for indexing, sync, checks, or publish.

---

## Installation access tokens (GitHub rollout)

GitHub is rolling out a new **stateless** installation token format (`ghs_…`, ~520 chars, JWT-shaped). Classic tokens were short opaque strings.

**Revy:** tokens are minted per request in `backend/app/integrations/github_api.py`, passed to httpx as `Bearer` strings, and **not stored** in the database. No length or format assumptions — **no change required** for this rollout.

**Optional staging check:** add `X-GitHub-Stateless-S2S-Token: enabled` on `POST /app/installations/{id}/access_tokens` and run repo sync / indexing once. Header is temporary for validation — see [GitHub changelog](https://github.blog/changelog/2026-05-15-github-app-installation-tokens-per-request-override-header/).

If you later **cache** installation tokens, store as `TEXT` (≥520 chars) and treat as opaque strings.

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `503 github_webhooks_disabled` | Empty or missing `GITHUB_WEBHOOK_SECRET` |
| `422` invalid signature | Secret mismatch between GitHub App and backend env |
| Webhook `200` but installation unchanged | Installation not registered in Revy (`github_installations` row missing) |
| Webhooks OK, indexing/checks `401` on `access_tokens` | App JWT rejected — see rows below (webhooks do not use App JWT) |
| `503 github_api_disabled` | Missing `GITHUB_APP_ID` or `GITHUB_APP_PRIVATE_KEY_PATH` |
| `PermissionError` on PEM in container | PEM mode `600` owned by `deploy` — fix permissions (see **Droplet PEM permissions**) |
| `GET /app` 401 — `exp` too far in the future | JWT lifetime > 600s from `iat` — upgrade Revy past PR #82 or patch `create_app_jwt()` (`exp = iat + 600`) |
| `GET /app` 401 — JWT could not be decoded | Wrong `GITHUB_APP_ID` (often installation ID in `.env`), PEM mismatch, or clock skew |
| `token mint` 401 (other message) | Same as `GET /app` 401 — fix App JWT first |
| `token mint` 404 | Installation id wrong for this app, or app not installed on that account |
| `plan_upgrade_required` on register | Workspace `plan` not `pro` — Stripe checkout or ops `UPDATE workspaces SET plan='pro'` |
| Repos not listed | App not installed, wrong installation ID in Revy, or no `installation_repositories` webhook — run **Sync repositories** |
| Task not running | Celery worker not consuming `github_events` / `repo_sync` / `indexing` |
| `docker exec … python <<'PY'` prints nothing | Missing `-i` on `docker exec` — use `docker exec -i revy-worker python <<'PY'` |
| Webhook 404 | Wrong path — must be `/api/v1/webhooks/github` (nginx must route `/api/v1`) |

Check nginx routes public API at `https://<host>/api/v1` (`deploy/nginx/revy.createit.digital.conf`).

---

## Future phases (not required today)

| Phase | Permission | Subscribe to events (form label) | `X-GitHub-Event` |
|-------|------------|----------------------------------|------------------|
| **R2** | **Pull requests: Read** | **Pull request** ✓ | `pull_request` |
| **R6** | **Contents: Write**, **Pull requests: Write**, **Checks: Write** | (same + check run events if needed) | `check_run`, etc. |
| **OAuth install UI** | — | Callback URL + **Request user authorization during installation** ✓ | — |

### Contents Write — inline thread resolve (required for publish)

GraphQL `resolveReviewThread` (used when findings are addressed) is gated on **Contents: Read and write**, not Pull requests write alone. Greptile/Bugbot-class bots have this permission.

**If `resolve_mutation_failed` appears in publish manifest:**

1. GitHub → **Settings → Developer settings → GitHub Apps** → your Revy app (`revy-staging` / `revy`).
2. **Repository permissions → Contents** → **Read and write** → **Save changes**.
3. **Install App** (sidebar) → **Configure** on the installation → **Review requested permissions** → accept.
4. Re-trigger publish (push to PR or wait for next Revy run).

Verify: publish `summary_json.thread_resolve_skipped.resolve_mutation_failed` → `0`; GitHub PR **Files changed** threads collapse on fix pushes.

Authority: [REVY_REVIEW_DOGFOOD_RR_V4_FINDINGS.md](../review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_RR_V4_FINDINGS.md).

Track program status: [docs/review-pipeline/README.md](../review-pipeline/README.md).
