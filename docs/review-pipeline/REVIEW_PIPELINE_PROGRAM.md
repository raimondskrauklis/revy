# Review pipeline — program guide

How to continue Revy **after SaaS base W0–W8** without forking. **No execution steps** — see per-phase execution files under [waves/](./waves/). **Recovery:** [REVIEW_PIPELINE_RECOVERY_CHECKLIST.md](./REVIEW_PIPELINE_RECOVERY_CHECKLIST.md).

---

## 1. Why not fork?

| Approach | Use when | Revy |
|----------|----------|------|
| **Same repo + feature branches** | One product team, shared CI/deploy | **Yes** — default |
| **Git tag on `main`** | Immutable “base shipped” snapshot | **`saas-base-v1`** on merge PR #7 |
| **GitHub fork** | Contributing upstream to someone else's project | **No** |
| **Second repo / template** | Publishing a generic B2B starter for *other* products | Optional later — see [FAST_START_STRIP_LIST.md](../saas-base/FAST_START_STRIP_LIST.md) |

Revy **is** the product. The SaaS shell (`docs/saas-base/`) and scaffold (`docs/starter-pack/`) are rails; code review is the domain slice built **additively** on top.

---

## 2. Baseline tag

```bash
# Already applied on main merge (PR #7):
git fetch origin
git checkout main
git pull
git show saas-base-v1   # annotated tag → dacfc5b
```

| Tag | Points to | Meaning |
|-----|-----------|---------|
| `saas-base-v1` | `dacfc5b` | SaaS base W0–W8 complete; P4 installations slice |
| `saas-base-v1.1` | `48c361e` | Alembic AUTOCOMMIT fix; review pipeline findings + R0 execution |
| `review-r0-v1` | `754c88c` | GitHub webhook ingestion (`POST /api/v1/webhooks/github`), delivery dedupe, `github_events` worker |
| `review-r1-v1` | `dddfde0` | Repository metadata sync (`github_repositories`), `repo_sync` worker, list/sync API |
| `review-r2-v1` | `09317b2` | PR ingestion (`github_pull_requests`), revisions, `pull_request` webhooks |
| `review-r3-v1` | `a299d14` | PR revision indexing (`github_index_jobs`, `github_code_chunks`), Voyage embeddings, `indexing` queue |

Future product milestones: `review-r4-v1`, `v0.2.0`, etc. Pushing a tag whose commit **includes** `.github/workflows/release-tag.yml` triggers an automatic GitHub Release. Tags on older commits (e.g. `saas-base-v1`) may need a one-time `gh release create` or **Actions → Release tag → Run workflow** with the tag name.

---

## 3. Branching workflow

```text
main  ──●──●──●──●──  deployable; SaaS base + product
           \
            └── feat/review-r0-webhooks  → PR → merge
```

| Rule | Detail |
|------|--------|
| **Base branch** | `main` only for merges |
| **Feature branches** | `feat/review-<phase>-<topic>`, `fix/review-…`, `chore/…` |
| **PRs** | Required; optional Greptile + CI (`deploy.yml`) while building; patterns → [product patterns](./REVIEW_PIPELINE_PRODUCT_PATTERNS.md) |
| **SaaS base changes** | Bugfixes only unless new cross-cutting requirement; prefer small PRs |
| **Planning docs** | `docs/review-pipeline/` — findings before execution LOOP |

**Do not** long-lived `develop` unless team grows; `main` stays shippable.

---

## 4. What exists today (post–SaaS base)

### Shipped (P4 + SaaS)

| Layer | Path / surface |
|-------|----------------|
| **Installations ORM** | `backend/app/models/github_installation.py` |
| **Installations API** | `GET/POST /api/v1/workspaces/{id}/installations` |
| **Plan gate** | `require_plan_feature` on create installation |
| **Installations UI** | `frontend/src/features/installations/` |
| **Celery routes** | `backend/app/workers/celery_app.py` — `github_events`, `repo_sync`, `indexing`, … |
| **Postgres** | `vector` extension in deploy SQL (indexing later) |

### Shipped (R0)

| Layer | Path / surface |
|-------|----------------|
| **GitHub webhook** | `POST /api/v1/webhooks/github` — HMAC verify, delivery dedupe |
| **Webhook deliveries** | `github_webhook_deliveries` table; migration `0010` |
| **GitHub worker** | `backend/app/workers/github_tasks.py` — `installation`, `installation_repositories`, `push` |

### Shipped (R1)

| Layer | Path / surface |
|-------|----------------|
| **Repositories ORM** | `github_repositories` table; migration `0011` |
| **Webhook apply** | `installation_repositories` → upsert/remove repo rows |
| **Repo sync worker** | `backend/app/workers/repo_tasks.py` — GitHub API full reconcile |
| **Repositories API** | `GET/POST …/installations/{id}/repositories`, `sync-repositories` |

### Shipped (R2)

| Layer | Path / surface |
|-------|----------------|
| **PR ORM** | `github_pull_requests`, `github_pull_request_revisions`, `github_pull_request_reviews`; migration `0012` |
| **Webhook apply** | `pull_request`, `pull_request_review` → PR rows + revisions + review activity |
| **PR list API** | `GET …/repositories/{repo_id}/pull-requests` |

### Shipped (R3)

| Layer | Path / surface |
|-------|----------------|
| **Index ORM** | `github_index_jobs`, `github_code_chunks` (vector 512); migration `0013` |
| **Archive + chunking** | `integrations/github_archive.py`, `services/code_chunking.py` |
| **Embeddings** | `integrations/voyage_embeddings.py` — Voyage API (`voyage-3-lite` v1); parallel local track documented (`architecture.md` §11.3.1) |
| **Index worker** | `backend/app/workers/index_tasks.py` — `indexing` queue |
| **Index API** | `POST …/revisions/{id}/index`, `GET …/index-job`, chunk list + semantic search |

### Not shipped (R4–R7)

| Gap | Notes |
|-----|--------|
| Review/findings tables | R4+ |
| Worker modules | `review_tasks`, … |
| LLM provider runtime | Config + Celery `review` queue |
| GitHub publish | Checks, review comments — `github_publish` queue |
| Reviewer UI | `frontend/src/features/reviewer/` (placeholder / absent) |

---

## 5. Phased roadmap (R0–R7)

Order follows [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) § Celery queues and `internal-docs/product/revy/docs/architecture.md`. Refine in **findings** before execution.

| Phase | Goal | Key deliverables |
|-------|------|------------------|
| **R0** | Webhook ingestion | GitHub App webhook route; HMAC verify; raw event store or idempotent enqueue → `github_events` |
| **R1** | Repo sync | Installation-linked repos; `repo_sync` tasks; mirror metadata |
| **R2** | PR ingestion | `pull_request` entity; opened/synchronize/closed events; revision tracking |
| **R3** | Indexing | Chunking, embeddings, pgvector; `indexing` queue |
| **R4** | Review run | LLM pipeline stages; `review` queue; workspace/installation tenancy |
| **R5** | Reconcile + judge | Finding fingerprints; `reconciliation`, `judge` queues |
| **R6** | GitHub publish | Check runs, PR review comments; `github_publish` queue |
| **R7** | Product UI | Findings list/detail; PR/review status in app; dashboard widgets |

**v1 worker deploy** (from product slice): single worker consuming  
`-Q github_events,repo_sync,indexing,review,reconciliation,judge,github_publish,maintenance`.

---

## 6. Code layout (target)

Additive under existing structure — no SaaS shell rewrites.

```text
backend/app/
  api/v1/webhooks/github.py          # R0
  models/github_repository.py        # R1
  models/github_pull_request.py      # R2
  models/github_review_run.py        # R4
  models/github_finding.py           # R4
  services/github_webhooks.py        # R0
  services/github_review.py          # R4
  workers/github_tasks.py            # R0
  workers/repo_tasks.py              # R1
  workers/index_tasks.py             # R3
  workers/review_tasks.py            # R4
  ...

frontend/src/features/
  installations/                     # exists
  reviewer/                          # R7
```

Register routes in `api/v1/__init__.py`; nav via extension registry or dedicated `/reviews` route (decide in R7 findings).

---

## 7. Environment & deploy (preview)

New secrets (document in R0 findings + `backend/.env.example`):

| Variable | Phase |
|----------|-------|
| `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY_PATH`, `GITHUB_WEBHOOK_SECRET` | R0–R1 |
| `MOONSHOT_API_KEY`, `REVY_LLM_PROVIDER`, Kimi model tier env | R4 (primary) |
| `ANTHROPIC_API_KEY` | R5 (judge / cross-family) |
| `VOYAGE_API_KEY` | R3 |
| Webhook public URL | R0 — same pattern as [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md) |

Worker droplet must consume Revy queues (see `implementation.revy.md`). Export/maintenance queue unchanged from SaaS W6.

---

## 8. Planning workflow (agents)

Same discipline as [docs/saas-base](../saas-base/README.md):

1. **`create-findings`** → [REVIEW_PIPELINE_FINDINGS.md](./REVIEW_PIPELINE_FINDINGS.md) (baseline-first; includes GitHub App ops pointers)
2. **`create-general-plan`** → per-phase `REVIEW_PIPELINE_R*_GENERAL_PLAN.md` (index: [REVIEW_PIPELINE_GENERAL_PLAN.md](./REVIEW_PIPELINE_GENERAL_PLAN.md))
3. **`create-execution-plan`** → `waves/REVIEW_PIPELINE_R*_EXECUTION.md` only
4. **Manual peer-review** — human invokes a **separate agent** with `architecture-peer-review` / `execution-peer-review` on the prepared files (skills in `.cursor/skills/`). The implementing agent does not mark this done.
5. **`phase-execution`** from execution file; branch `feat/review-r*-…`

**GitHub App runbooks:** [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md), [GITHUB_APP_TARGET_CONFIG.md](../utils/GITHUB_APP_TARGET_CONFIG.md).

Skills in `.cursor/skills/` named for `docs/starter-pack/` apply by analogy — point agents at `docs/review-pipeline/` paths.

---

## 9. Relationship to SaaS base

| SaaS base | Review pipeline |
|-----------|-----------------|
| Settings, billing, admin, impersonation | Unchanged unless R* needs a hook (e.g. plan gate on review volume) |
| `installations` UI + API | **Input** to R0 (link webhooks to installation rows) |
| Audit (`record_audit`) | Use for review lifecycle events |
| `STAGING_VERIFICATION.md` | Extend with review e2e when R6+ ships |

SaaS base program is **complete** — see [docs/saas-base/README.md](../saas-base/README.md). Do not reopen W waves except bugfixes.

---

## 10. References

| Path | Role |
|------|------|
| [REVY_PRODUCT_SLICE.md](../starter-pack/REVY_PRODUCT_SLICE.md) | P4 committed spec |
| [docs/saas-base/README.md](../saas-base/README.md) | SaaS base index |
| [AGENTS.md](../../AGENTS.md) | Agent entry |
| `internal-docs/product/revy/docs/architecture.md` | Full pipeline design |
| `internal-docs/product/revy/deploy/docs/implementation.revy.md` | Worker + deploy |
