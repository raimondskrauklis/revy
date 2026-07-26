# docs/review-pipeline/waves/REVIEW_PIPELINE_R0_EXECUTION.md

# R0 — GitHub webhook ingestion (execution)

Phase **R0** of [REVIEW_PIPELINE_GENERAL_PLAN.md](../REVIEW_PIPELINE_GENERAL_PLAN.md). Baseline: [REVIEW_PIPELINE_FINDINGS.md](../REVIEW_PIPELINE_FINDINGS.md). **Depends on** P4 installations + SaaS base. **R0 only.**

**Goal:** Signed GitHub App webhooks → idempotent delivery store → Celery `github_events` queue.

**Authority:** `internal-docs/product/revy/docs/WEBHOOKS.md`, [REVY_PRODUCT_SLICE.md](../../starter-pack/REVY_PRODUCT_SLICE.md), `backend/app/api/v1/webhooks/stripe.py` (pattern).

## Decisions locked for R0

- **Path:** `POST /api/v1/webhooks/github` — no JWT; HMAC `X-Hub-Signature-256`.
- **Raw body:** `await request.body()` before JSON parse.
- **Dedupe:** `github_webhook_deliveries` table keyed by `X-GitHub-Delivery` UUID; duplicate → **200** without re-enqueue.
- **Events v1:** `installation`, `installation_repositories`, `push` — map to installation row updates or enqueue sync stub.
- **Unknown installation:** log warning + **200** (no retry storm).
- **Celery:** `app.workers.github_tasks.process_github_event` on `github_events` queue.
- **Config:** reuse `settings.github_webhook_secret`; disabled when secret empty → `503` or skip route mount (match Stripe `billing_disabled` pattern).
- EN+LV not required for R0 (no user-facing UI); ops logs English.

## Out of scope for R0

- Repository / PR tables (R1/R2)
- GitHub OAuth install flow
- nginx IP allowlist
- Production worker queue change in deploy.yml (document only; optional subphase)
- `heavy_job` cleanup (optional tiny fix if touched)

---

## R0.1 — Delivery dedupe migration + settings

**What:** Hand-written migration `github_webhook_deliveries` (`delivery_id` PK, `event_type`, `installation_id` nullable, `received_at`). Ensure `GITHUB_WEBHOOK_SECRET` documented in `.env.example` + deploy example.

**Files:** `backend/alembic/versions/…_github_webhook_deliveries.py`, `backend/app/models/github_webhook_delivery.py`, `backend/app/core/config.py` (if needed), env examples

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_webhook_config.py -q` — green (new).

---

## R0.2 — Signature verification service

**What:** `integrations/github_webhook.py` — `verify_github_signature(payload, signature, secret)` per `WEBHOOKS.md`. Unit tests with known vector.

**Files:** `backend/app/integrations/github_webhook.py`, `backend/tests/unit/test_github_webhook_verify.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_webhook_verify.py -q` — green.

---

## R0.3 — Webhook route + idempotent handler

**What:** `api/v1/webhooks/github.py` — thin handler: read body, verify signature, `try_record_delivery`, dispatch by `X-GitHub-Event`, commit, **200**. Mount on `webhooks` router without auth dependency.

**Files:** `backend/app/api/v1/webhooks/github.py`, `backend/app/services/github_webhooks.py`, `backend/app/api/v1/webhooks/__init__.py`, `backend/tests/unit/test_github_webhook.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_webhook.py -q` — green.

---

## R0.4 — Celery `github_tasks` + installation handlers

**What:** `workers/github_tasks.py` — `process_github_event(delivery_id)` loads payload, updates `github_installations.status` on `installation` action, logs `push` / `installation_repositories` (enqueue stub for R1). Register import in `celery_app.py`.

**Files:** `backend/app/workers/github_tasks.py`, `backend/app/services/github_installations.py` (status update helper), `backend/tests/unit/test_github_tasks.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_github_tasks.py tests/unit/test_github_webhook.py -q` — green.

---

## R0.5 — Ops docs + local dev

**What:** `docs/review-pipeline/GITHUB_WEBHOOK_DEV.md` — smee.io / `gh webhook forward`, secret alignment, sample `installation` payload. Cross-link `DEV_BOOTSTRAP.md` § migrations (AUTOCOMMIT note).

**Files:** `docs/review-pipeline/GITHUB_WEBHOOK_DEV.md`, `docs/starter-pack/DEV_BOOTSTRAP.md` (migration verify step)

**Deliverable:** `test -f docs/review-pipeline/GITHUB_WEBHOOK_DEV.md`.

**Human gate:** one successful local or staging delivery logged **200**.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_webhook_config.py \
  tests/unit/test_github_webhook_verify.py \
  tests/unit/test_github_webhook.py \
  tests/unit/test_github_tasks.py \
  -q
```

**Deploy:** `alembic upgrade head`; set `GITHUB_WEBHOOK_SECRET`; GitHub App webhook URL → `https://<host>/api/v1/webhooks/github`.

**Next:** [REVIEW_PIPELINE_R1_EXECUTION.md](./REVIEW_PIPELINE_R1_EXECUTION.md) (create when planning R1).
