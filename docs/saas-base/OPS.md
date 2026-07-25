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

## Staging sign-off

Human checklist: [STAGING_VERIFICATION.md](./STAGING_VERIFICATION.md) — run before production SaaS base sign-off.

---

## Fast-start clone

Strip list for new products: [FAST_START_STRIP_LIST.md](./FAST_START_STRIP_LIST.md).
