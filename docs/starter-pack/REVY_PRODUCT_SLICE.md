# docs/starter-pack/REVY_PRODUCT_SLICE.md

# Revy product slice — `github_installation` vertical (P4)

Repo-safe spec distilled from `internal-docs/product/revy/docs/` (TENANCY.md, PLATFORM_CONTEXT.md, architecture.md) and deploy supplement `implementation.revy.md`. **Redacted** — no secrets, no full review pipeline.

---

## Goal

Ship the first Revy domain entity on starter-pack rails: **workspace-scoped GitHub App installations** with cursor list + dev manual register. Webhooks, mirrors, reviews, and embeddings are **out of scope** for this slice.

---

## Entities

### `github_installation` (table: `github_installations`)

| Column | Type | Notes |
|--------|------|--------|
| `id` | UUID v7 | PK |
| `workspace_id` | UUID | FK → `workspaces.id`, NOT NULL |
| `github_installation_id` | BIGINT | GitHub installation ID, **globally unique** |
| `account_login` | TEXT | GitHub org/user login |
| `account_type` | TEXT | `organization` \| `user` |
| `account_id` | BIGINT | GitHub account ID |
| `status` | TEXT | `active` \| `suspended` \| `removed` |
| `permissions_snapshot` | JSONB | Optional permissions map from GitHub |
| `created_at` / `updated_at` | TIMESTAMPTZ | `TimestampedModel` |

**Tenancy:** one installation belongs to exactly one workspace; a workspace may have multiple installations.

**Later (not P4):** `repository` → `pull_request` → `review_revision` / `findings` hang off installation.

---

## API endpoints

Base: `/api/v1/workspaces/{workspace_id}/installations`

| Method | Path | Permission | Body / response |
|--------|------|------------|-----------------|
| `GET` | `/` | Workspace member (`items:view` or any active membership) | Cursor list of installations |
| `POST` | `/` | Workspace `admin` (`admin:users`) | Manual dev register until webhook phase |

### `POST` create (dev register)

```json
{
  "github_installation_id": 12345678,
  "account_login": "acme-corp",
  "account_type": "organization",
  "account_id": 987654,
  "permissions_snapshot": { "contents": "read" }
}
```

### List item shape

```json
{
  "id": "uuid",
  "workspace_id": "uuid",
  "github_installation_id": 12345678,
  "account_login": "acme-corp",
  "account_type": "organization",
  "account_id": 987654,
  "status": "active",
  "permissions_snapshot": {},
  "created_at": "2026-07-24T00:00:00Z",
  "updated_at": "2026-07-24T00:00:00Z"
}
```

**Guards:** `require_same_workspace`, `get_current_user`, idempotency on `POST` (P3 pattern).

---

## Permissions

| Action | Workspace role |
|--------|----------------|
| List installations | `admin`, `operator`, `viewer` (via `items:view`) |
| Register installation (dev) | `admin` only (`admin:users`) |

Platform `super_admin` bypasses workspace checks per starter-pack RBAC.

---

## Celery queues

Revy worker queue map (from `implementation.revy.md` §3). **P4 wires routes; task modules may remain stubs.**

| Queue | Work |
|-------|------|
| `github_events` | Webhook ingestion, HMAC verify |
| `repo_sync` | Mirror fetch, branch updates |
| `indexing` | Chunking, embeddings, symbol index |
| `review` | LLM review stages |
| `reconciliation` | Finding fingerprint reconcile |
| `judge` | Escalation / disagreement |
| `github_publish` | Check runs, review comments |
| `maintenance` | Outbox poll, worktree cleanup |

**v1 deploy:** single `revy-worker` consuming  
`-Q github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance`.

```python
celery_app.conf.task_routes = {
    "app.workers.github_tasks.*": {"queue": "github_events"},
    "app.workers.repo_tasks.*": {"queue": "repo_sync"},
    "app.workers.index_tasks.*": {"queue": "indexing"},
    "app.workers.review_tasks.*": {"queue": "review"},
    "app.workers.reconcile_tasks.*": {"queue": "reconciliation"},
    "app.workers.judge_tasks.*": {"queue": "judge"},
    "app.workers.publish_tasks.*": {"queue": "github_publish"},
    "app.workers.maintenance_tasks.*": {"queue": "maintenance"},
}
```

---

## Exclusions (P4)

- GitHub webhook endpoint and HMAC verification
- `repository`, `pull_request`, review/findings tables
- pgvector index jobs, LLM providers runtime
- Production GitHub App registration automation
- Items demo removal (keep `0002_p1_items` as pattern reference)
- `.cursorrules`, CI workflow, root README → **P5 deferred**

---

## Frontend (P4.4)

- Route: `/installations` under authenticated shell
- List + empty state + dev register form
- i18n: `installations_*` keys in EN/LV bundles
