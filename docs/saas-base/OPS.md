# SaaS base — operations index

Short pointers for running the W0–W8 platform on staging/production. Full deploy: `internal-docs/starter-pack/deploy/docs/implementation.md`.

---

## Migrations

```bash
cd backend && pipenv run alembic upgrade head
```

Required through **`0009_impersonation_sessions`** for SaaS base W6–W7.

---

## Celery worker

Export jobs (W6) and maintenance tasks use the **`maintenance`** queue:

```bash
cd backend
pipenv run celery -A app.workers.celery_app worker -Q maintenance,default --loglevel=info
```

| Env var | Purpose | Default (dev) |
|---------|---------|---------------|
| `EXPORT_STORAGE_PATH` | ZIP output directory | `/tmp/revy/exports` |
| `EXPORT_TTL_DAYS` | Days until export artifact eligible for cleanup | `7` |

Production example: `deploy/env-examples/backend.env.production.example`.

---

## Bootstrap super_admin

One-time per environment — see [DEV_BOOTSTRAP.md](../starter-pack/DEV_BOOTSTRAP.md) §5 and `internal-docs/starter-pack/docs/backend/BOOTSTRAP_SUPER_ADMIN.md`.

1. Set `BOOTSTRAP_SUPER_ADMIN_EMAIL` in backend env.
2. `pipenv run python -m scripts.seed_bootstrap_super_admin`
3. Remove env var after first successful login; register same email in Keycloak.

---

## Stripe webhooks

Setup: [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md).

| Endpoint | `POST /api/v1/webhooks/stripe` |
|----------|-------------------------------|
| Auth | Stripe signature (`STRIPE_WEBHOOK_SECRET`) |
| Orphan subscription events | Log + **200** (no retry storm) |
| Checkout missing workspace | **500** (Stripe retries) |

---

## AWS Bedrock (optional judge / reviewer)

Model policy M1 — use when operators prefer IAM over `ANTHROPIC_API_KEY`.

| Env | Purpose |
|-----|---------|
| `AWS_REGION` | Bedrock runtime region (e.g. `eu-central-1`) |
| `REVY_JUDGE_PROVIDER=bedrock` | Route R5 judge to Bedrock |
| `REVY_BEDROCK_JUDGE_MODEL_ID` | Bedrock model ID (e.g. `anthropic.claude-sonnet-4-20250514-v1:0`) |
| `REVY_REVIEWER_PROVIDER=bedrock` | Optional — route R4 reviewer to Bedrock |
| `REVY_BEDROCK_REVIEWER_MODEL_ID` | Single model ID for all reviewer profiles |
| `REVY_BEDROCK_INFERENCE_PROFILE_ARN` | Optional — documented; v1 uses `modelId` when unset |

Grant the API/worker IAM role `bedrock:InvokeModel` on the chosen model(s). After a judge run, verify `judge_provider` / `judge_model_id` on `github_finding_judge_outcomes`.

### Workspace model policy (M2)

Per-workspace overrides live in `workspace_model_policies`. Platform env remains the fallback when no row exists for a role.

| API | Purpose |
|-----|---------|
| `GET /api/v1/workspaces/{id}/model-policy` | Current overrides + `review_autostart_enabled` |
| `PATCH /api/v1/workspaces/{id}/model-policy` | Set/clear per-role model (`null` = platform default) |
| `GET /api/v1/workspaces/{id}/model-catalog` | Dropdown options filtered by platform-enabled providers |

Admins configure via `/settings/review` (M3). Run migration `0023_workspace_model_policies` before deploy.

---

## Staging sign-off

Human checklist: [STAGING_VERIFICATION.md](./STAGING_VERIFICATION.md) — run before production SaaS base sign-off.

---

## Fast-start clone

Strip list for new products: [FAST_START_STRIP_LIST.md](./FAST_START_STRIP_LIST.md).
